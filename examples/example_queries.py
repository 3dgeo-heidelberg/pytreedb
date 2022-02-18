#load modules
from pytreedb import db
import sys
import json

#Create pytreedb and load existing database from local file
mydbfile='syssifoss.db'
mydb = db.PyTreeDB(dbfile=mydbfile, mongodb = {"uri": "mongodb://127.0.0.1:27017/", "db": "pytreedb", "col": "syssifoss"})

print("Import new")
mydb.import_data(r'https://heibox.uni-heidelberg.de/f/05969694cbed4c41bcb8/?dl=1', overwrite=True)
print(mydb.get_stats())

"""
print("Import false")
mydb.import_data(r'https://heibox.uni-heidelberg.de/f/05969694cbed4c41bcb8/?dl=1', overwrite=False)
print(mydb.get_stats())

print("Import db from local file")
mydb.import_db(r'../data/db_dump/data.db', overwrite=False)
print(mydb.get_stats())

print("Import db from URL")
mydb.import_db('https://heibox.uni-heidelberg.de/f/182057733fa34ba2bcd6/?dl=1', overwrite=False)
print(mydb.get_stats())

print("Import db from URL - overwrite")
mydb.import_db('https://heibox.uni-heidelberg.de/f/182057733fa34ba2bcd6/?dl=1', overwrite=True)
print(mydb.get_stats())


print("Clear")
mydb.clear()
print(mydb.get_stats())

print("Load")
mydb.load(mydbfile)
print(mydb.get_stats())
mydb.save()

print("Save db as gzip file")
mydb.save('D:/tmp/syssifoss.db')


print("Load db as gzip file")
mydb.load('D:/tmp/syssifoss.db')
print(mydb.get_stats())

print("Clear")
mydb.clear()
print(mydb.get_stats())
print("-----Clear")

mydb.import_data(r'https://heibox.uni-heidelberg.de/f/05969694cbed4c41bcb8/?dl=1', overwrite=False)
print("Save db as gzip file")
mydb.save('syssifoss_snapshot.db')
print("Load db as gzip file")
mydb.load('syssifoss_snapshot.db')
print(mydb.get_stats())

#Validate input GEOJSON if all mandatory keys are present
mydb.validate_json(r'D:\data\SYSSIFOSS\geojsons\geojsons\AbiAlb_BR03_01.geojson')

#Import data: append or create
mydb.import_data(r'D:\data\SYSSIFOSS\geojsons\geojsons\\', overwrite=False)

#Import other serialized db file
mydb.import_db(r'D:\tmp\SYSSIFOSS\syssifoss_mongo_copy.db')
print(mydb.get_stats())

# Run performance test with large import
#for i in range (0,100):
#    mydb.import_data(r'D:\data\SYSSIFOSS\geojsons\geojsons\\', overwrite=False)


# Print statistics and DB infos
print(mydb.get_stats())                      # Print statistiscs of trees in DB
print(mydb.get_list_species())           # Print unique species names
print(mydb.get_shared_properties())  #Print tree properties that are shared among all trees (i.e. available for all trees)

# Iterate over the objects in the database
for tree in mydb:
    print(tree['geometry']['coordinates'])
    print(tree['properties']['data'])
    print("------------------------------------------------------------------------")
    break

# Access objects via index subscription (__getitem__)
print(mydb[[2]])                            # get subset dict with int index
print(mydb[0])
print(mydb[[1,0]])                          # get subset dict by providing list of indices
print(mydb[0]["_file"])                                   # what was the name of the input file
print(mydb[0]["_date"])                                   # when was the object added to the DB
print(mydb.get_tree_as_json(mydb[0]))          # get first object as JSON (as in input file)
print([k['_file'] for k in mydb[1:2]])           # get list of a specific field for all trees fulfilling slicing
print(len(mydb[:]))                                 # get number of all trees fulfilling slicing

# Queries on single fields
print("Query result <tree id>:", len(mydb.query({"properties.species": "Abies alba"}, limit=10)) )#get all trees fulfilling filter (as dict)
print("Query results for trees with quality=3 (on any dataset): ", len(mydb.query({"properties.data.quality": "3"})))
print("Query result 'leaf-on' :", len(mydb.query({'properties.data.canopy_condition': 'leaf-on'})))  # get subset of db fufilling query
print("Query result 'leaf-off':", len(mydb.query({'properties.data.canopy_condition': 'leaf-off'})))  # get subset of db fufilling query
print("Query result 'ALS' :", len(mydb.query({"properties.data.mode": "ALS"})))  # get subset of db fufilling query


#Queries with logical operator between conditions
#See: https://docs.mongodb.com/manual/reference/operator/query/
print("Query results for trees with quality=3 (for ALS only): ", len(mydb.query({"$and": [{"properties.data.quality": "3"}, {"properties.data.mode": "ALS"}]})))
print("Query results for trees with quality=3 (for TLS only): ", len(mydb.query({"$and": [{"properties.data.quality": "3"}, {"properties.data.mode": "TLS"}]})))

#Numeric comparisons (for fields with numeric values)
print("Numeric comparison on point count:", len(mydb.query({'properties.data.point_count': { "$gt": 100000}})))  # get subset of db fufilling query
print("Query by numeric comparison - pointCount < 5000 : ", len(mydb.query({'properties.data.point_count': { "$lt": 5000}})))

print("Query if key exists: 'properties.measurements.crown_base_height_m': ", len(mydb.query_by_key_exists('properties.measurements.crown_base_height_m')))

print("Query species with regex 'Quercus*': ", len(mydb.query_by_species('Quercus*')))
print("Query species with regex 'Quercus pet*': ", len(mydb.query_by_species('Quercus pet*')))
print("Query result of exact search: Quercus petrea:", len(mydb.query({"properties.species": "Quercus petraea"})) )#get all trees fulfilling 

print("Query by key and value:", len(mydb.query_by_key_value(key="properties.species", value="Quercus petraea", regex=False)    ) )
print("Query by key and value:", len(mydb.query_by_key_value(key="properties.species", value="Quercus *", regex=True)    ) )

#Query by date
print("Query by date:", len(mydb.query_by_date(key="properties.measurements.date", start="2019-08-28", end='2022-01-01')    ) )
print("Query by date:", len(mydb.query_by_date(key="properties.data.date", start="2019-08-28")    ) )

#Query by search geometry [watch out latlon]
print("Distance search1: ", len(mydb.query_by_geometry(json.loads('{"type": "Point", "coordinates": [ 8.682112, 49.014387] }'), distance=2000.0)))

print("Distance search2: ", len(mydb.query_by_geometry('{"type": "Point", "coordinates": [ 8.682112, 49.014387]}', distance=1500.0)))

print("Distance search3: ", len(mydb.query_by_geometry('{ "type": "Polygon", "coordinates": [ [ [ 8.700980940620983, 49.012725603975355 ], [ 8.700972890122355, 49.011695140150906 ], [ 8.70235623413669, 49.01167501390433 ], [ 8.702310614644462, 49.012713528227415 ], [ 8.702310614644462, 49.012713528227415 ], [ 8.700980940620983, 49.012725603975355 ] ] ] }', distance=0.0)))

trees_in_poly = mydb.query_by_geometry('{ "type": "Polygon", "coordinates": [ [ [ 8.700980940620983, 49.012725603975355 ], [ 8.700972890122355, 49.011695140150906 ], [ 8.70235623413669, 49.01167501390433 ], [ 8.702310614644462, 49.012713528227415 ], [ 8.702310614644462, 49.012713528227415 ], [ 8.700980940620983, 49.012725603975355 ] ] ] }', distance=0.0)
for tree in trees_in_poly:
    print(tree['_file'])
    break

# Get tree ids for a query result
print(mydb.get_ids(mydb.query({"properties.species": "Abies alba"}, limit=10, skip=10)))
print(mydb.get_ids(mydb.query({"properties.species": "Abies alba"}, limit=1)))
"""


print ("# Query examples for AND and OR as well as nested queries")
#https://www.analyticsvidhya.com/blog/2020/08/query-a-mongodb-database-using-pymongo/
print(mydb.get_ids(mydb.query({"$or":[{"properties.species": "Abies alba"}, {"properties.species": "Fagus sylvatica"}]})))
print(mydb.get_ids(mydb.query({"$and":[{"properties.species": "Abies alba"}, {"properties.data.mode": "TLS"}]})))
print(mydb.get_ids(mydb.query({"$and":[{"properties.species": "Abies alba"}, {"$or":[{"properties.data.mode": "TLS"}, {"properties.data.mode": "ALS"}]}]})))


sys.exit()

"""

#Query example: Get trees with Field Inventory measurements (FI)
res_fi = mydb.query('source', 'FI')
print(mydb.get_ids(res_fi))
for t in res_fi:
    print("Measurements for tree (id=%s)" % (t['properties']['id']))
    print("----------------------------------------")
    print (t['properties']['measurements'])

#Query example: Date search

print(db.hash_file(mydb.dbfile))

# Get original JSON(str) of a tree
json_of_first_tree = mydb.get_tree_as_json(mydb[0])
print(json_of_first_tree)

# Export data
mydb.export_data('d:/tmp/test')                   # Export all, = reverse of import_data()
mydb.export_data('d:/tmp/test2', trees=[1,5])     # Export only subset
mydb.export_data(r'd:\tmp\test')
mydb.export_data(r'd:\tmp\test2', trees=[1,5])

"""
