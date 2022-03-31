"""
This file contains format specifications and related database field configurations.
In case the geojson format and the fields to be queried are changed, this needs to be specified here.
"""

import pymongo

# INDICES: Define queries and MongoDB indices here
# https://pymongo.readthedocs.io/en/stable/api/pymongo/collection.html#pymongo.collection.Collection.create_index
# Examples:
#   - Single field: [ ("species",1)]
#   - Compound idx: [("properties.species",1), ("properties.data.mode",1)]
INDEX_FIELDS = [[("species", 1)],
                [("properties.data.mode", 1)],
                [("properties.data.date", 1)],
                [("properties.data.canopy_condition", 1)],
                [("properties.data.quality", 1)],
                [("properties.species", 1)],
                [("properties.species", 1),
                 ("properties.data.mode", 1)]]
INDEX_UNIQUE_FIELDS = []  # [[("properties.id", 1)]]
INDEX_GEOM_SPHERE_FIELDS = [("geometry", pymongo.GEOSPHERE)]

# QUERY FIELDS
QUERY_SPECIES_FIELDNAME = "properties.species"
QUERY_GEOMETRY = "geometry"

# GEOJSON Format Specification: Minimal format of input geojson. This variable is used to validate the input format
TEMPLATE_GEOJSON = """{
    "type": "Feature",
    "properties": {
        "id": 1,
        "source": "http://syssifoss.db",
        "species": "Fagus sylvatica L.",
        "measurements": [
          {
            "source": "FI",
            "date": "2019-01-01"
          }
        ],
        "measurements_metadata": [
          {
          }
        ],
        "data": [
          {
            "type": "pointcloud",
            "mode": "TLS",
            "file": "http://jjljljlj",
            "date": "2020-08-11",
            "canopy_condition": "leaf-on",
            "point_count": 1234567,
            "metadata-url": "http://doi",
            "crs": "epsg:25832",
            "quality": 1
          }
        ]
    },
    "geometry": {
    "type": "Point",
        "coordinates": [
            8.709045,
            48.995801,
            291.779968
        ]
    }
}"""
