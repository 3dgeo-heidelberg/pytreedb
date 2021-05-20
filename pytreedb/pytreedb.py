from pytreedb.__init__ import __version__
import json
import glob
import os
import datetime
import shapely.geometry
import urllib
import urllib.request
import _pickle as cpickle
import numpy
import collections
from pathlib import Path
from operator import lt, le, eq, ne, ge, gt  # operator objects

# import own sub-modules
from pytreedb.treedb_ufuncs import *
from pytreedb.treedb_format import *

""" 
---------------------
OPEN ISSUES
---------------------
GENERAL / DB-BACKEND:
    - REST server: start, stop, monitoring; @API functions 
    - Write TESTS / test class: https://realpython.com/python-testing/
    
- IMPORT
    - Import from other DB via REST interface and optionally also download and re-link all linked data sources [idea from Fabian 22.07.2020]

- QUERIES
    - ?

DB EXPORTS
    - Export as geojson
    - Export as Numpy array
    - Export as Shapefile with flattened attributes: see flatten_json code
    - Export for R
    - Export for potree
    - Export as input for HELIOS: XML => Select data source (i.e. point cloud)

WEBPAGE:
    - Webpage providing (2D/3D) visualization and search capabilities based on OpenAPI of pytreedb
    - Download option of selected trees (including linked data) as ZIP file: do it via Web Service (?)

PYPI PACKAGE
    - Check PEP-8:  https://legacy.python.org/dev/peps/pep-0008/ ; e.g. => underscore in variables
    - Doxygen / auto docs generation
    - Prepare folder/file structure for pypi: see ORS as example
    - Create package and test upload
    - Documentation for pypi
 
"""


class PyTreeDB:
    def __init__(self, dbfile = None):
        if __name__ == "__main__":
            print("pyTreeDB (version {}), (c) 3DGeo Research Group, Heidelberg University (2020+)".format(__version__))
        self.dbfile = None  # pickle file holding the entire database
        self.db = None  # dictionary central db file
        self.data = None  # path do input data imported with import
        self.host = None
        self.port = None
        self.service = None
        self.stats = {"n_trees": None,
                      "n_species": None}  # dictionary holding summary statistics about database (default variables are defined here)
        self.i = 0  # needed for iterator
        
        if dbfile is not None:
            # Check if dbfile is a valid path, if not, query users if an empty file shall be created
            if not os.path.exists(dbfile):
                if query_yes_no("The given path of dbfile <%s> does not exist. Create an empty file now?" % dbfile):
                    print("Note that you might want to import data into this empty .db file.")
                    # Create the directory first if the dir does not exist
                    if not os.path.exists(os.path.dirname(dbfile)):
                        os.makedirs(os.path.dirname(dbfile))
                    open(dbfile, 'w').close() # Create empty file
                    self.dbfile = dbfile; # Set number variable
                else:
                    raise Exception("No such file or directory: %s" % self.dbfile)
            else:
                self.load_db(dbfile)

    def __getitem__(self, item):
        """Allow index(int) subscription on the database, list(int) and slicing access with int"""
        if isinstance(item, int):
            """Returns single tree(dict)"""
            return self.db[item]
        elif isinstance(item, list) or isinstance(item, numpy.ndarray):
            """Returns a list of selected trees(dict)"""
            return list(self.db[key] for key in item)
        elif isinstance(item, slice):
            """Returns list of slicing selected trees(dict) """
            idx_array = numpy.array(list(self.db.keys()))
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

    def load_db(self, dbfile):
        """Loads existing database file from pickle"""
        try:
            self.db = cpickle.load(open(dbfile, "rb"))
        except:
            raise Exception("Could not read db file %s" % (dbfile))

    def import_data(self, path, overwrite=False):
        """Read data from local file or from ZIP file provided as URL with filename like *.*json"""
        if self.db is None or overwrite is True:
            self.db = collections.OrderedDict()  # indexed.IndexedOrderedDict()  #https://pypi.org/project/indexed/
        self.data = path  # URL or local directory used as data storage
        # Check if data is local path or URL
        if urllib.parse.urlparse(path).scheme in ('http', 'https',):
            print("Download and use data from: {}".format(path))
            data_dir = download_extract_zip_tempdir(path)
            print("Downloading to local temp: ", data_dir)
        else:
            # local data
            data_dir = path
        for f in Path(data_dir).rglob('*.*json'):
            try:
                self.add_tree_file(f)
            except Exception as err:
                print("Input file <%s> cannot be read and is ignored. %s" % (f, err))

        "#Store db as pickle"
        cpickle.dump(self.db, open(self.dbfile, "wb"))

    def import_db(self, path, overwrite=False):
        """Import other database via pytreedb REST interface and optionally also download all files and re-link to new location"""
        raise Exception("Not implemented yet.")

    def add_tree_file(self, filenamepath):
        """Add single tree object from JSON file to db and add meta info"""

        # Validate input file first
        if self.validate_json(filenamepath) is False:
            print("File '%s' is not a valid format for pydtreedb. See template in treedb_format.py" % filenamepath)
            return

        f_json = open(filenamepath)
        json_string = json.loads(f_json.read())
        tree_dict = json_string.copy()
        # Get id for new tree as autoincrement
        new_idx = self.get_new_index()
        self.db[new_idx] = tree_dict
        # Add additional columns used for db handling and quick searching
        tree_dict['id'] = new_idx  # Store object ID additionally also in object
        tree_dict['_date'] = datetime.datetime.now().isoformat()  # Get insertion date
        tree_dict['_file'] = Path(filenamepath).name  # Get filename
        tree_dict['_geometry'] = shapely.geometry.shape(
            json_string['geometry'])  # Generate Shapely geometry object of position
        tree_dict['_json'] = json.dumps(json_string)  # Store original input json string
        tree_dict['_file_hash'] = hash_file(filenamepath)
        f_json.close()

    def get_new_index(self):
        """Get auto-increment new key for tree object"""
        if self.db is None:
            return 0
        elif len(self.db) > 0:
            return max(self.db.keys()) + 1
        else:
            return 0

    def get_db_file(self):
        """Returns name/path to pickle file of DB"""
        return self.dbfile

    def del_db_file(self):
        """Delete associated pickle db file"""
        return os.remove(self.dbfile)

    def get_stats(self):
        self.stats["n_trees"] = len(self.db)
        self.stats["n_species"] = len(self.get_list_species())
        return self.stats

    def get_list_species(self):
        """Returns list of unique names of species stored in DB"""
        return list(set(gen_dict_extract('species', self.db)))

    def get_shared_properties(self):
        """Returns all object.properties that are shared among all objects"""
        try:
            setlist = [set(self.db[i]['properties'].keys()) for i in range(0, len(self.db))]
            return sorted(list(set.intersection(*setlist)))
        except Exception as ex:
            return []

    def query(self, key, value, regex=True):
        """ Returns trees (list) fulfilling the regex or exact matching of value for a given key. Keys must written exactly the same."""
        try:
            if regex is True:
                idx = [i for i in self.db if len(list(gen_dict_extract_regex(key, self.db[i], value)))]
            else:
                idx = [i for i in self.db if len(list(gen_dict_extract_exact(key, self.db[i], value)))]
            #returning input json for now because of error "Object of type Point is not JSON serializable"; might need to implement custom serialization
            return list(json.loads(self.db[key]["_json"]) for key in idx)
        except Exception as ex:
            print(ex)
            return []

    def query_by_numeric_comparison(self, key, value, comp_op):
        """ Returns trees (list) fulfilling the numeric comparison of values for given key"""
        if comp_op not in [lt, le, eq, ne, ge, gt]:
            raise Exception("Operator must be one of the module operator: lt, le, eq, ne, ge, gt")
        else:
            idx = [i for i in self.db if len(list(gen_dict_extract_numeric_comp(key, self.db[i], value, comp_op)))]
            return list(self.db[key] for key in idx)

    def query_by_key_exists(self, key):
        """ Returns trees(list) having a given key (no matter which value)"""
        idx = [i for i in self.db if len(list(gen_dict_extract(key, self.db[i])))]
        return list(self.db[key] for key in idx)

    def query_by_species(self, value):
        """Returns trees(list) fulfilling the regex matching on the species name"""
        return self.query('species', value)

    def query_by_geometry(self, geom, distance=0.0):
        """Returns list of trees(dict) that are within a defined distance (in map units of the coordinates - watch out for latlon) from search geometry which is provided as geojson dictionary or string
            e.g. {"type": "Point", "coordinates": (0.0, 0.0)}
        """
        try:
            if isinstance(geom, str):
                geom = json.loads(geom)
            search_geometry = shapely.geometry.shape(geom)
        except Exception as err:
            print("Provided search geometry could not be parsed: %s" % err)
            return []

        return [tree for tree in self if tree['_geometry'].distance(search_geometry) <= distance]

    def query_by_date(self, key, value, comp_op):
        """Returns trees(list) fulfilling the date comparison on a key which contains a date ('YYYY-MM-DD')"""
        try:
            _date_parts = value.split("-")
            _date = datetime.date(int(_date_parts[0]), int(_date_parts[1]), int(_date_parts[2]))
        except:
            raise Exception("Date format is required as string 'YYYY-MM-DD' ")

        if comp_op not in [lt, le, eq, ne, ge, gt]:
            raise Exception("Operator must be one of the module operator: lt, le, eq, ne, ge, gt")
        else:
            idx = [i for i in self.db if len(list(gen_dict_extract_date_comp(key, self.db[i], _date, comp_op)))]
            return list(self.db[key] for key in idx)

    def join(self, results, operator='and'):
        """Returns list of tree ids: Method to join list of resulting lists of trees(dict) using their 'id' by applying a logical operator on those sets"""
        implemented_ops = ['and', 'or']
        if operator not in implemented_ops:
            raise Exception("Supported operators are: %s" % (str(implemented_ops)))
        if len(results) < 2:
            raise Exception("Provide 2 or more resulting lists.")
        if operator == 'and':
            return list(set.intersection(*[set(self.get_ids(x)) for x in results]))
        elif operator == 'or':
            results_sets = [set(self.get_ids(i)) for i in results]
            print(results_sets)
            return list(set.union(*results_sets))  # unique ids

    def get_ids(self, trees):
        """Returns ids(list) of trees(list)"""
        if not isinstance(trees, list):
            # in case only single tree is provided
            trees = [trees]
        if len(trees) >= 1:
            return [k['properties']['id'] for k in trees]
        else:
            return []

    def to_list(self):
        """Returns list of all tree objects(dict)"""
        return [self.db[k] for k in self.db.keys()]

    def get_tree_as_json(self, tree):
        """Returns original JSON(str) file content for a single tree(dict)"""
        return tree['_json']

    def validate_json(self, json_file):
        """Checks if JSON is valid and compatible for import into pytreedb. Only mandatory fields and main structure are checked"""
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

    def print_db_html(self, outfile):
        # flatten_json
        # self.df.to_html(outfile)
        raise Exception("Not implemented yes.")

    def update(self):
        # store git checksum on zip file of git / or date of file
        # check whether it has changed => run fresh read
        raise Exception("Not implemented yes.")

    def export_data(self, outdir, trees=[]):
        """Reverse of import_data(): Creates single geojson files for each tree in DB and puts it in local directory
            Optionally list of ids of trees to be exported can be provided. [] means that all will be exported"""
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        for tree in self:
            if trees == [] or tree['id'] in trees:
                json_content = tree['_json']
                json_filename = os.path.join(outdir, tree['_file'])
                json_filept = open(json_filename, 'w')
                json_filept.write(json_content)
                json_filept.close()
                print(json_filename)

    def export_as_numpy(self):
        """Export database as numpy array"""
        raise Exception("Not implemented yes.")

    def start_server(self, host="127.0.0.1", port=5000):
        self.host = host
        self.port = port
        raise Exception("Not implemented yet.")
        """
        from fastapi import FastAPI
        import uvicorn
        
        app = FastAPI()
       
        @app.get("/")
        async def root():
            return {"message": "Hello World"}

        #print ("http://127.0.0.1:5000/")
        #print ("http://127.0.0.1:5000/openapi.json")
        self.service = uvicorn.run("main:app", host="127.0.0.1", port=5000, log_level="info")    
        """

    def stop_server(self):
        raise Exception("Not implemented yes.")

    def test(self):
        """Test routines to check all functions of the class"""
        raise Exception("Not implemented yes.")


if __name__ == "__main__":
    pass
