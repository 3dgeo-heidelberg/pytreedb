#load module
import pytreedb.pytreedb as pytreedb

#Test import from ZIP web resource
db = pytreedb.PyTreeDB(dbfile=r'E:\tmp\SYSSIFOSS\syssifoss.db')
db.import_data(r'https://heibox.uni-heidelberg.de/f/fc5e3cc8d93d4e0ca53b/?dl=1', overwrite=True)
print(db.get_stats())

# Create or load db from previous import
mydb = pytreedb.PyTreeDB(dbfile=r'E:\tmp\SYSSIFOSS\syssifoss.db')
mydb = pytreedb.PyTreeDB(dbfile=r'E:\work\heidelberg\syssifoss.db')


#Validate input GEOJSON if all mandatory keys are present
# mydb.validate_json('C:/Users/bhoefle/Downloads/geojsons/B_BR01_01.geojson')
mydb.validate_json(r'C:\Users\Anna\AppData\Local\Temp\tmpf52gu1pn\AbiAlb_BR03_01.geojson')

#Import data: append or create
mydb.import_data(r'E:\work\heidelberg\geojsons', overwrite=True)
#mydb.import_data(r'https://heibox.uni-heidelberg.de/f/05969694cbed4c41bcb8/?dl=1', overwrite=True)

#mydb.import_data(r'C:\Users\bhoefle\Downloads')
print(mydb.get_stats())

"""
# Run performance test with large import
for i in range (0,500):
    sys.stdout.write("\r%s" % (i))
    sys.stdout.flush()
    mydb.import_data(r'D:\tmp\SYSSIFOSS', overwrite=False)

"""

# Print statistics and DB infos
print(mydb.get_stats())                      # Print statistiscs of trees in DB
print(mydb.get_list_species())                # Print unique species names
print(mydb.get_shared_properties())           #Print tree properties that are shared among all trees (i.e. available for all trees)

# Iterate over the objects in the database
for tree in mydb:
    print(tree['_file'])
    print(tree['geometry']['coordinates'])
    print(tree['_geometry'])
    print(tree['properties']['data'])
    print("------------------------------------------------------------------------")

# Access objects via index subscription (__getitem__)
print(mydb[[2]])                            # get subset dict with int index
print(mydb[[1,0]])                          # get subset dict by providing list of indices
print(mydb.get_tree_as_json(mydb[0]))          # get first object as JSON (as in input file)
print(mydb[1]['_file'])                     # what was the name of the input file
print(mydb[0]['_date'])                     # when was the object added to the DB
print([k['id'] for k in mydb[:]])           # get list[ids] of subset provided by slicing on indices

# Queries on keys/values
print("Query result <tree id>:", len(mydb.query('species', 'Fagus s')) )#get subset of db fufilling query
print("Query species result <tree id>:", len(mydb.query_by_species('Lari'))) #get subset of db fufilling query
print("Query results for trees with quality=3 (on any dataset): ", len(mydb.query('quality', '3', regex=False))) #query in exact manner
print("Query result 'leaf-on' :", len(mydb.query('canopy_condition', 'leaf-on')))  # get subset of db fufilling query
print("Query result 'leaf-off':", len(mydb.query('canopy_condition', 'leaf-off')))  # get subset of db fufilling query
print("Query result 'leaf-on' (exact value search):", len(mydb.query('canopy_condition', 'leaf-on', False)))  # get subset of db fufilling query in exact manner

print("Query by numeric comparison - quality == 3(eq): ", len(mydb.query_by_numeric_comparison('quality', 3, pytreedb.eq)))
print("Query by numeric comparison - quality <= 3 (le): ", len(mydb.query_by_numeric_comparison('quality', 3, pytreedb.le)))
print("Query by numeric comparison - pointCount < 5000 : ", len(mydb.query_by_numeric_comparison('pointCount', 5000, pytreedb.lt)))
print("Query result 'ALS' :", len(mydb.query('mode', 'ALS', regex=False)))  # get subset of db fufilling query
print("Query if key exists: season: ", len(mydb.query_by_key_exists('canopy_condition')))
print("Query if key exists: crown_diameter_1_m: ", len(mydb.query_by_key_exists('crown_diameter_1_m')))

#Query by date
print("Query by date: ", len(mydb.query_by_date('date','2020-01-01', pytreedb.gt)))

#Query by search geometry [watch out latlon]
print("Distance search1: ", len(mydb.query_by_geometry('{"type": "Point", "coordinates": [ -121.425061, 40.506229, 233.56 ] }', distance=1.0)))
print("Distance search2: ", len(mydb.query_by_geometry('{"type": "Point", "coordinates": [ -121.425061, 40.506229, 233.56 ] }', distance=1.0)))
print("Distance search3: ", len(mydb.query_by_geometry('{"type": "Polygon", "coordinates": [[[ -120, 40  ],  [  -120,  41  ],  [  -119,  41  ],  [  -119,  40  ],  [  -120,  40  ]  ]  ]  }', distance=1.0)))

# Get tree ids for a query result
print(mydb.get_ids(mydb.query('species', 'Fagus s')))

# Query and join results(lists) using a logical operator
print("Join (trees) results AND:", mydb.join([mydb[0:2],mydb.to_list()], operator='and'))
print("Join (trees) results OR :", mydb.join([mydb[0:1],mydb[0:]], operator='or'))

#Query example: Select tree species AND
res_fagus = mydb.query('species', 'Fagus s')
res_ALS = mydb.query('mode', 'ALS')
res_fagus_ALS =  mydb.join([res_fagus, res_ALS], operator='and')
print("Fagus with ALS data: ",res_fagus_ALS)
# print(mydb[res_fagus]) res_fagus is a list of strings (tree ids). 

#Query example: Get trees with Field Inventory measurements (FI)
res_fi = mydb.query('source', 'FI')
print(mydb.get_ids(res_fi))
for t in res_fi:
    print("Measurements for tree (id=%s)" % (t['properties']['id']))
    print("----------------------------------------")
    print (t['properties']['measurements'])

#Query example: Date search

print(pytreedb.hash_file(mydb.dbfile))

# Get original JSON(str) of a tree
json_of_first_tree = mydb.get_tree_as_json(mydb[0])
print(json_of_first_tree)

# Export data
mydb.export_data('d:/tmp/test')                   # Export all, = reverse of import_data()
mydb.export_data('d:/tmp/test2', trees=[1,5])     # Export only subset
mydb.export_data(r'E:\tmp\test')
mydb.export_data(r'E:\tmp\test2', trees=[1,5])
