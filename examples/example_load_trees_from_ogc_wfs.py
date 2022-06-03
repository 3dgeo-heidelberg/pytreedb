from pytreedb import db, db_utils, db_conf
import csv
import json
import copy
import sys

print("###################################################################################################")
print("  pytreedb - Showcase of import of trees from Open Government Data source - City of Vienna, Austria")
print("###################################################################################################")

URL_DATA = "https://data.wien.gv.at/daten/geo?service=WFS&request=GetFeature&version=1.1.0&typeName=ogdwien:BAUMKATOGD&srsName=EPSG:4326&outputFormat=csv"

# Use pytreedb json template and tweak a little bit
template = json.loads(db_conf.TEMPLATE_GEOJSON)

print ("Download OGC WFS data from: https://data.wien.gv.at")
data_csv = db_utils.download_file_to_tempdir(URL_DATA)

# Read csv file as dict
with open(data_csv, 'r', encoding='utf-8') as f:
    data = list(csv.DictReader(f, delimiter=","))

# Count things
skipped = 0
cnt = 0

print("# Create pytreedb - incl. local file and mongoDB connection")
mydbfile = "vienna_trees.db"  # file where database is stored locally additionally to MongoDB

print("# Create PyTreeDB object and read MongoDB connection from local .env file")
mydb = db.PyTreeDB(dbfile=mydbfile)

print("Converting csv input to pytreedb geojson files and import directly...")
for tree in data:
    cnt += 1
    if cnt % 1000 == 0:
        sys.stdout.write("\r{} trees imported.".format(cnt))
    try:
        tree_json = copy.deepcopy(template)

        # Fake individual input file name
        json_file_name = "tree_id_" + tree['OBJECTID'] + ".geojson"
        tree_json["_file"] = json_file_name

        # READ DATA FROM INPUT
        tree_json['properties']['id'] = tree['BAUM_ID']
        tree_json['properties']['source'] = URL_DATA
        tree_json['properties']['species'] = tree['GATTUNG_ART']
        tree_json['properties']['measurements'][0]['DBH_cm'] = int(tree['STAMMUMFANG_TXT'].split("cm")[0])
        tree_json['properties']['measurements'][0]['crown_diameter_m'] = (float(tree['KRONENDURCHMESSER_TXT'][:-1].split("-")[0]) + float(tree['KRONENDURCHMESSER_TXT'][:-1].split("-")[1])) / 2.0
        tree_json['properties']['measurements'][0]['height_m'] = (float(tree['BAUMHOEHE_TXT'][:-1].split("-")[0]) + float(tree['BAUMHOEHE_TXT'][:-1].split("-")[1]) ) / 2.0

        #Set geometry/location by dirty string hacking
        geom_str = tree['SHAPE']
        lon = geom_str.split("(")[1].split(" ")[0]
        lat = geom_str.split("(")[1].split(" ")[1][:-1]
        tree_json['geometry']['coordinates'][0] = float(lon)
        tree_json['geometry']['coordinates'][1] = float(lat)
        tree_json['geometry']['coordinates'][2] = 0.0

        #Add tree directly to database (with faked _file field)
        mydb.add_tree(tree_json)

    except Exception as e:
        skipped +=1

print("\nManual sync local db file with MongoDB connection...")
mydb.mongodb_synchronize()
print("Save db locally in file: {}".format(mydb.dbfile))
mydb.save()
print("done.")

print("\n{} trees found. {} trees skipped due to formatting problems or missing information.".format(cnt, skipped))
print(mydb.get_stats())
print("done.")

