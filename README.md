Waymarked Trails - Database Backend
===================================

[Waymarked Trails](https://waymarkedtrails.org) is a website that shows
recreational routes from [OpenStreetMap](https://openstreetmap.org) and
lets you inspect the routes and selected details.

This repository contains the database backend and map rendering. This is
sufficient for creating the map overlays.

To set up the full site, you also need:
* the [API](https://github.com/waymarkedtrails/waymarkedtrails-api)
* the [website](https://github.com/waymarkedtrails/waymarkedtrails-website)


Installation
============

The code is written in Python3. The installation should work on any Linux-like
system. However, the production servers run on Debian 12, so this is what is
tested. If possible, use this for development/testing as well. Alternatively
install all Python dependencies via pip.

Installing prerequisites
------------------------

You need to first install
[osgende](https://github.com/waymarkedtrails/osgende) and
[waymarkedtrails-shields](https://github.com/waymarkedtrails/waymarkedtrails-shields)
as well as their respective requirements.
Rendering requires [Mapnik](https://mapnik.org/) together with its Python
bindings. PyCairo >= 1.18 is needed or shields will have the wrong size.
SQLAlchemy is needed in version 2.0+.

On Ubuntu 24.04/Debian 12 the following should install all prerequisites:

    sudo apt install python3-psycopg2 python3-pip \
                     python3-gi python3-gi-cairo \
                     libcairo2-dev gir1.2-pango-1.0 gir1.2-rsvg-2.0 \
                     gcc libcairo2-dev pkg-config python3-dev \
                     git python3-jinja2 python3-mapnik python3-virtualenv

Then install the remaining dependencies in a virtual environment:

    virtualenv -p python3 --system-site-packages wmtenv
    . wmtenv/bin/activate

    pip install -U osmium PyCairo shapely \
                   SQLAlchemy GeoAlchemy2 \
                   git+https://github.com/waymarkedtrails/osgende@master \
                   git+https://github.com/waymarkedtrails/waymarkedtrails-shields@master

Finally, from the root of this repo, run the following to install the backend:

    pip install .


Setting up PostgreSQL
---------------------

Next you need to install and set up [PostgreSQL](https://postgresql.org/).
First install the appropriate packages:

    sudo apt install postgresql postgresql-postgis


You need two PostgreSQL users for waymarkedtrails: the user that imports and
updates the data needs superuser database rights. The second user is used for
serving the data and only get read access to the database. On Debian/Ubuntu
this should usually be the website user 'www-data'. Create both users
with:

    sudo -u postgres createuser -s <username>
    sudo -u postgres createuser www-data


Importing a new database
------------------------

The waymarkedtrails database consists of a single OSM backing database which
contains a snapshot of the full OSM data and multiple sub-databases in
separate schemas which contain the data for the various route maps.

### Configuring the Installation

Custom configuration is expected in the module `wmt_local_config.backend`. To
create such a file create first a directory `wmt_local_config` and then
create a file `backend.py`. See `wmt_db/config/common.py` for possible settings.
In particular you might want to set:

 * `DB_NODESTORE` to enable storage of node locations in an external file
   instead of the database. Point to the file to use, must be a python `str`.
   This saves a large amount of space for larger
   installation (Europe, planet etc.). Plan about 90GB for the file.
 * `SYMBOL_DIR` is the directory where shield graphics are stored. Must be
   a `pathlib.Path` object.

Make sure to put the parent directory of `wmt_local_config` into the
`PYTHONPATH`, so that Python can find the file.

### Importing the backing database

To import the backing database, download a recent OSM planet or extract and
create the database with:

    wmt-makedb -f planet.osm.pbf db import

This creates a database with the name `planet`. Run `wmt-makedb --help` to see
what options there are to tweak database name and user name.

Importing the planet takes quite a while. Once it is finished, you need to add
country data. We use the data from the Nominatim project:

```
psql -d planet -c "DROP table IF EXISTS country_osm_grid"
wget https://nominatim.org/data/country_grid.sql.gz
zcat country_grid.sql.gz | psql -d planet
psql -d planet -c "ALTER TABLE country_osm_grid ADD COLUMN geom geometry(Geometry,3857)"
psql -d planet -c "UPDATE country_osm_grid SET geom=ST_Transform(geometry, 3857)"
psql -d planet -c "ALTER TABLE country_osm_grid DROP COLUMN geometry"
psql -d planet -c "CREATE INDEX idx_country_osm_grid_geom ON country_osm_grid USING gist(geom)"
```

Finally prepare some indexes we need to updating:

    wmt-makedb db prepare


### Importing route databases

Once the backing database is finished, you may add additional route databases
by running the following commands:

```
wmt-makedb hiking create
wmt-makedb hiking import
wmt-makedb hiking dataview
```

Replace `hiking` with the route flavour you want to import.

### Rendering maps

Maps may be rendered with Mapnik using your favourite render infrastructure.
The default style for each map flavour can be created using:

```
wmt-makedb hiking mapstyle > hiking.xml
```

Updating the database
---------------------

To update the database with latest data from OpenStreetMap, you need to run
updates for each of the parts you have imported:

```
wmt-makedb db update
wmt-makedb hiking update
```


Where to go from here
---------------------

To set up the full website stack, continue now with the installation
instructions for the [API](https://github.com/waymarkedtrails/waymarkedtrails-api).

License
=======

The source code is available under GPLv3. See COPYING for more information.

Images in `wmt_db/data/shields` are an exception. Rights remain with the operators
of the respective routes.
