# encoding: utf-8
# vim: set ts=2 sw=2 et:

def register(params)
  require 'yaml'

  @protocols = {}
  YAML.load_file(params['protocols']).each do |k, v|
    @protocols[k] = v
    @protocols[v.downcase] = v
  end

  @services = {}
  params.fetch('services', {}).each do |proto, path|
    services = {}
    YAML.load_file(path).each do |k, v|
      services[k] = v
      services[v.downcase] = v
    end
    @services[proto.downcase] = services
  end
end

def filter(event)
  ['Source', 'Target'].each do |cls|
    (event.get(cls) || []).each_with_index do |entry, index|
      protocols = []
      entry[1].fetch('Protocol', []).each do |proto|
        @protocols.fetch(proto.to_s.downcase, proto)
      end

      # @FIXME There is no way to know which protocol a port refers to
      ports = []
      entry[1].fetch('Port', []).each do |port|
        
      end
    end
  end

  # Quick reminder:
  # network.application: meaningful layer 7 protocol name (e.g. "aim")
  # network.protocol:    IANA-assigned layer 7 protocol name (e.g. "aol")
  # network.iana_number: layer 4 protocol number
  # network.transport:   layer 4 protocol name
  # network.type:        layer 3 protocol name
  l4_number = event.get('[Attachment][RawLog][Content][network][iana_number]')
  l4_name = event.get('[Attachment][RawLog][Content][network][transport]')
  if l4_name.nil? and not l4_number.nil?
    l4_name = @protocols[l4_number.to_s]
    unless l4_name.nil?
      l4_name.downcase!
      event.set('[Attachment][RawLog][Content][network][transport]', l4_name)
    end
  elsif l4_number.nil? and not l4_name.nil?
    l4_name.downcase!
    l4_number = @protocols[l4_name]
    unless l4_number.nil?
      l4_number = l4_number.to_i
      event.set('[Attachment][RawLog][Content][network][iana_number]', l4_number)
    end
  end

  l7_name = event.get('[Attachment][RawLog][Content][network][protocol]')
  services = @services[l4_name]
  if l7_name.nil? and services
    ssvc = services[event.get('[Attachment][RawLog][Content][source][port]').to_s]
    dsvc = services[event.get('[Attachment][RawLog][Content][destination][port]').to_s]

    # If only one of the source or destination uses a well-known port,
    # use the associated service as the IANA-assigned layer 7 protocol name.
    if ssvc.nil? and not dsvc.nil?
      l7_name = dsvc
    elsif dsvc.nil? and not ssvc.nil?
      l7_name = ssvc
    end
    event.set('[Attachment][RawLog][Content][network][protocol]', l7_name)
  end

  # Use the IANA-assigned name as the application name if that's all we've got.
  app = event.get('[Attachment][RawLog][Content][network][application]')
  if app.nil? and not l7_name.nil?
    event.set('[Attachment][RawLog][Content][network][application]', l7_name)
  end

  return [event]
end
