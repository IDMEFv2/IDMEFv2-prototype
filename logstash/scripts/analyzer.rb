# encoding: utf-8
# vim: set ts=2 sw=2 et:
require 'logstash/version'

def register(params)
  # Use "ip" to retrieve the default source IP
  @me = {
    'Name'        => ENV['ANALYZER_NAME'],
    'Model'       => "Logstash #{LOGSTASH_CORE_VERSION}",
    'Location'    => ENV['ANALYZER_LOCATION'],
    'UnLocation'  => ENV['ANALYZER_UNLOCATION'],
    'GeoLocation' => ENV['ANALYZER_GEOLOCATION'],
    'IP'          => ENV['ANALYZER_IP'],
    'Hostname'    => ENV['ANALYZER_HOSTNAME'],
  }
  @me.compact!
end

def filter(event)
  if event.get('Analyzer').nil?
    event.set('Analyzer', @me)
  end
  return [event]
end
