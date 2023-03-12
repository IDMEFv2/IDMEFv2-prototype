# encoding: utf-8
# vim: set ts=2 sw=2 et:
require 'ipaddr'
require 'json'
require "lru_redux"
require 'set'

java_import 'java.util.concurrent.locks.ReentrantReadWriteLock'

def register(params)
  @cti = {}
  @parameters = params
  if params['cache_size'] > 0
    @cache = LruRedux::TTL::ThreadSafeCache.new(params['cache_size'], params['cache_ttl'])
    @function = method(:memoize)
  else
    @function = method(:get_feeds)
  end
  rw_lock = java.util.concurrent.locks.ReentrantReadWriteLock.new
  @write_lock = rw_lock.writeLock
  @read_lock = rw_lock.readLock
  refresh

  # Map parameters to IDMEFv2 fields
  @checks = {
    'IP'     => 'IP',
    # 'Domain' => 'Hostname',
    'Email'  => 'Email',
    # 'URL'    => 'URL'
  }
end

def refresh
  lock_for_write do
    # Map parameters to their CTI type
    {
      'IP'        => 'ip',
      'Email'     => 'mail',
      # 'Domain'    => 'domain',
      # 'URL'       => 'url',
      # 'Hash'      => 'hash',
      # 'File'      => 'file',
    }.each do |k, type|
      load_file(k, type)
    end
    @next_refresh = Time.now + @parameters['refresh_interval']
  end
end

def load_file(key, type)
  @cti[key] = nil
  begin
    path = @parameters['databases'][key]
    if path.nil?
      logger.info("No CTI configured for '#{key}'")
      return
    end

    file = File.open path
    begin
      @cti[key] = JSON.load file
    ensure
      file.close
    end

    unless @cti[key].fetch("type", '') == type
      raise "Type mismatch (#{@cti[key].fetch("type", '')})"
    end

    logger.info("CTI for #{key} successfully loaded from: #{path}")
  rescue StandardError => e
    logger.warn("CTI for #{key} could not be loaded: #{e.class.to_s}: #{e.message}")
    @cti[key] = nil
  end
end

def lock_for_write
  @write_lock.lock
  begin
    yield
  ensure
    @write_lock.unlock
  end
end

def lock_for_read
  @read_lock.lock
  begin
    yield
  ensure
    @read_lock.unlock
  end
end

def needs_refresh?
  lock_for_read do
    return @next_refresh < Time.now
  end
end

def get_feeds(type, key, value)
  items = @cti[type].fetch("items", {})
  wilds = @cti[type].fetch("wildcards", {})
  ti = Set[]

  if type == 'IP'
    ip = IPAddr.new value
    # Canonicalization:
    # - IPv4-mapped IPv6 addresses are converted to IPv4 addresses
    # - The addresses are normalized and compressed
    value = ip.native.to_s

    # Try subnet matches first
    prefix = ip.ipv6? ? 128 : 32
    while prefix > 0
        wilds.fetch(ip.mask(prefix).to_s + '/' + prefix.to_s, {}).each_key do |feed|
        ti.add("#{key}:#{feed}")
      end
      prefix -= 1
    end
  end

  # Try exact macth
  items.fetch(value, {}).each_key do |feed|
    ti.add("#{key}:#{feed}")
  end

  logger.debug("Completed CTI lookup for #{type}: #{value}")
  ti
end

def memoize(type, key, value)
  @cache.getset([type, value]) { get_feeds(type, key, value) }
end

def filter(event)
  if needs_refresh?
    refresh
  end

  (event.get('[Source]') || []).each_with_index do |source, index|
    @checks.each do |type, key|
      logger.debug("Processing CTI for [Source][#{index.to_s}][#{key}]")

      if source.key?(key)
        ti = Set[]
        lock_for_read do
          if @cti[type].nil?
            next
          end
          ti = @function.(type, key, source[key])
        end

        unless ti.empty?
          ti.merge(source.fetch('TI', []))
          event.set("[Source][#{index.to_s}][TI]", ti.to_a)
        end
      end
    end
  end

  attach = event.get('[Attachment][CTI][Content]')
  unless attach.nil?
    @checks.each do |type, key|
      logger.debug("Processing CTI for [Attachment][CTI][Content][#{key}]")
      lock_for_read do
        if @cti[type].nil?
          next
        end
      end

      attach.fetch(key, {}).each do |value, old_ti|
        ti = Set[]
        lock_for_read do
          if @cti[type].nil?
            next
          end
          ti = @function.(type, key, value)
        end

        unless ti.empty?
          ti.merge(old_ti)
          event.set("[Attachment][CTI][Content][#{key}][#{value}]", ti.to_a)
        end
      end
    end
  end

  return [event]
end
