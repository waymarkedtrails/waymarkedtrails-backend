Waymarked Trails - Database Backend
===================================

[Waymarked Trails](https://waymarkedtrails.org) is a website that shows
recreational routes from [OpenStreetMap](https://openstreetmap.org) and
lets you inspect the routes and selected details.

This repository contains the database backend and map rendering. For the
website frontend have a look at
[waymarked-trails-site](https://github.com/waymarkedtrails/waymarked-trails-site).

Installation
============

The code is written in Python3. You need to install
[osgende](https://github.com/waymarkedtrails/osgende) and
[waymarkedtrails-shields](https://github.com/waymarkedtrails/waymarkedtrails-shields)
first as well as their respective requirements.

Rendering requires [Mapnik](https://mapnik.org/) together with its Python
bindings.

No special installation is needed for this repository. Just download the code
and run the scripts in place.

Importing a new database
------------------------

The waymarkedtrails database consists of a single OSM backing database which
contains a snapshot of the complete OSM data and multiple sub-databases in
separate schemas which contain the data for the various route maps.

### Importing the backing database

To import the backing database, download a recent OSM planet or extract and
create the database with:

    ./makedb.py -f planet.osm.pbf db import

This creates a database with the name `planet`. Run `./makedb.py --help` to see
what options there are to tweak database name and user name.

Importing the planet takes quite a while. Once it is finished, you need to add
country data. We use the data from the Nominatim project:

```
psql -d planet -c "DROP table IF EXISTS country_osm_grid"
wget https://nominatim.org/data/country_grid.sql.gz
zcat country_osm_grid.sql.gz | psql -d planet
psql -d planet -c "ALTER TABLE country_osm_grid ADD COLUMN geom geometry(Geometry,3857)"
psql -d planet -c "UPDATE country_osm_grid SET geom=ST_Transform(geometry, 3857)"
psql -d planet -c "ALTER TABLE country_osm_grid DROP COLUMN geometry"
psql -d planet -c "CREATE INDEX idx_country_osm_grid_geom ON country_osm_grid USING gist(geom)"
```

Finally prepare some indexes we need to updating:

    ./makedb.py db prepare


### Importing route databases

Once the backing database is finished, you may add additional route databases
by running the following commands:

```
./makedb.py hiking create
./makedb.py hiking import
./makedb.py hiking dataview
```

Replace `hiking` with the route flavour you want to import.

Updating the database
---------------------

To update the database with latest data from OpenStreetMap, you need to run
updates for each of the parts you have imported:

```
./makedb.py db update
./makedb.py hiking update
```

License
=======

The source code is available under GPLv3. See COPYING for more information.
