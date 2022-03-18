from .__init__ import __version__
import json
import os
import datetime
import gzip
import csv

import urllib
import urllib.request

from pathlib import Path
from operator import lt, le, eq, ne, ge, gt  # operator objects
from functools import *

from dotenv import dotenv_values #.env  for DB credentials

import numpy as np
import copy

# import own sub-modules
from pytreedb.db_utils import *
from pytreedb.db_conf import *

import pymongo
from bson.son import SON

class PyTreeDB:
    """ This class is the starting point and the core component of pytreedb

    :ivar str dbfile: local file holding self.db
    :ivar dict mongodb: dict holding mongodb connection infos
    :ivar list db: list of dictionaries (single dicts equal json files)
    :ivar str data: path to input data imported with import (path of last import)
    :ivar dict stats: dictionary holding summary statistics about database
    :ivar int i: needed for iterator

    """

    def __init__(self, dbfile, mongodb={"uri": None, "db": None, "col": None}):

        """ This function initializes a class object

        :param str dbfile: local file holding self.db
        :param dict mongodb: dict holding mongodb connection infos

        """

        self.dbfile = dbfile  # local file holding self.db
        self.mongodb = mongodb  # dict holding mongodb connection infos
        self.db = list()  # data container  -> list of dictionaries (single dicts equal json files)
        self.data = None  # path to input data imported with import (path of last import)
        self.stats = {"n_trees": None, "n_species": None}  # dictionary holding summary statistics about database
        self.i = 0  # needed for iterator
        if self. mongodb["uri"] is None and self. mongodb["db"] is None and self. mongodb["col"] is None:         #Check if .env available and only take if mongodb is not set manually (i.e. all values are None)
            config = dotenv_values(os.path.join(os.getcwd(), '.env')) 
            self.mongodb = { "uri": config["CONN_URI"], "db": config["CONN_DB"], "col": config["CONN_COL"]}
        try:
            # Connect MongoDB
            self.mongodb_client = pymongo.MongoClient(self.mongodb["uri"])  # Check MongoDB connection
            # Check if collection exists.
            if not self.mongodb["col"] in self.mongodb_client[self.mongodb["db"]].list_collection_names():
                print("Collection: {} created.".format(self.mongodb["col"]))
                # Connect and create connection if not yet there.
            # MongoDB collection to be queried
            self.mongodb_col = self.mongodb_client[self.mongodb["db"]][self.mongodb["col"]]
            # Create indices in MongoDB
            self.mongodb_create_indexes()
        except:
            print(f"Could not connect to MongoDB server or establishing sync/indices/etc. to MongoDB: {self.mongodb}.")
            # raise
            sys.exit()

    def __getitem__(self, item):
        """Allow index(int) subscription on the database, list(int) and slicing access with int"""
        if isinstance(item, int):
            """Returns single tree(dict)"""
            return self.db[item]
        elif isinstance(item, list) or isinstance(item, np.ndarray):
            """Returns a list of selected trees(dict)"""
            return list(self.db[key] for key in item)

        elif isinstance(item, slice):
            """Returns list of slicing selected trees(dict) """
            idx_array = np.arange(0, len(self.db))
            return self[idx_array[item]]

    def __len__(self):
        """Returns the number of objects in database"""
        return len(self.db)

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        if self.i >= self.__len__():
            raise StopIteration
        else:
            self.i += 1
            return self[self.i - 1]

    def __copy__(self):
        raise Exception(
            "Copying of PyTreeDb object is not yet safe. Lifehack: Make a new database and import the other db.")

    def save(self, dbfile=None, sync=False):
        """Saves database to compressed serialized version as local file."""
        if dbfile is None:
            dbfile = self.dbfile  # if no filename is given as arg - just overwrite existing file in self.dbfile
        try:
            with gzip.open(dbfile, 'w') as output_file:
                output_file.write(json.dumps(self.db).encode('utf-8'))
            if sync is True:
                upload_result = self.mongodb_synchronize(clear=True)
                print(f"{len(upload_result.inserted_ids)} trees synchronized with MongoDB server.")
        except:
            raise Exception(f"Could not write db file {dbfile}. Path or permissions might be missing.")

    def load(self, dbfile, sync=True):
        """Loads existing compressed serialized version of database.

        :param str dbfile: data base file
        :param bool sync: synchronize MongoDB immediately after loading (clears MongoDB first)

        """
        try:
            with gzip.open(dbfile, 'r') as input_file:
                self.db = json.loads(input_file.read().decode('utf-8'))
            if sync is True:
                upload_result = self.mongodb_synchronize(clear=True)
                print(f"{len(upload_result.inserted_ids)} trees synchronized with MongoDB server.")
        except:
            raise Exception(f"Could not read db file {dbfile}. File might be corrupt.")

    def clear(self):
        """Clear database and MongoDB. Start with empty data and MongoDB. Does not empty local db file."""
        self.__init__(self.dbfile, self.mongodb)
        self.mongodb_clear_col()

    def import_data(self, path, overwrite=False):
        """Read data (json files) from local file or from URL of ZIP archive with files named like *.*json.

        :param str path: path to input file
        :raises FileNotFoundError: in case file is not found
        :raises: exception in case the input file cannot be read
        :return: number of added trees
        :rtype: int

        """
        if overwrite is True:
            self.clear()  # empty db

        self.data = Path(path)  # URL or local directory used as data storage
        if urllib.parse.urlparse(str(path)).scheme in ('http', 'https',):  # Check if data is local path or URL
            print(f"Download from: {path}")
            data_dir = download_extract_zip_tempdir(path)
        else:
            data_dir = path  # local data
            if not Path(data_dir).exists():
                raise FileNotFoundError(f"Directory <{data_dir}> does not exist.")
        cnt = 0
        for f in Path(data_dir).rglob('*.*json'):
            try:
                self.add_tree_file(f)
                cnt += 1
            except Exception as err:
                print(f"Input file <{f}> cannot be read and is ignored. {err}")

        # Save zipped db file  and synchronize with MongoDB
        self.save(self.dbfile, sync=True)
        return cnt

    def import_db(self, path, overwrite=False):
        """Read data from local db file or from URL. Returns number of trees added"""
        if overwrite is True:
            self.clear()  # empty db

        self.data = Path(path)  # URL or local directory used as data storage
        if urllib.parse.urlparse(str(path)).scheme in ('http', 'https',):  # Check if data is local path or URL
            print(f"Download from: {path}")
            data_file = download_file_to_tempdir(path)
        else:
            data_file = path  # local data
        try:
            with gzip.open(data_file, 'r') as input_file:
                data = json.loads(input_file.read().decode('utf-8'))
        except:
            raise Exception("Could not read db file {}. File might be not existing or corrupt.".format(data_file))

        cnt = 0
        for tree_dict in data:  # add each single tree
            self.add_tree(tree_dict)  # add tree
            cnt += 1

        # Save zipped db file  and synchronize with MongoDB
        self.save(self.dbfile, sync=True)
        return cnt

    def mongodb_create_indexes(self):
        # print("Create MongoDB indexes.")
        # Create indices on fields
        try:
            for idx in INDEX_FIELDS:
                resp = self.mongodb_col.create_index(idx)
            for idx in INDEX_UNIQUE_FIELDS:
                resp = self.mongodb_col.create_index(idx, unique=True)
            for idx in INDEX_GEOM_SPHERE_FIELDS:
                resp = self.mongodb_col.create_index([idx])
        except:
            print(f"Could not create index: {idx} defined in db_conf.py")

    def mongodb_drop_indexes(self):
        # print("Dropping all MongoDB indexes.")
        self.mongodb_col.drop_indexes()  # drop all existing indices

    def mongodb_synchronize(self, clear=True):
        # Bulk import into Mongodb
        if clear is True:  # empty collection first
            self.mongodb_clear_col()
        # deepcopy avoids that MongoDB object ["_id"] id is written into local dictionary
        result = self.mongodb_col.insert_many(copy.deepcopy(self.db))
        return result

    def mongodb_clear_col(self):
        # print("Clear MongoDB collection.")
        self.mongodb_col.delete_many({})  # clear collection

    def add_tree(self, tree):
        """Add single tree object from dict"""
        tree_dict = tree.copy()
        # Add meta data 
        tree_dict['_id_x'] = len(self.db)  # store id (increment) for faster operations on result sets
        tree_dict['_date'] = datetime.datetime.now().isoformat()  # Get insertion date
        self.db.append(tree_dict)  # add to list

    def add_tree_file(self, filenamepath):
        """Add single tree object from JSON file to db and add meta info"""
        # Validate input file first
        if self.validate_json(filenamepath) is False:
            print(f"File '{filenamepath}' is not a valid format for pydtreedb. See template in treedb_format.py")
            return
        # Add data
        f_json = open(filenamepath)  # open input file
        json_string = json.loads(f_json.read())
        tree_dict = json_string.copy()
        tree_dict['_file'] = Path(filenamepath).name
        self.add_tree(tree_dict)
        f_json.close()  # close input file

    def get_db_file(self):
        """Returns name/path to local file of DB"""
        return self.dbfile

    def del_db_file(self):
        """Delete associated local db file"""
        return os.remove(self.dbfile)

    def get_stats(self):
        self.stats["n_trees"] = len(self.db)
        self.stats["n_species"] = len(self.get_list_species())
        return self.stats

    def get_list_species(self):
        """Returns list of unique names of species stored in DB"""
        res = self.mongodb_col.distinct("properties.species")
        return list(res)

    def get_shared_properties(self):  # this is currently not done in DB, but sequentially on list(dict).
        """Returns all object.properties that are shared among all objects"""
        try:
            setlist = [set(self.db[i]['properties'].keys()) for i in range(0, len(self.db))]
            return sorted(list(set.intersection(*setlist)))
        except Exception as ex:
            return []

    def query(self, *args, **kwargs):
        """
        General MongDB query forwarding: Returns trees (list of dict) fulfilling the arguments.
            Returns list of dict (=trees)
          - Example: filter = {"properties.species": "Abies alba"}   
          - Query ops: https://docs.mongodb.com/manual/reference/operator/query/ 
          - e.g. AND: https://docs.mongodb.com/manual/reference/operator/query/and/#mongodb-query-op.-and
        """
        try:
            res = self.mongodb_col.find(*args, **kwargs)
            return [e for e in res]
        except Exception as ex:
            print(ex)
            return []

    def query_by_key_value(self, key, value, regex=True):
        """
        Returns trees (list) fulfilling the regex or exact matching of value for a given key
        (including nested path of key).
        Keys must written exactly the same, e.g. key = properties.species, value="Quercus *", regex=True
        """
        if regex is True:
            res = self.mongodb_col.find({key: {"$regex": value}}, {'_id': False})
        else:
            res = self.mongodb_col.find({key: value}, {'_id': False})
        return [e for e in res]

    def query_by_key_exists(self, key):
        """Returns trees(list) having a given key(string) defined as dict (no matter which value)"""
        res = self.mongodb_col.find({key: {'$exists': 1}}, {'_id': False})
        return [e for e in res]

    def query_by_numeric_comparison(self, key, value, comp_op):
        """Returns trees (list) fulfilling the numeric comparison of values for given key"""
        raise Exception("Can be done with self.query()")

    def query_by_species(self, regex):
        """Returns trees(list) fulfilling the regex matching on the species name"""
        res = self.mongodb_col.find({QUERY_SPECIES_FIELDNAME: {"$regex": regex}}, {'_id': False})
        return [e for e in res]

    def query_by_date(self, key, start, end=False):
        """
        Returns trees(list) fulfilling the date of key lies between start and end date in format 'YYYY-MM-DD'
        If no end date is given, the current day is taken.
        Examples:   
            - query_by_date(key="properties.measurements.date", start="2019-08-28", end='2022-01-01')
            - query_by_date(key="properties.data.date", start="2019-08-28")
        """
        try:
            startdate = datetime.datetime.strptime(start, '%Y-%m-%d').isoformat()
            if end is False:
                enddate = datetime.datetime.now().isoformat()  # take today
            else:
                enddate = datetime.datetime.strptime(end, '%Y-%m-%d').isoformat()
        except:
            raise Exception("Date format is required as string 'YYYY-MM-DD' ")

        res = self.mongodb_col.find({key: {"$gte": startdate, "$lte": enddate}}, {'_id': False})
        return [e for e in res]

    def query_by_geometry(self, geom, distance=0.0):
        """Returns list of trees(dict) that are within a defined distance (in meters) from search geometry which is
        provided as GEOJSON dictionary or string; Geometry types Point and Polygon are supported, for example:

        {"type": "Point", "coordinates": (0.0, 0.0)}
     
        { "type": "Polygon",
        "coordinates": [[[8.700980940620983, 49.012725603975355],
                         [8.700972890122355, 49.011695140150906],
                         [8.70235623413669, 49.01167501390433],
                         [8.702310614644462, 49.012713528227415],
                         [8.702310614644462, 49.012713528227415],
                         [8.700980940620983, 49.012725603975355]]]}
      
    - Online help for geometries in MongoDB: 
        - https://docs.mongodb.com/manual/geospatial-queries/
        - https://pymongo.readthedocs.io/en/stable/examples/geo.html  
    """
        try:
            if isinstance(geom, str):
                geom = json.loads(geom)
        except:
            raise Exception(f"Could not convert search geometry to dictionary. Correct geojson?\n{geom}")

        if geom["type"] == "Point":
            spatial_query = {QUERY_GEOMETRY: {"$nearSphere": {"$geometry": geom, "$maxDistance": distance}}}
        elif geom["type"] == "Polygon":
            spatial_query = {QUERY_GEOMETRY: {"$geoWithin": {"$geometry": geom}}}

        # Run query on spatial index
        res = self.mongodb_col.find(spatial_query, {'_id': False})

        return [e for e in res]

    def get_ids(self, trees) -> list:
        """Returns ids(list) of trees(list)"""
        try:
            return [k['_id_x'] for k in trees]
        except:
            if not isinstance(trees, list):
                print(
                    f"Input for function {sys._getframe().f_code.co_name}() must be a list. "
                    f"Given wrong type: {type(trees)}.) ")
            else:
                print(f"Could not get id for: {trees}")
            return None
            # TODO: return [] ?

    def to_list(self):
        """Returns list of all tree objects(dict)"""
        return self.db

    def get_tree_as_json(self, tree, indent=4, metadata=False):
        """Returns original JSON(str) file content for a single tree(dict)"""
        tree_export = copy.copy(tree)
        if metadata is False:  # remove metadata
            # Remove all keys with leading "_": could also be done in loop but might be slower. hardcode for the minute.
            del tree_export["_file"]
            del tree_export["_date"]
            del tree_export["_id_x"]
        return json.dumps(tree_export, indent=indent)

    def validate_json(self, json_file):
        """
        Checks if JSON is valid and compatible for import into pytreedb.
        Only mandatory fields and main structure are checked
        """
        keys_template = list(flatten_json(json.loads(TEMPLATE_GEOJSON)).keys())
        keys_json = list(flatten_json(json.loads(open(json_file, 'r').read())).keys())
        fnd = 0
        for k in keys_template:
            if k in keys_json:
                fnd += 1
            else:
                print(k)
        if len(keys_template) == fnd:
            return True  # valid
        return False  # not valid

    def export_data(self, outdir, trees: list = []):
        """
        Reverse of import_data():
        Creates single geojson files for each tree in DB and puts it in local directory
        Optionally list of ids of trees to be exported can be provided. [] means that all will be exported
        returns list of file paths written
        """
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        files_written = []
        for tree in self:
            if trees == [] or tree['_id_x'] in trees:
                json_content = self.get_tree_as_json(tree)
                json_filename = os.path.join(outdir, tree['_file'])
                with open(json_filename, 'w') as json_filept:
                    json_filept.write(json_content)
                files_written.append(Path(json_filename))
        return files_written

    def convert_to_csv(self, outdir, trees=[]):
        """Exports trees to local csv files. Each export creates two separate csv files, 
        one for general imformations, one for metrics.
        Optionally list of ids of trees to be exported can be provided. [] means that all will be exported
        returns list of file paths written
        """
        csv_metrics = []
        metrics_header = ["tree_id"]
        csv_general = [["tree_id", "species", "lat_epsg4326", "long_epsg4326",
                        "elev_epsg4326", "x_epsg25832", "y_epsg25832", "z_epsg25832"]]

        for tree in self:
            if trees == [] or tree['_id_x'] in trees:

                # writing "general" table: species, lat, long, elev
                general_line = [tree["properties"]["id"],
                                tree["properties"]["species"],
                                tree["geometry"]["coordinates"][1],
                                tree["geometry"]["coordinates"][0],
                                tree["geometry"]["coordinates"][2]]

                # writing "metrics" table: metrics in columns, one row per data source
                for entry in tree["properties"]["measurements"]:
                    keys = entry.keys()
                    if "position_xyz" in keys:
                        general_line.append(entry["position_xyz"][0])
                        general_line.append(entry["position_xyz"][1])
                        general_line.append(entry["position_xyz"][2])
                    else:
                        metrics_line = [tree["properties"]["id"]]
                        for key in keys:
                            if key not in metrics_header:
                                metrics_header.append(key)
                        for i in range(1, len(metrics_header)):
                            if metrics_header[i] in keys:
                                metrics_line.append(entry[metrics_header[i]])
                            else:
                                metrics_line.append("")
                    csv_metrics.append(metrics_line)

                csv_general.append(general_line)
        csv_metrics.insert(0, metrics_header)

        # save locally
        def save(filename, content):
            with open(str(outdir) + filename, 'w', newline='') as file:
                csv_writer = csv.writer(file, delimiter=',')
                for line in content:
                    csv_writer.writerow(line)
        save('/result_general.csv', csv_general)
        save('/result_metrics.csv', csv_metrics)


if __name__ == "__main__":
    print("pyTreeDB (version {}), (c) 3DGeo Research Group, Heidelberg University (2022+)".format(__version__))
