# encoding: utf-8
# vim: set ts=2 sw=2 et:
require 'csv'
require "lru_redux"

java_import 'java.util.concurrent.locks.ReentrantReadWriteLock'

def register(params)
  @parameters = params
  if params['cache_size'] > 0
    @cache = LruRedux::TTL::ThreadSafeCache.new(params['cache_size'], params['cache_ttl'])
    @function = method(:memoize)
  else
    @function = method(:get_closest_location)
  end
  rw_lock = java.util.concurrent.locks.ReentrantReadWriteLock.new
  @write_lock = rw_lock.writeLock
  @read_lock = rw_lock.readLock
  @map = {}
  @ecs = ['[client]', '[destination]', '[host]', '[observer]', '[server]', '[source]']
  load_database
end

def load_database
  lock_for_write do
    @map.clear
    CSV.read(@parameters['database'], headers: true, encoding: 'UTF-8').each do |row|
      k = [deg2rad(row["lat"].to_f), deg2rad(row["lng"].to_f)]
      @map[k] = "#{row['city']}, #{row['admin_name']}, #{row['country']}"
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

def deg2rad(v)
  v * Math::PI / 180
end

def dist(lat1, lat2, lon1, lon2)
  # Spherical law of Cosines for Earth (approx. radius = 6371 Km)
  Math.acos( Math.sin(lat1)*Math.sin(lat2) + Math.cos(lat1)*Math.cos(lat2)*Math.cos(lon2-lon1) ) * 6371
end

def get_closest_location(geoloc)
  lat = deg2rad(geoloc[0].to_f)
  lon = deg2rad(geoloc[1].to_f)
  min_dist = nil
  min_data = nil
  @map.each do |k, v|
    # Pre-filter coordinates to 0.01 radian.
    if (k[0] - lat).abs < 0.01 and (k[1] - lon).abs < 0.01
      d = dist(k[0], lat, k[1], lon)
      # Keep only the closest match
      if min_dist.nil? or d < min_dist
        min_dist = d
        min_data = v
      end
    end
  end

  unless min_dist.nil? or min_dist > 10
    min_data
  end
end

def memoize(geoloc)
  @cache.getset(geoloc) { get_closest_location(geoloc) }
end

def enrich_geoloc(event, entry, field, geoloc_attr, loc_attr)
  geoloc = entry[geoloc_attr]

  # No geolocation data in the event or the associated location is already known.
  if geoloc.nil? or entry.key?(loc_attr)
    return
  end

  begin
    if geoloc.kind_of?(String)
      # "1.234, 5.678" => ["1.234", "5.678"]
      geoloc = geoloc.split(%r{,\s*})
      if geoloc.length < 2
        raise "Invalid string"
      end
    else
      # We suppose the geolocation data contains an ECS geo-point.
      geoloc = [geoloc['lat'], geoloc['lon']]
    end

    lock_for_read do
      location = @function.(geoloc)
      unless location.nil?
        event.set("#{field}[#{loc_attr}]", location)
      end
    end
  rescue StandardError => e
    logger.warn("Could not perform geolocation enrichment: #{e.class.to_s}: #{e.message}")
  end
end

def filter(event)
  if needs_refresh?
    load_database
  end

  entry = event.get('[Analyzer]')
  unless entry.nil?
    enrich_geoloc(event, entry, '[Analyzer]', 'GeoLocation', 'Location')
  end

  ["Source", "Target", "Vector"].each do |cls|
    (event.get(cls) || []).each_with_index do |entry, index|
      enrich_geoloc(event, entry, "[#{cls}][#{index}]", 'GeoLocation', 'Location')
    end
  end

  # For events whose "RawLog" attachment is assuredly defined,
  # try to enrich the location based on the geo-coordinates.
  if event.get('[@metadata][kafka][key]') != 'IDMEFv2'
    @ecs.each do |cls|
      entry = event.get("[Attachment][RawLog][Content]#{cls}[geo]")
      if entry.nil?
        next
      end

      enrich_geoloc(event, entry, "[Attachment][RawLog][Content]#{cls}[geo]", 'location', 'name')
    end
  end

  return [event]
end
