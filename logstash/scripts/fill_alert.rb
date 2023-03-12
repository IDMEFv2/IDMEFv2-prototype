# encoding: utf-8
# vim: set ts=2 sw=2 et:

def fill(event, idmef_cls, ecs_cls)
  fields = {
    '[Hostname]'    => '%{[hostname]}',
    '[Location]'    => '%{[geo][name]}',
    '[IP]'          => '%{[ip]}',
    '[Port][0]'     => '%{[port]}',
    '[GeoLocation]' => '%{[geo][location][lat]}, %{[geo][location][lon]}',
  }

  fields.each do |idmef_attr, ecs_attr|
    begin
      unless event.get("#{idmef_cls}#{idmef_attr}")
        v = ecs_attr.gsub(/%{[^}]+}/) { |s|
          r = event.get("[Attachment][RawLog][Content][#{ecs_cls}]#{s[2..-2]}")
          if r.kind_of?(Array)
            r = r[0]
          end
          unless [String, TrueClass, FalseClass, Integer, Float].any? { |type| r.kind_of?(type) }
            raise "Not a scalar value"
          end
          r
        }

        event.set("#{idmef_cls}#{idmef_attr}", v)
      end
    rescue StandardError => e
      # The substitution failed, probably because the field did not exist
      # or did not contain a (list of) scalar(s).
    end
  end
end

def filter(event)
  unless event.get('[Attachment][RawLog][Content]')
    return [event]
  end

  src = event.get('[@metadata][IDMEFv2][source]')
  if src
    fill(event, '[Source][0]', src)
  end

  tgt = event.get('[@metadata][IDMEFv2][target]')
  if tgt
    fill(event, '[Target][0]', tgt)
  end

  return [event]
end
