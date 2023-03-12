# encoding: utf-8
# vim: set ts=2 sw=2 et:
require "lru_redux"
require "resolv"
require "logstash/filters/dns/resolv_patch"

java_import 'java.net.IDN'

def register(params)
  @nameserver = params['nameserver']
  @timeout = params.fetch('timeout', 0.5)
  @max_retries = params.fetch('max_retries', 2)
  @hit_cache_size = params.fetch('hit_cache_size', 0)
  @hit_cache_ttl = params.fetch('hit_cache_ttl', 60)
  @failed_cache_size = params.fetch('failed_cache_size', 0)
  @failed_cache_ttl = params.fetch('failed_cache_ttl', 5)
  @hostsfile = params['hostsfile']

  if @nameserver.nil? && @hostsfile.nil?
    @resolv = Resolv.new(default_resolvers)
  else
    @resolv = Resolv.new(build_resolvers)
  end

  if @hit_cache_size > 0
    @hit_cache = LruRedux::TTL::ThreadSafeCache.new(@hit_cache_size, @hit_cache_ttl)
  end

  if @failed_cache_size > 0
    @failed_cache = LruRedux::TTL::ThreadSafeCache.new(@failed_cache_size, @failed_cache_ttl)
  end

  @ip_validator = Resolv::AddressRegex
  @ecs = ['[client]', '[destination]', '[host]', '[observer]', '[server]', '[source]']
end

def filter(event)
  (event.get('[Sensor]') || []).each_with_index do |entry, index|
    enrich_dns(event, entry, '[Sensor]['+index.to_s+']')
  end

  entry = event.get('[Analyzer]')
  unless entry.nil?
    enrich_dns(event, entry, '[Analyzer]')
  end

  (event.get('[Source]') || []).each_with_index do |entry, index|
    enrich_dns(event, entry, '[Source]['+index.to_s+']')
  end

  (event.get('[Target]') || []).each_with_index do |entry, index|
    enrich_dns(event, entry, '[Target]['+index.to_s+']')
  end

  # For events whose "RawLog" attachment is assuredly defined,
  # try to enrich the hostname/IP address of various ECS classes.
  if event.get('[@metadata][kafka][key]') != 'IDMEFv2'
    @ecs.each do |cls|
      ip = event.get("[Attachment][RawLog][Content]#{cls}[ip]")
      if ip.kind_of?(Array)
        # Convert to a set then back to an array
        case (ip|[]).length
        when 0
          ip = nil
        when 1
          ip = ip[0]
        else
          next
        end
      end
      hostname = event.get("[Attachment][RawLog][Content]#{cls}[hostname]")

      if hostname.nil? and !ip.nil?
        logger.debug("DNS: Attempting IP address to hostname resolution for '#{ip}'")
        reverse(event, ip, "[Attachment][RawLog][Content]#{cls}[hostname]")
      elsif ip.nil? and !hostname.nil?
        logger.debug("DNS: Attempting hostname to IP address resolution for '#{hostname}'")
        resolve(event, hostname, "[Attachment][RawLog][Content]#{cls}[ip]")
      end
    end
  end

  return [event]
end

def enrich_dns(event, entry, field)
  ip = entry['IP']
  hostname = entry['Hostname']

  if ip and !hostname
    logger.debug("DNS: Attempting IP address to hostname resolution for '#{ip}'")
    reverse(event, ip, field + '[Hostname]')
  elsif hostname and !ip
    logger.debug("DNS: Attempting hostname to IP address resolution for '#{hostname}'")
    resolve(event, hostname, field + '[IP]')
  end
end

def default_resolvers
  [::Resolv::Hosts.new, default_dns_resolver]
end

def default_dns_resolver
  dns_resolver(nil)
end

def dns_resolver(args=nil)
  dns_resolver = ::Resolv::DNS.new(args)
  dns_resolver.timeouts = @timeout
  dns_resolver
end

def build_resolvers
  build_user_host_resolvers.concat([::Resolv::Hosts.new]).concat(build_user_dns_resolver)
end

def build_user_host_resolvers
  return [] if @hostsfile.nil? || @hostsfile.empty?
  @hostsfile.map{|fn| ::Resolv::Hosts.new(fn)}
end

def build_user_dns_resolver
  return [] if @nameserver.nil? || @nameserver.empty?
  [dns_resolver(normalised_nameserver)]
end

def normalised_nameserver
  nameserver_hash = @nameserver.kind_of?(Hash) ? @nameserver.dup : { 'address' => @nameserver }

  nameserver = nameserver_hash.delete('address') || fail(LogStash::ConfigurationError, "DNS Enrichment: `nameserver` hash must include `address` (got `#{@nameserver}`)")
  nameserver = Array(nameserver).map(&:to_s)
  nameserver.empty? && fail(LogStash::ConfigurationError, "DNS Enrichment: `nameserver` addresses, when specified, cannot be empty (got `#{@nameserver}`)")

  search     = nameserver_hash.delete('search') || []
  search     = Array(search).map(&:to_s)
  search.size > 6 && fail(LogStash::ConfigurationError, "DNS Enrichment: A maximum of 6 `search` domains are accepted (got `#{@nameserver}`)")

  ndots      = nameserver_hash.delete('ndots') || 1
  ndots      = Integer(ndots)
  ndots <= 0 && fail(LogStash::ConfigurationError, "DNS Enrichment: `ndots` must be positive (got `#{@nameserver}`)")

  fail(LogStash::ConfigurationError, "Unknown `nameserver` argument(s): #{nameserver_hash}") unless nameserver_hash.empty?

  {
    :nameserver => nameserver,
    :search     => search,
    :ndots      => ndots
  }
end

def resolve(event, raw, field)
  begin
    return if @failed_cache && @failed_cache[raw] # recently failed resolv, skip
    if @hit_cache
      address = @hit_cache[raw]
      if address.nil?
        if address = retriable_getaddress(raw)
          @hit_cache[raw] = address
        end
      end
    else
      address = retriable_getaddress(raw)
    end
    if address.nil?
      @failed_cache[raw] = true if @failed_cache
      logger.debug("DNS: couldn't resolve the hostname.",
                    :field => field, :value => raw)
      return
    end
  rescue Resolv::ResolvTimeout
    @failed_cache[raw] = true if @failed_cache
    logger.warn("DNS: timeout on resolving the hostname.",
                  :field => field, :value => raw)
    return
  rescue SocketError => e
    logger.error("DNS: Encountered SocketError.",
                  :field => field, :value => raw, :message => e.message)
    return
  rescue Java::JavaLang::IllegalArgumentException => e
    logger.error("DNS: Unable to parse address.",
                  :field => field, :value => raw, :message => e.message)
    return
  rescue => e
    logger.error("DNS: Unexpected Error.",
                  :field => field, :value => raw, :message => e.message)
    return
  end

  unless address.nil?
    logger.debug("DNS: Resolved #{raw.inspect} to #{address.inspect}")
    event.set(field, address)
  end
end

def reverse(event, raw, field)
  if ! @ip_validator.match(raw)
    logger.debug("DNS: not an address",
                  :field => field, :value => event.get(field))
    return
  end

  begin
    return if @failed_cache && @failed_cache.key?(raw) # recently failed resolv, skip
    if @hit_cache
      hostname = @hit_cache[raw]
      if hostname.nil?
        if hostname = retriable_getname(raw)
          @hit_cache[raw] = hostname
        end
      end
    else
      hostname = retriable_getname(raw)
    end
    if hostname.nil?
      @failed_cache[raw] = true if @failed_cache
      logger.debug("DNS: couldn't resolve the address.",
                    :field => field, :value => raw)
      return
    end
  rescue Resolv::ResolvTimeout
    @failed_cache[raw] = true if @failed_cache
    logger.warn("DNS: timeout on resolving address.",
                  :field => field, :value => raw)
    return
  rescue SocketError => e
    logger.error("DNS: Encountered SocketError.",
                  :field => field, :value => raw, :message => e.message)
    return
  rescue Java::JavaLang::IllegalArgumentException => e
    logger.error("DNS: Unable to parse address.",
                  :field => field, :value => raw, :message => e.message)
    return
  rescue => e
    logger.error("DNS: Unexpected Error.",
                  :field => field, :value => raw, :message => e.message)
    return
  end

  unless hostname.nil?
    logger.debug("DNS: Resolved #{raw.inspect} to #{hostname.inspect}")
    event.set(field, hostname)
  end
end

def retriable_request(&block)
  tries = 0
  begin
    block.call
  rescue Resolv::ResolvTimeout,  SocketError
    if tries < @max_retries
      tries = tries + 1
      retry
    else
      raise
    end
  end
end

def retriable_getname(address)
  retriable_request do
    getname(address)
  end
end

def retriable_getaddress(name)
  retriable_request do
    getaddress(name)
  end
end

def getname(address)
  name = resolv_getname_or_nil(@resolv, address)
  name && name.force_encoding(Encoding::UTF_8)
  name && IDN.toUnicode(name)
end

def getaddress(name)
  idn = IDN.toASCII(name)
  address = resolv_getaddress_or_nil(@resolv, idn)
  address && address.force_encoding(Encoding::UTF_8)
end

def resolv_getname_or_nil(resolver, address)
  # `Resolv#each_name` yields to the provided block zero or more times;
  # to prevent it from yielding multiple times when more than one match
  # is found, we return directly in the block.
  # See also `Resolv#getname`
  resolver.each_name(address) do |name|
    return name
  end

  # If no match was found, we return nil.
  return nil
end

def resolv_getaddress_or_nil(resolver, name)
  # `Resolv#each_address` yields to the provided block zero or more times;
  # to prevent it from yielding multiple times when more than one match
  # is found, we return directly in the block.
  # See also `Resolv#getaddress`
  resolver.each_address(name) do |address|
    return address
  end

  # If no match was found, we return nil.
  return nil
end
