from os import environ as os_environ

MEDIA_URL = 'http://wmt.loar/static'
TILE_BASE_URL = 'http://wmt.loar/tiles/' + os_environ.get('WMT_CONFIG', '')
HILLSHADING_URL = 'http://zephyria/hillshading'

TILE_CACHE = {'type' : 'DummyCache'}

DB_NAME = 'planet'
DB_NODESTORE = '/home/suzuki/osm/data/osgende-test.nodestore'

IMPRESSUM = 'Sarah Hoffmann<br/>\nJüngststr.13<br/>\n01277 Dresden\n\nemail: lonvia@denofr.de'

BASEMAPS = (
  { 'id' : "osm-mapnik",
    'name' : "OSM Standard Map",
    'url' : "https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    'attribution' : '<a href="https://openstreetmap.org">OpenStreetMap</a>(<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-by-SA</a>)'
  },
  { 'id' : "opentopo",
    'name' : "OpenTopoMap",
    'url' : "https://{a-c}.tile.opentopomap.org/{z}/{x}/{y}.png",
    'attribution' : '<a href="https://opentopomap.org/">OpenTopoMap</a>(<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-by-SA</a>)'
  }
)
