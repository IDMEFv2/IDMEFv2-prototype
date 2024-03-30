# encoding: utf-8
# vim: set ts=2 sw=2 et:

def register(params)
   patterns = {
     'EMAILLOCALPART' => '[a-zA-Z][a-zA-Z0-9_.+-=:]+',
     'HOSTNAME'       => '\b(?:[0-9A-Za-z][0-9A-Za-z-]{0,62})(?:\.(?:[0-9A-Za-z][0-9A-Za-z-]{0,62}))*(?:\.?|\b)',
     'IPV4'           => '(?<![0-9])(?:(?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5])[.](?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5])[.](?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5])[.](?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5]))(?![0-9])',
     'IPV6'           => '(?:(?:[0-9A-Fa-f]{1,4}:){7}(?:[0-9A-Fa-f]{1,4}|:))|(?:(?:[0-9A-Fa-f]{1,4}:){6}(?::[0-9A-Fa-f]{1,4}|(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(?:(?:[0-9A-Fa-f]{1,4}:){5}(?:(?:(?::[0-9A-Fa-f]{1,4}){1,2})|:(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(?:(?:[0-9A-Fa-f]{1,4}:){4}(?:(?:(?::[0-9A-Fa-f]{1,4}){1,3})|(?:(?::[0-9A-Fa-f]{1,4})?:(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(?:(?:[0-9A-Fa-f]{1,4}:){3}(?:(?:(?::[0-9A-Fa-f]{1,4}){1,4})|(?:(?::[0-9A-Fa-f]{1,4}){0,2}:(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(?:(?:[0-9A-Fa-f]{1,4}:){2}(?:(?:(?::[0-9A-Fa-f]{1,4}){1,5})|(?:(?::[0-9A-Fa-f]{1,4}){0,3}:(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(?:(?:[0-9A-Fa-f]{1,4}:){1}(?:(?:(?::[0-9A-Fa-f]{1,4}){1,6})|(?:(?::[0-9A-Fa-f]{1,4}){0,4}:(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(?::(?:(?:(?::[0-9A-Fa-f]{1,4}){1,7})|(?:(?::[0-9A-Fa-f]{1,4}){0,5}:(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))(?:%\w+)?',
     'POSINT'         => '\b(?:[1-9][0-9]*)\b',
     'USER'           => '[a-zA-Z0-9._-]+',
     'URIPROTO'       => '[A-Za-z](?:[A-Za-z0-9+\-.]+)+',
     'URIPATH'        => '(?:/[A-Za-z0-9$.+!*\'(){},~:;=@#%&_\-]*)+',
     'URIPARAM'       => '\?[A-Za-z0-9$.+!*\'|(){},~@#%&/=:;_?\-\[\]<>]*',
   }
   patterns['EMAILADDRESS'] = "#{patterns['EMAILLOCALPART']}@#{patterns['HOSTNAME']}"
   patterns['IP']           = "(?:#{patterns['IPV4']}|#{patterns['IPV6']})"
   patterns['IPORHOST']     = "(?:#{patterns['IP']}|#{patterns['HOSTNAME']})"
   patterns['URIHOST']      = "#{patterns['IPORHOST']}(?::#{patterns['POSINT']})?"
   patterns['URIPATHPARAM'] = "#{patterns['URIPATH']}(?:#{patterns['URIPARAM']})?"
   patterns['URI']          = "#{patterns['URIPROTO']}://(?:#{patterns['USER']}(?::[^@]*)?@)?(?:#{patterns['URIHOST']})?(?:#{patterns['URIPATHPARAM']})?"

   @re = {
     'IP'    => Regexp.new("(#{patterns['IP']})"),
     'Email' => Regexp.new("(#{patterns['EMAILADDRESS']})"),
     'URI'   => Regexp.new("(#{patterns['URI']})"),
   }
   @source = params['source']
end

def filter(event)
  msg = event.get(@source)
  if msg.nil?
    return []
  end

  extdata = {}
  ['IP', 'Email', 'URI'].each do |k|
    data = {}
    msg.scan(@re[k]).flatten.each do |m|
      data[m] = []
    end
    unless data.empty?
      extdata[k] = data
    end
  end

  unless extdata.empty?
    event.set('[Attachment][EXTDATA]', {
      'ContentType' => 'application/json',
      'Content'     => extdata
    })
  end

  return [event]
end
