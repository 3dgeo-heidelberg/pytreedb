from pytreedb import db, db_utils

print("##########################################")
print("  Run some example imports...")
print("##########################################")

print("# Create pytreedb - incl. local file and mongoDB connection")
mydbfile = "my_first_pytree.db"  # file where database is stored locally additionally to MongoDB

print("# Create PyTreeDB object and read MongoDB connection from local .env file")
mydb = db.PyTreeDB(dbfile=mydbfile)

print(
    "# Fresh import data from into pytreedb from URL which provides zipped folder with geojson files of each tree "
    "to be added"
)
mydb.import_data(
    r"https://github.com/3dgeo-heidelberg/pytreedb/raw/main/data/test/geojsons.zip",
    overwrite=True,
)
print(mydb.get_stats())  # print short stats after import

print("# Import from URL with GeoJSON files but appending not clearing the pytreedb first")
mydb.import_data(
    "https://github.com/3dgeo-heidelberg/pytreedb/raw/main/data/test/geojsons.zip",
    overwrite=False,
)
print(mydb.get_stats())

print("# Import and append data from local already existing pytreedb file")
mydb.import_db(r"../data/db_dump/data.db", overwrite=False)
print(mydb.get_stats())

print("# Import and append pytreedb file from URL")
mydb.import_db("https://github.com/3dgeo-heidelberg/pytreedb/raw/main/data/test/data.db", overwrite=False)
print(mydb.get_stats())

print("# Fresh import pytreedb file from URL")
mydb.import_db(
    "https://github.com/3dgeo-heidelberg/pytreedb/raw/main/data/test/data.db",
    overwrite=True,
)
print(mydb.get_stats())

print("# Import and thus append other serialized pytreedb file")
mydb.import_db(r"../data/db_dump/data_copy.db")
print(mydb.get_stats())

print("# Import and append from local folder containing geojsons")
mydb.import_data(r"..\data\geojson\trees\\", overwrite=False)
print(mydb.get_stats())

print("# Clear connected MongoDB from data")
mydb.clear()
print(mydb.get_stats())

print("# Load local pytreedb file")
mydb.load(mydbfile)
print(mydb.get_stats())

print("# Save database to compressed serialized version.")
mydb.save()

print(f"# Save database to compressed serialized version as a new file: new_{mydbfile}")
mydb.save("new_" + mydbfile)

print("# Validate input GEOJSON if all mandatory keys are present")
print(mydb.validate_json(r"..\data\geojson\AbiAlb_BR03_01.geojson"))

print(
    "# Show how to use a pytreedb util function: Generate SHA-1 hash for a file "
    "(e.g. could be used to check if content has changed"
)
print(db_utils.hash_file(mydb.dbfile))

print("#DONE.")
