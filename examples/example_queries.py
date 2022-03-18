#load modules
import sys
from pytreedb import db
import os
import json
import numpy as np

print("##########################################")
print("  Run some example queries and exports...")
print("##########################################")

print("# Create PyTreeDB object and read MongoDB connection from local .env file")
mydbfile='my_first_pytree.db' #file where database is stored locally additionally to MongoDB
mydb = db.PyTreeDB(dbfile=mydbfile)
mydb.import_db(r'../data/db_dump/data.db', overwrite=False)

print("# Print statistics and some DB infos")
print(" - Main stats: %s" %  mydb.get_stats())                      # Print statistics of trees in DB
print(" - Unique species: %s" %  mydb.get_list_species())           # Print unique species names
print(" - Tree properties that are shared among all trees (i.e. available for all trees): %s" %  mydb.get_shared_properties())  

print()
print("# Test to iterate over the objects in the database")
for tree in mydb:
    print(tree['geometry']['coordinates'])
    print(tree['properties']['data'])
    print("----------------------------- stop after 1 iteration -----------------------------------")
    break
    
print("# Access objects via index subscription (__getitem__)")
print(" - Get subset dict with int index:  mydb[[2]] --> %s" % mydb[[2]])                            
print(" - Get single tree object with int index: mydb[0] -->%s" % mydb[0])
print(" - Get subset dict by providing list of indices: mydb[[1,0]] --> %s " %  mydb[[1,0]])                          
print(" - Try slicing: len(mydb[:]) --> %s " % len(mydb[:]))      
print(" - Get list of a specific field for all trees fulfilling slicing: [k['_file'] for k in mydb[1:2]] --> %s" % [k['_file'] for k in mydb[1:2]])

print()
print("What was the name of the input GeoJSON for this tree: mydb[0][\"_file\"] --> %s" % mydb[0]["_file"])
print("When was the object added to the pytreedb: mydb[0][\"_date\"] --> %s" % mydb[0]["_date"])     

print()
print("# Queries on single fields")
print(" - Trees fulfilling filter (as dict) - Abies alba:", len(mydb.query({"properties.species": "Abies alba"}, limit=10)) )
print(" - Query result trees with quality=3 (on any dataset): ", len(mydb.query({"properties.data.quality": 3})))
print(" - Query result 'leaf-on' :", len(mydb.query({'properties.data.canopy_condition': 'leaf-on'})))  
print(" - Query result 'leaf-off':", len(mydb.query({'properties.data.canopy_condition': 'leaf-off'}))) 
print(" - Query result mode is 'ALS' :", len(mydb.query({"properties.data.mode": "ALS"})))

print()
print("#Queries with logical operator between conditions") #See MongoDB reference: https://docs.mongodb.com/manual/reference/operator/query/
print("Query results for trees with quality=3 (for ALS only): ", len(mydb.query({"$and": [{"properties.data.quality": 3}, {"properties.data.mode": "ALS"}]})))
print("Query results for trees with quality=3 (for TLS only): ", len(mydb.query({"$and": [{"properties.data.quality": 3}, {"properties.data.mode": "TLS"}]})))

print()
print("# Numeric comparisons (for fields with numeric values)")
print(" - Numeric comparison on point_count > 100000:", len(mydb.query({'properties.data.point_count': { "$gt": 100000}}))) 
print(" - Query by numeric comparison - point_count < 5000 : ", len(mydb.query({'properties.data.point_count': { "$lt": 5000}})))

print()
print("# Get objects for which a certain key exists: 'properties.measurements.crown_base_height_m': ", len(mydb.query_by_key_exists('properties.measurements.crown_base_height_m')))

print()
print("# Query with regex and exact search")
print(" - Query species with regex 'Quercus*': ", len(mydb.query_by_species('Quercus*')))
print(" - Query species with regex 'Quercus pet*': ", len(mydb.query_by_species('Quercus pet*')))
print(" - Query result of exact search: Quercus petrea:", len(mydb.query({"properties.species": "Quercus petraea"})) )

print()
print("# Query by a single key and respective value for a field")
print(" - Query by key and value without regex (key=\"properties.species\", value=\"Quercus petraea\"): ", len(mydb.query_by_key_value(key="properties.species", value="Quercus petraea", regex=False)) )
print(" - Query by key and value with regex (key=\"properties.species\", value=\"Quercus *\"): ", len(mydb.query_by_key_value(key="properties.species", value="Quercus *", regex=True)    ) )

print()
print("# Query by date")
print(" - Query with start and end date (key=\"properties.measurements.date\", start=\"2019-08-28\", end=\"2022-01-01\"):", len(mydb.query_by_date(key="properties.measurements.date", start="2019-08-28", end='2022-01-01')    ) )
print(" - Query with only start date (key=\"properties.data.date\", start=\"2019-08-28\"):", len(mydb.query_by_date(key="properties.data.date", start="2019-08-28")    ) )

print()
print("# Query by search geometry [watch out LatLon requirement]")
print(" - Distance search around point (2000m): ", len(mydb.query_by_geometry(json.loads('{"type": "Point", "coordinates": [ 8.682112, 49.014387] }'), distance=2000.0)))
print(" - Distance search around point (1500m): ", len(mydb.query_by_geometry('{"type": "Point", "coordinates": [ 8.682112, 49.014387]}', distance=1500.0)))
print(" - Query by search geometry, here point-in-polygon: ", len(mydb.query_by_geometry('{ "type": "Polygon", "coordinates": [ [ [ 8.700980940620983, 49.012725603975355 ], [ 8.700972890122355, 49.011695140150906 ], [ 8.70235623413669, 49.01167501390433 ], [ 8.702310614644462, 49.012713528227415 ], [ 8.702310614644462, 49.012713528227415 ], [ 8.700980940620983, 49.012725603975355 ] ] ] }', distance=0.0)))

print()
print("# Store search result in variable and loop over it")
trees_in_poly = mydb.query_by_geometry('{ "type": "Polygon", "coordinates": [ [ [ 8.700980940620983, 49.012725603975355 ], [ 8.700972890122355, 49.011695140150906 ], [ 8.70235623413669, 49.01167501390433 ], [ 8.702310614644462, 49.012713528227415 ], [ 8.702310614644462, 49.012713528227415 ], [ 8.700980940620983, 49.012725603975355 ] ] ] }', distance=0.0)
for tree in trees_in_poly:
    print("     e.g. species of first tree found in search polygon : " +tree['_file'])
    break

print()
print(" # Get tree indices (=index to access a tree in pytreedb object) for a query result. Query uses limit and skip parameters")
print(mydb.get_ids(mydb.query({"properties.species": "Abies alba"}, limit=10, skip=10)))
print(mydb.get_ids(mydb.query({"properties.species": "Abies alba"}, limit=1)))

print()
print ("# Query examples for AND and OR as well as NESTED queries")
#https://www.analyticsvidhya.com/blog/2020/08/query-a-mongodb-database-using-pymongo/
print("""mydb.get_ids(mydb.query({"$or":[{"properties.species": "Abies alba"}, {"properties.species": "Fagus sylvatica"}]}))
mydb.get_ids(mydb.query({"$and":[{"properties.species": "Abies alba"}, {"properties.data.mode": "TLS"}]}))
mydb.get_ids(mydb.query({"$and":[{"properties.species": "Abies alba"}, {"$or":[{"properties.data.mode": "TLS"}, {"properties.data.mode": "ALS"}]}]}))""")
print("  Results (indices): ")
print(mydb.get_ids(mydb.query({"$or":[{"properties.species": "Abies alba"}, {"properties.species": "Fagus sylvatica"}]})))
print(mydb.get_ids(mydb.query({"$and":[{"properties.species": "Abies alba"}, {"properties.data.mode": "TLS"}]})))
print(mydb.get_ids(mydb.query({"$and":[{"properties.species": "Abies alba"}, {"$or":[{"properties.data.mode": "TLS"}, {"properties.data.mode": "ALS"}]}]})))

print()
print("# Query example: Get trees with Field Inventory measurements (FI)")
res_fi = mydb.query({"properties.measurements.source": "FI"})
for t in res_fi:
    print("All measurements for tree (id=%s)" % (t['properties']['id']))
    print("----------------------------------------")
    print (t['properties']['measurements'])
    break
  
print()
print("# EXPORT data - options")
print(" - Get original JSON(str) of a tree")
json_of_first_tree = mydb.get_tree_as_json(mydb[0])
print(json_of_first_tree[0:100]+"\n [....]")
print(" - Write/Export selected trees as GeoJSON files to given output directory: mydb.export_data('./output', trees=[1,5])")
files_written = mydb.export_data('./output', trees=[1,5])                   # Export selected trees
print("Files written: %s" % files_written)

print()
print(" - Write/Export all GeoJSON files to given output directory (= revers of import): mydb.export_data('./output2')")
files_written = mydb.export_data('./output2')                   # Export all, = reverse of import_data()
print("Files written: %s" % files_written)

print()
print(" - Export metrics as CSV")
#mydb.convert_to_csv("D:/tmp/")

