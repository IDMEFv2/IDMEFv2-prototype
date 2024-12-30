# encoding: utf-8
# vim: set ts=2 sw=2 et:

require 'yaml'
require 'logstash/filters/translate'
require 'logstash/filters/mutate'

def register(params)
  @rulesets = {}
  Dir.glob(params['rules']) do |filename|
    YAML.load_stream(File.read(filename)) do |doc|
      name = doc['ruleset']['name']
      doc['ruleset'].fetch('rules', []).each do |rule|
        r = []
        rule.fetch('translate', []).each do |trans|
          d = {
            "field" => trans['source'],
            "destination" => trans['target'],
            "dictionary" => trans['dictionary']
          }
          if trans.key?('fallback')
            d['fallback'] = trans['fallback']
          end
          f = LogStash::Filters::Translate.new(d)
          f.register
          r.push(f)
        end
        f = LogStash::Filters::Mutate.new({
            "add_field" => rule['fields'],
            "add_tag" => ['alert']
        })
        f.register
        r.push(f)
        ruleid = Integer(rule['id']) rescue 0
        if ruleid == 0
          logger.error("IDMEFv2 matching plugin: Can't read configuration for rule ID #{rule['id']}")
        else
          @rulesets[ruleid] = r
        end
      end
    end
  end
end

def filter(event)
  ruleid = Integer(event.get('[Attachment][RawLog][Content][rule][id]')) rescue 0
  if ruleid == 0
    return [event]
  end
  @rulesets.fetch(ruleid, []).each do |filter|
    filter.filter(event)
  end
  return [event]
end
