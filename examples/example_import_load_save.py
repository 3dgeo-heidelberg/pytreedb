import sys
import os
import json
from dotenv import load_dotenv
sys.path.append("..")
from pytreedb import db

load_dotenv()
conn_uri = os.environ.get("CONN_URI")
conn_db = os.environ.get("CONN_DB")
conn_col = os.environ.get("CONN_COL")

print("##########################################")
print("  Run some example imports...")
print("##########################################")

print("# Create pytreedb - incl. local file and mongoDB connection") 
mydbfile='my_first_pytree.db' #file where database is stored locally additionally to MongoDB

print("# Define (local) MongoDB connection")
mydb = db.PyTreeDB(dbfile=mydbfile, mongodb = {"uri": conn_uri, "db": conn_db, "col": conn_col})

print("# Fresh import data from into pytreedb from URL which provides zipped folder with geojson files of each tree to be added")
mydb.import_data(r'https://heibox.uni-heidelberg.de/f/92dcfa3eecb240a6b550/?dl=1', overwrite=True)
print(mydb.get_stats()) # print short stats after import

print ("# Import from URL with GeoJSON files but appending not clearing the pytreedb first")
mydb.import_data(r'https://heibox.uni-heidelberg.de/f/92dcfa3eecb240a6b550/?dl=1', overwrite=False)
print(mydb.get_stats())

print ("# Import and append data from local already existing pytreedb file")
mydb.import_db(r'../data/db_dump/data.db', overwrite=False)
print(mydb.get_stats())

print("# Import and append pytreedb file from URL")
mydb.import_db('https://heibox.uni-heidelberg.de/f/2be9b438f7d94e12a091/?dl=1', overwrite=False)
print(mydb.get_stats())

print("# Fresh import pytreedb file from URL")
mydb.import_db('https://heibox.uni-heidelberg.de/f/2be9b438f7d94e12a091/?dl=1', overwrite=True)
print(mydb.get_stats())

print ("# Import and thus append other serialized pytreedb file")
mydb.import_db(r'../data/db_dump/data_copy.db')
print(mydb.get_stats())

print ("# Import and append from local folder containing geojsons")
mydb.import_data(r'..\data\geojson\trees\\', overwrite=False) 
print(mydb.get_stats())

print("# Clear connected MongoDB from data")
mydb.clear()
print(mydb.get_stats())

print("# Load local pytreedb file")
mydb.load(mydbfile)
print(mydb.get_stats())

print("# Save database to compressed serialized version.")
mydb.save()

print("# Save database to compressed serialized version as a new file: "+"new_"+mydbfile)
mydb.save("new_"+mydbfile)

print("# Validate input GEOJSON if all mandatory keys are present")
print(mydb.validate_json(r'..\data\geojson\AbiAlb_BR03_01.geojson'))

print("# Show how to use a pytreedb util function: Generate SHA-1 hash for a file (e.g. could be used to check if content has changed")
print(db.hash_file(mydb.dbfile))

print("#DONE.")