import copy
import datetime
import gzip
import json
import os
import sys
import urllib
import urllib.request
from pathlib import Path
from typing import Union, List

import numpy as np
import pymongo
from dotenv import dotenv_values  # .env  for DB credentials

# import config values
from pytreedb.db_conf import (
    TEMPLATE_GEOJSON,
    INDEX_FIELDS,
    INDEX_UNIQUE_FIELDS,
    INDEX_GEOM_SPHERE_FIELDS,
    QUERY_SPECIES_FIELDNAME,
    QUERY_GEOMETRY,
)

# import own sub-modules
from pytreedb.db_utils import (
    flatten_json,
    download_extract_zip_tempdir,
    download_file_to_tempdir,
    write_list_to_csv,
)
from .__init__ import __version__
from ._types import PathLike, JSONString, DateString, URL


class PyTreeDB:
    """This class is the starting point and the core component of pytreedb

    :ivar PathLike dbfile: local file holding self.db
    :ivar dict mongodb: dict holding mongodb connection infos
    :ivar list db: list of dictionaries (single dicts equal json files)
    :ivar str data: path to input data imported with import (path of last import)
    :ivar dict stats: dictionary holding summary statistics about database
    :ivar int i: needed for iterator

    """

    def __init__(self, dbfile: PathLike, mongodb: dict = None):
        """This function initializes a class object

        :param PathLike dbfile: local file holding self.db
        :param dict mongodb: dictionary holding mongodb connection infos

        """

        if mongodb is None:
            try:
                config = dotenv_values(os.path.join(os.getcwd(), ".env"))
                mongodb = {
                    "uri": config["CONN_URI"],
                    "db": config["CONN_DB"],
                    "col": config["CONN_COL"],
                }
            except:
                print(
                    "Could not find or load expected .env file in current working directory. "
                    "Consider changing working directory before initiating class."
                )
                # raise
                sys.exit()
        self.dbfile = dbfile  # local file holding self.db
        self.mongodb = mongodb  # dict holding mongodb connection infos
        self.db = list()  # data container  -> list of dictionaries (single dicts equal json files)
        self.data = None  # path to input data imported with import (path of last import)
        self.stats = {
            "n_trees": None,
            "n_species": None,
        }  # dictionary holding summary statistics about database
        self.i = 0  # needed for iterator

        try:
            # Connect MongoDB
            self.mongodb_client = pymongo.MongoClient(self.mongodb["uri"])  # Check MongoDB connection
            # Check if collection exists.
            if not self.mongodb["col"] in self.mongodb_client[self.mongodb["db"]].list_collection_names():
                print(f"Collection: {self.mongodb['col']} created.")
                # Connect and create connection if not yet there.
            # MongoDB collection to be queried
            self.mongodb_col = self.mongodb_client[self.mongodb["db"]][self.mongodb["col"]]
            # Create indices in MongoDB
            self.mongodb_create_indexes()
        except:
            print(f"Could not connect to MongoDB server or establishing sync/indices/etc. to MongoDB: {self.mongodb}.")
            # raise
            sys.exit()

    def __getitem__(self, item: Union[int, list, slice, np.ndarray]) -> Union[dict, List[dict]]:
        """
        Allow index(int) subscription on the database, list(int) and slicing access with int

        :param item: Tree index or list/array/slice of tree indices
        :type item: int or list or slice or np.ndarray
        :return: tree or list of trees (tree dictionaries)
        :rtype dict or list[dict]

        """
        if isinstance(item, int):
            """Returns single tree(dict)"""
            return self.db[item]
        elif isinstance(item, list) or isinstance(item, np.ndarray):
            """Returns a list of selected trees(dict)"""
            return list(self.db[key] for key in item)

        elif isinstance(item, slice):
            """Returns list of slicing selected trees(dict)"""
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
            "Copying of PyTreeDb object is not yet safe. Lifehack: Make a new database and import the other db."
        )

    def save(self, dbfile: PathLike = None, sync: bool = False):
        """
        Saves database to compressed serialized version as local file.

        :param dbfile: local file path, where the database should be saved
        :param bool sync: synchronize MongoDB immediately after saving (clears MongoDB first)

        """
        if dbfile is None:
            dbfile = self.dbfile  # if no filename is given as arg - just overwrite existing file in self.dbfile
        try:
            with gzip.open(dbfile, "w") as output_file:
                output_file.write(json.dumps(self.db).encode("utf-8"))
            if sync is True:
                upload_result = self.mongodb_synchronize(clear=True)
                print(f"{len(upload_result.inserted_ids)} trees synchronized with MongoDB server.")
        except:
            raise Exception(f"Could not write db file {dbfile}. Path or permissions might be missing.")

    def load(self, dbfile: PathLike, sync: bool = True):
        """Loads existing compressed serialized version of database.

        :param str dbfile: data base file which should be loaded
        :param bool sync: synchronize MongoDB immediately after loading (clears MongoDB first)

        """
        try:
            with gzip.open(dbfile, "r") as input_file:
                self.db = json.loads(input_file.read().decode("utf-8"))
            if sync is True:
                upload_result = self.mongodb_synchronize(clear=True)
                print(f"{len(upload_result.inserted_ids)} trees synchronized with MongoDB server.")
        except:
            raise Exception(f"Could not read db file {dbfile}. File might be corrupt.")

    def clear(self):
        """Clear database and MongoDB. Start with empty data and MongoDB. Does not empty local db file."""
        self.__init__(self.dbfile, self.mongodb)
        self.mongodb_clear_col()

    def import_data(self, path: Union[PathLike, URL], overwrite: bool = False):
        r"""
        Read data (json files) from local file or from URL of ZIP archive with files named like \*.\*json.

        :param str path: path to input folder or URL of ZIP archive
        :param bool overwrite: Overwrite current data in database (clears database and then adds data)
        :raises FileNotFoundError: in case file is not found
        :raises Exception: in case the input file cannot be read
        :return: Number of trees added to database
        :rtype: int

        """
        if overwrite is True:
            self.clear()  # empty db

        self.data = Path(path)  # URL or local directory used as data storage
        if urllib.parse.urlparse(str(path)).scheme in (
            "http",
            "https",
        ):  # Check if data is local path or URL
            print(f"Download from: {path}")
            data_dir = download_extract_zip_tempdir(path)
        else:
            data_dir = path  # local data
            if not Path(data_dir).exists():
                raise FileNotFoundError(f"Directory <{data_dir}> does not exist.")
        cnt = 0
        for f in sorted(Path(data_dir).rglob("*.*json")):
            try:
                self.add_tree_file(f)
                cnt += 1
            except Exception as err:
                print(f"Input file <{f}> cannot be read and is ignored. {err}")

        # Save zipped db file  and synchronize with MongoDB
        self.save(self.dbfile, sync=True)
        return cnt

    def import_db(self, path: PathLike, overwrite: bool = False) -> int:
        """
        Read data from local db file or from URL. Returns number of trees added

        :param PathLike path: local database file or URL
        :param bool overwrite: Overwrite current data in database (clears database and then adds data)
        :return: Number of trees added to database
        :rtype: int

        """
        if overwrite is True:
            self.clear()  # empty db

        self.data = Path(path)  # URL or local directory used as data storage
        if urllib.parse.urlparse(str(path)).scheme in (
            "http",
            "https",
        ):  # Check if data is local path or URL
            print(f"Download from: {path}")
            data_file = download_file_to_tempdir(path)
        else:
            data_file = path  # local data
            if not Path(data_file).exists():
                raise FileNotFoundError(f"File <{data_file}> does not exist.")
        try:
            with gzip.open(data_file, "r") as input_file:
                data = json.loads(input_file.read().decode("utf-8"))
        except:
            raise Exception(f"Could not read db file {data_file}. File might be not existing or corrupt.")

        cnt = 0
        for tree_dict in data:  # add each single tree
            self.add_tree(tree_dict)  # add tree
            cnt += 1

        # Save zipped db file  and synchronize with MongoDB
        self.save(self.dbfile, sync=True)
        return cnt

    def mongodb_create_indexes(self):
        """Create indices on fields"""
        try:
            for idx in INDEX_FIELDS:
                # TODO: Local variable "resp" not used, call function without "resp = "?
                self.mongodb_col.create_index(idx)
            for idx in INDEX_UNIQUE_FIELDS:
                self.mongodb_col.create_index(idx, unique=True)
            for idx in INDEX_GEOM_SPHERE_FIELDS:
                self.mongodb_col.create_index([idx])
        except:
            print(f"Could not create index: {idx} defined in db_conf.py")

    def mongodb_drop_indexes(self):
        """Drop all existing indices"""
        self.mongodb_col.drop_indexes()

    def mongodb_synchronize(self, clear: bool = True):  # todo: add type for return
        """
        Bulk import into MongoDB
        :param bool clear: Clear MongoDB collection first
        :return: #todo

        """
        # Bulk import into Mongodb
        if clear is True:  # empty collection first
            self.mongodb_clear_col()
        # deepcopy avoids that MongoDB object ["_id"] id is written into local dictionary
        result = self.mongodb_col.insert_many(copy.deepcopy(self.db))
        return result

    def mongodb_clear_col(self):
        """Clear MongoDB collection"""
        self.mongodb_col.delete_many({})  # clear collection

    def add_tree(self, tree: dict):
        """
        Add single tree object from dict

        :param dict tree: tree dictionary

        """
        tree_dict = tree.copy()
        # Add meta data
        tree_dict["_id_x"] = len(self.db)  # store id (increment) for faster operations on result sets
        tree_dict["_date"] = datetime.datetime.now().isoformat()  # Get insertion date
        self.db.append(tree_dict)  # add to list

    def add_tree_file(self, filenamepath: PathLike):
        """
        Add single tree object from JSON file to db and add meta info

        :param filenamepath: path to JSON file
        :raises ValueError: if the content of the JSON file is not in the right format for pytreedb.

        """
        # Validate input file first
        if self.validate_json(filenamepath) is False:
            raise ValueError(f"File '{filenamepath}' is not a valid format for pytreedb." f"See template in db_conf.py")
        # Add data
        with open(filenamepath, "r") as f_json:
            json_string = json.loads(f_json.read())
            tree_dict = json_string.copy()
            tree_dict["_file"] = Path(filenamepath).name
        self.add_tree(tree_dict)

    def get_db_file(self):
        """Return name/path to local file of DB"""
        return self.dbfile

    def del_db_file(self):
        """Delete associated local db file"""
        return os.remove(self.dbfile)

    def get_stats(self) -> dict:
        """return basic database statistics: number of trees and number of species

        :return: dictionary holding the database statistics
        :rtype: dict

        """
        self.stats["n_trees"] = len(self.db)
        self.stats["n_species"] = len(self.get_list_species())
        return self.stats

    def get_list_species(self) -> List[str]:
        """
        Get list of unique names of species stored in DB

        :return: List of tree species
        :rtype: list[str]

        """
        res = self.mongodb_col.distinct("properties.species")
        return list(res)

    def get_shared_properties(
        self,
    ) -> List[str]:  # this is currently not done in DB, but sequentially on list(dict).
        """
        Returns all object.properties that are shared among all objects

        :return: list of shared properties
        :rtype: list[str]

        """
        try:
            setlist = [set(self.db[i]["properties"].keys()) for i in range(0, len(self.db))]
            return sorted(list(set.intersection(*setlist)))
        except Exception:
            return []

    def query(self, *args, **kwargs) -> List[dict]:
        """
        General MongDB query forwarding: Returns trees (list of dict) fulfilling the arguments.
        Returns list of dict (=trees)

        Example: ``filter = {"properties.species": "Abies alba"}``

        Query ops: https://docs.mongodb.com/manual/reference/operator/query/

        e.g. AND: https://docs.mongodb.com/manual/reference/operator/query/and/#mongodb-query-op.-and

        :return: list of trees (tree dictionaries) fulfilling the query
        :rtype: list[dict]

        """
        try:
            res = self.mongodb_col.find(*args, **kwargs)
            return [e for e in res]
        except Exception as ex:
            print(ex)
            return []

    def query_by_key_value(self, key: str, value: str, regex: bool = True):
        """
        Returns trees (list) fulfilling the regex or exact matching of value for a given key
        (including nested path of key).

        Keys must be written exactly the same, e.g. ``key=properties.species, value="Quercus *", regex=True``

        :param str key: Key in the dictionary to use in the query
        :param str value: Value that the key must have
        :param bool regex: whether the value is a regex or not
        :return: list of trees (tree dictionaries) fulfilling the query
        :rtype: list[dict]
        """
        if regex is True:
            res = self.mongodb_col.find({key: {"$regex": value}}, {"_id": False})
        else:
            res = self.mongodb_col.find({key: value}, {"_id": False})
        return [e for e in res]

    def query_by_key_exists(self, key: str) -> List[dict]:
        """
        Returns trees having a given key defined inside dict (no matter which value)

        :param str key: Key which has to exist in dictionary
        :return: list of trees (tree dictionaries) fulfilling the query
        :rtype: list[dict]
        """
        res = self.mongodb_col.find({key: {"$exists": 1}}, {"_id": False})
        return [e for e in res]

    def query_by_numeric_comparison(self, key: str, value: str, comp_op: str):
        """Returns trees (list) fulfilling the numeric comparison of values for given key"""
        raise Exception("Can be done with self.query()")  # todo: remove method?

    def query_by_species(self, regex: str) -> List[dict]:
        """
        Returns trees(list) fulfilling the regex matching on the species name

        :param str regex: regular expression for finding tree species
        :return: list of trees (tree dictionaries) fulfilling the query
        :rtype: list[dict]
        """
        res = self.mongodb_col.find({QUERY_SPECIES_FIELDNAME: {"$regex": regex}}, {"_id": False})
        return [e for e in res]

    def query_by_date(self, key: str, start: DateString, end: DateString = None) -> List[dict]:
        """
        Returns trees(list) fulfilling the date of key lies between start and end date in format 'YYYY-MM-DD'
        If no end date is given, the current day is taken.

        Examples::

            query_by_date(key="properties.measurements.date", start="2019-08-28", end='2022-01-01')

            query_by_date(key="properties.data.date", start="2019-08-28")

        :param str key:
        :param DateString start: String representation ('YYYY-MM-DD') of the start date
        :param DateString end: String representation ('YYYY-MM-DD') of the end date
        :return: List of trees (tree dictionaries) fulfilling the query
        :rtype: list[dict]

        """
        try:
            startdate = datetime.datetime.strptime(start, "%Y-%m-%d").isoformat()
            if end is None:
                enddate = datetime.datetime.now().isoformat()  # take today
            else:
                enddate = datetime.datetime.strptime(end, "%Y-%m-%d").isoformat()
        except:
            raise Exception("Date format is required as string 'YYYY-MM-DD' ")

        res = self.mongodb_col.find({key: {"$gte": startdate, "$lte": enddate}}, {"_id": False})
        return [e for e in res]

    def query_by_geometry(self, geom: Union[JSONString, dict], distance: float = 0.0) -> List[dict]:
        """
        Returns list of trees(dict) that are within a defined distance (in meters) from search geometry which is
        provided as GEOJSON dictionary or string; Geometry types Point and Polygon are supported, for example::

            {"type": "Point", "coordinates": [0.0, 0.0]}``

            { "type": "Polygon", "coordinates": [[[8.700980940620983, 49.012725603975355],
                         [8.700972890122355, 49.011695140150906],
                         [8.70235623413669, 49.01167501390433],
                         [8.702310614644462, 49.012713528227415],
                         [8.702310614644462, 49.012713528227415],
                         [8.700980940620983, 49.012725603975355]]]}

        Online help for geometries in MongoDB:
        - https://docs.mongodb.com/manual/geospatial-queries/
        - https://pymongo.readthedocs.io/en/stable/examples/geo.html

        :param geom: json string representing a geometry
        :type geom: str or dict
        :param float distance: distance from search geometry in meters
        :raises ValueError: if the search geometry cannot be converted to a dictionary
        :return: list of trees (tree dictionaries) fulfilling the query
        :rtype: list[dict]

        """
        try:
            if isinstance(geom, str):
                geom = json.loads(geom)
        except json.decoder.JSONDecodeError as e:
            raise ValueError(
                f"Could not convert search geometry to dictionary.\n"
                f"Check syntax of:\n{geom}\n"
                f"JSON Error message: {e}"
            )

        if geom["type"] == "Point":
            spatial_query = {QUERY_GEOMETRY: {"$nearSphere": {"$geometry": geom, "$maxDistance": distance}}}
        elif geom["type"] == "Polygon":
            spatial_query = {QUERY_GEOMETRY: {"$geoWithin": {"$geometry": geom}}}

        # Run query on spatial index
        res = self.mongodb_col.find(spatial_query, {"_id": False})

        return [e for e in res]

    def get_ids(self, trees: List[dict]) -> List[int]:
        """
        Returns ids of trees

        :param list[dict] trees: list of tree dictionaries
        :return: list with IDs of trees
        :rtype: list[int]

        """
        try:
            return [k["_id_x"] for k in trees]
        except:
            if not isinstance(trees, list):
                print(
                    f"Input for function {sys._getframe().f_code.co_name}() must be a list. "
                    f"Given wrong type: {type(trees)}.) "
                )
            else:
                print(f"Could not get id for: {trees}")
            return []

    def to_list(self):
        """Returns list of all tree objects(dict)"""
        return self.db

    @staticmethod
    def get_pointcloud_urls(trees: List[dict]) -> List[str]:
        """
        Returns a list of point clouds for the given trees

        :param list[dict] trees: list of tree dictionaries
        :raises TypeError: if the trees are not provided in a list
        :return: list with .laz point cloud files of trees
        :rtype: list[str]
        """
        try:
            return [obj["file"] for tree in trees for obj in tree["properties"]["data"]]
        except:
            if not isinstance(trees, list):
                raise TypeError(
                    f"Input for function {sys._getframe().f_code.co_name}() must be a list. "
                    f"Given wrong type: {type(trees)}.) "
                )
            else:
                print(f"Could not get url for: {trees}")
            return []

    @staticmethod
    def get_tree_as_json(tree: dict, indent: bool = 4, metadata: bool = False) -> JSONString:
        """
        Returns original JSON(str) file content for a single tree

        :param dict tree: Dictionary describing a single tree in the database
        :param int indent: pretty-print with that given indent level
        :param bool metadata: include metadata in output JSON
        :return: JSON string of the tree object
        :rtype: str

        """
        tree_export = copy.copy(tree)
        if metadata is False:  # remove metadata
            # Remove all keys with leading "_": could also be done in loop but might be slower. hardcode for the minute.
            del tree_export["_file"]
            del tree_export["_date"]
            del tree_export["_id_x"]
        return json.dumps(tree_export, indent=indent)

    @staticmethod
    def validate_json(json_file: PathLike):
        """
        Checks if JSON is valid and compatible for import into pytreedb.
        Only mandatory fields and main structure are checked

        :param json_file: path to json file
        :return: Content of JSON file is valid or not
        :rtype: bool

        """
        keys_template = list(flatten_json(json.loads(TEMPLATE_GEOJSON)).keys())
        keys_json = list(flatten_json(json.loads(open(json_file, "r").read())).keys())
        fnd = 0
        for k in keys_template:
            if k in keys_json:
                fnd += 1
            else:
                print(k)
        if len(keys_template) == fnd:
            return True  # valid
        return False  # not valid

    def export_data(self, outdir, trees: List[int] = None) -> List[PathLike]:
        """
        Reverse of import_data():
        Creates single geojson files for each tree in DB and puts it in local directory
        Optionally list of ids of trees to be exported can be provided. None (default) means that all will be exported

        :param PathLike outdir: Path to output directory
        :param list[int] trees: List of tree IDs
        :return: List of file paths that have been written
        :rtype: PathLike

        """
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        files_written = []
        for tree in self:
            if trees is None or tree["_id_x"] in trees:
                json_content = self.get_tree_as_json(tree)
                json_filename = os.path.join(outdir, tree["_file"])
                with open(json_filename, "w") as json_filept:
                    json_filept.write(json_content)
                files_written.append(Path(json_filename))
        return files_written

    def convert_to_csv(
        self,
        outdir: PathLike,
        trees: List[int] = None,
        filename_general: str = "result_general.csv",
        filename_metrics: str = "result_metrics.csv",
    ) -> List[PathLike]:
        """
        Exports trees to local csv files. Each export creates two separate csv files,
        one for general information (one row per tree), one for metrics (one row per source of measurements).
        Optionally list of ids of trees to be exported can be provided. None means that all will be exported
        returns list of file paths written

        :param PathLike outdir: Path to output directory
        :param list[int] trees: List of tree IDs
        :param PathLike filename_general: Name of the file in which general tree info are written
        :param PathLike filename_metrics: Name of the file in which specific tree metrics per measurement are written
        :return: List of file paths that have been written
        :rtype: list[PathLike]

        """
        outdir = Path(outdir)
        csv_metrics = []
        metrics_header = ["tree_id"]
        csv_general = []
        general_header = [
            "tree_id",
            "species",
            "lat_epsg4326",
            "long_epsg4326",
            "elev_epsg4326",
        ]
        if not trees:
            data = self.db
        else:
            data = self[trees]

        # get the unique keys of all "measurements" of each tree
        keys = set(
            [
                key
                for i in range(0, len(data))
                for j in range(len(data[i]["properties"]["measurements"]))
                for key in data[i]["properties"]["measurements"][j].keys()
            ]
        )

        # write the headers of the csv files
        if "position_xyz" in keys:
            general_header += ["x", "y", "z", "xyz_crs"]
            keys.remove("crs")
            keys.remove("position_xyz")
        metrics_header += list(keys)

        # get the values for the csv file
        for tree in data:
            general_line = [None] * len(general_header)
            general_line[:5] = [
                tree["properties"]["id"],
                tree["properties"]["species"],
                tree["geometry"]["coordinates"][1],
                tree["geometry"]["coordinates"][0],
                tree["geometry"]["coordinates"][2],
            ]
            for entry in tree["properties"]["measurements"]:
                keys = entry.keys()
                if "position_xyz" in keys:
                    crs = entry["crs"]
                    general_line[5] = entry["position_xyz"][0]
                    general_line[6] = entry["position_xyz"][1]
                    general_line[7] = entry["position_xyz"][2]
                    general_line[8] = crs
                if "source" in keys:
                    metrics_line = [None] * len(metrics_header)
                    metrics_line[0] = tree["properties"]["id"]
                    for i in range(1, len(metrics_header)):
                        if metrics_header[i] in keys:
                            metrics_line[i] = entry[metrics_header[i]]
                        else:
                            metrics_line[i] = None
                    csv_metrics.append(metrics_line)
            csv_general.append(general_line)

        # insert headers at beginning of the lists
        csv_general.insert(0, general_header)
        csv_metrics.insert(0, metrics_header)

        output_files = []
        if filename_general is not None:
            output_files.append(write_list_to_csv(outdir / filename_general, csv_general))
        if filename_metrics is not None:
            output_files.append(write_list_to_csv(outdir / filename_metrics, csv_metrics))
        return output_files


if __name__ == "__main__":
    print(f"pyTreeDB (version {__version__}), (c) 3DGeo Research Group, Heidelberg University (2022+)")
