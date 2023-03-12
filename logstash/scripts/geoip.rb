# encoding: utf-8
# vim: set ts=2 sw=2 et:
require "lru_redux"
require 'maxmind/geoip2'

java_import 'java.util.concurrent.locks.ReentrantReadWriteLock'

def register(params)
  @parameters = params
  if params['cache_size'] > 0
    @cache = LruRedux::TTL::ThreadSafeCache.new(params['cache_size'], params['cache_ttl'])
    @function = method(:memoize)
  else
    @function = method(:get_record)
  end
  rw_lock = java.util.concurrent.locks.ReentrantReadWriteLock.new
  @write_lock = rw_lock.writeLock
  @read_lock = rw_lock.readLock
  @reader = nil
  @unlocode = {}
  load_databases
  @location_attr = 'Location'
  @geoloc_attr   = 'GeoLocation'
  @unloc_attr    = 'UnLocation'
  @ecs = ['[client]', '[destination]', '[host]', '[observer]', '[server]', '[source]']
end

def load_databases
  lock_for_write do
    begin
      unless @reader.nil?
        @reader.close
      end

      @reader = MaxMind::GeoIP2::Reader.new(database: @parameters['geoip_database'], locales: ['en'], mode: MaxMind::DB::MODE_MEMORY)
    rescue StandardError => e
      logger.warn("Could not load GeoIP database from #{@parameters['geoip_database'].to_s}: #{e.class.to_s}: #{e.message}")
      @reader = nil
    end

    begin
      file = File.open @parameters['unlocode_database']
      begin
        @unlocode = JSON.load file
        # Basic checks to detect corruption.
        unless @unlocode.kind_of?(Hash) and @unlocode['data'].kind_of?(Array) and @unlocode['locations'].kind_of?(Hash)
          raise "Database corruption detected"
        end
      ensure
        file.close
      end
    rescue StandardError => e
      logger.warn("Could not load UN/LOCODE database from #{@parameters['unlocode_database'].to_s}: #{e.class.to_s}: #{e.message}")
      @unlocode = {}
    end

    @next_refresh = Time.now() + @parameters['refresh_interval']
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

def get_record(ip)
  begin
    lock_for_read do
      if @reader.nil?
        return nil
      end
      logger.debug("Performing GeoIP enrichment for #{ip}")
      record = @reader.city(ip)

      # "XY" is the UN Locode for international waters and so on.
      country_code = record.country&.iso_code || "XZ"
      country_name = record.country&.name
      subdiv_code  = record.most_specific_subdivision&.iso_code || ""
      subdiv_name  = record.most_specific_subdivision&.name
      city         = record.city&.name
      postcode     = record.postal&.code

      # GeoLocation
      res = {
        'lat' => record.location&.latitude,
        'lon' => record.location&.longitude,
      }

      # Location
      unless country_name.nil?
        location = ["Country: #{country_name}"]
        unless subdiv_name.nil?
          location.push("Subdivision: #{subdiv_name}")
        end
        unless city.nil?
          location.push("City: #{city}")
        end
        unless postcode.nil?
          location.push("Postal code: #{postcode}")
        end
        res['location'] = location.join(', ')
      end

      # UN Location code (UN/LOCODE)
      unless city.nil? or @unlocode.empty?
        locid = @unlocode['locations'].fetch(country_code, {}).fetch(subdiv_code, {})[city]
        city_code = locid.nil? ? '???' : @unlocode['data'].fetch(locid, {}).fetch('location', '???')
        res['unlocode'] = "#{country_code} #{city_code.to_s}"
      end

      return res
    end
  rescue MaxMind::GeoIP2::AddressNotFoundError => e
    logger.debug("No GeoIP record for #{ip}")
  rescue StandardError => e
    logger.warn("Error while performing enrichment for '#{ip}': #{e.class.to_s}: #{e.message}")
  end
  return nil
end

def memoize(ip)
  @cache.getset(ip) { get_record(ip) }
end

def enrich_geoip(entry, ip, loc_attr, geoloc_attr, unloc_attr, geopoint)
  if ip.nil? or entry.nil?
    return false
  end

  if ip.kind_of?(Array)
    ip = ip[0]
  end

  do_loc    = !loc_attr.nil? && !entry.key?(loc_attr)
  do_geoloc = !geoloc_attr.nil? && !entry.key?(geoloc_attr)
  do_unloc  = !unloc_attr.nil? && !entry.key?(unloc_attr)

  unless do_loc or do_geoloc or do_unloc
    return false
  end

  record = nil
  lock_for_read do
    record = @function.(ip)
  end

  if record.nil?
    return false
  end
  changed = false

  if do_loc and record.key?('location')
    entry[loc_attr] = record['location']
    changed = true
  end

  if do_geoloc and !record['lat'].nil? and !record['lon'].nil?
    if geopoint
      entry[geoloc_attr] = {"lat": record['lat'], "lon": record['lon']}
    else
      entry[geoloc_attr] = "#{record['lat'].to_s}, #{record['lon'].to_s}"
    end
    changed = true
  end

  if do_unloc and record.key?('unlocode')
    entry[unloc_attr] = record['unlocode']
    changed = true
  end

  return changed
end

def filter(event)
  if needs_refresh?
    load_databases
  end

  (event.get('[Sensor]') || []).each_with_index do |entry, index|
    if enrich_geoip(entry, entry['IP'], @location_attr, nil, @unloc_attr, false)
      event.set("[Sensor][#{index.to_s}]", entry)
    end
  end

  entry = event.get('[Analyzer]')
  unless entry.nil?
    if enrich_geoip(entry, entry['IP'], @location_attr, @geoloc_attr, @unloc_attr, false)
      event.set("[Analyzer]", entry)
    end
  end

  (event.get('[Source]') || []).each_with_index do |entry, index|
    if enrich_geoip(entry, entry['IP'], @location_attr, @geoloc_attr, @unloc_attr, false)
      event.set("[Source][#{index.to_s}]", entry)
    end
  end

  (event.get('[Target]') || []).each_with_index do |entry, index|
    if enrich_geoip(entry, entry['IP'], @location_attr, @geoloc_attr, @unloc_attr, false)
      event.set("[Target][#{index.to_s}]", entry)
    end
  end

  # For events whose "RawLog" attachment is assuredly defined,
  # try to enrich the location based on the geo-coordinates.
  if event.get('[@metadata][kafka][key]') != 'IDMEFv2'
    loc_attr = 'name'
    geoloc_attr = 'location'
    unloc_attr = 'UNlocation'

    @ecs.each do |cls|
      entry = event.get("[Attachment][RawLog][Content]#{cls}")
      if entry.nil?
        next
      end

      geo = entry.fetch('geo', {})
      if enrich_geoip(geo, entry['ip'], loc_attr, geoloc_attr, unloc_attr, true)
        event.set("[Attachment][RawLog][Content]#{cls}[geo]", geo)
      end
    end
  end

  return [event]
end
