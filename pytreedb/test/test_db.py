#!/usr/bin/env python
# -- coding: utf-8 --

import os
import pytest
import json
from pytreedb import db
from dotenv import load_dotenv
from pathlib import Path
import numpy as np
from numpy.lib.recfunctions import structured_to_unstructured
import pytreedb.db_utils
import zipfile

load_dotenv()
conn_uri = os.environ.get("CONN_URI")
conn_db = os.environ.get("CONN_DB")
conn_col = os.environ.get("CONN_COL")

root_path = str(Path(__file__).parent.parent.parent)


@pytest.fixture()
def mydb(tmp_path):
    """Fixture for a database instance (function-scope, used for imports and exports)"""
    my_dbfile = tmp_path / "temp.db"
    mydb = db.PyTreeDB(dbfile=my_dbfile, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col})
    return mydb


@pytest.fixture(scope="session")
def mydb_dbfile_local(tmp_path_factory):
    """Fixture for a database connection importing local db file with >1000 trees"""
    test_dir = tmp_path_factory.mktemp("test_db_local")
    my_dbfile = test_dir / "temp.db"
    test_dbfile = f"{root_path}/data/test/data.db"
    mydb = db.PyTreeDB(dbfile=my_dbfile, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col})
    mydb.import_db(test_dbfile, overwrite=True)
    return mydb


@pytest.fixture(scope="session")
def mydb_test_geojsons_local(tmp_path_factory):
    """Fixture for a database connection importing small local test set of geojson files"""
    test_dir = tmp_path_factory.mktemp("test_geojsons_local")
    my_dbfile = test_dir / "temp.db"
    test_geojsons = f"{root_path}/data/test/test_geojsons"
    mydb = db.PyTreeDB(dbfile=my_dbfile, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col + "_2"})
    mydb.import_data(test_geojsons, overwrite=True)
    return mydb


@pytest.mark.imports
@pytest.mark.parametrize(
    "data_path, n_trees_expected",
    [
        (
            "https://github.com/3dgeo-heidelberg/pytreedb/raw/main/data/test/geojsons.zip",
            1491,
        ),
        (f"{root_path}/data/test/test_geojsons", 6),
    ],
)
def test_import_data(mydb, data_path, n_trees_expected):
    """Test for reading data (json files) from local file or from URL of ZIP archive with files named like *.*json"""

    assert mydb.import_data(data_path) == n_trees_expected


@pytest.mark.imports
@pytest.mark.parametrize(
    "data_path, n_trees_expected",
    [
        (
            "https://github.com/3dgeo-heidelberg/pytreedb/raw/main/data/test/data.db",
            1491,
        ),
        (f"{root_path}/data/test/data.db", 1491),
    ],
)
def test_import_db(mydb, data_path, n_trees_expected):
    """Test for reading local database file or URL to database file"""

    assert mydb.import_db(data_path) == n_trees_expected


@pytest.mark.imports
def test_import_db_wrong_path(mydb):
    """Test if importing database from a corrupt local path raises Error"""
    # given
    my_corrupt_path = "corrupt/path/to/file.db"

    # Check if raises error
    with pytest.raises(FileNotFoundError) as e:
        mydb.import_db(my_corrupt_path)
    assert e.type is FileNotFoundError


@pytest.mark.imports
def test_import_db_wrong_url(mydb):
    """Test if importing data from a corrupt URL raises Error"""
    # given
    my_corrupt_url = "https://githubbb.com/3dgeo-heidelberg/pytreedb/raw/main/data/test/data.db"

    # Check if raises error
    with pytest.raises(ConnectionError) as e:
        mydb.import_db(my_corrupt_url)
    assert e.type is ConnectionError


@pytest.mark.imports
def test_import_data_wrong_path(mydb):
    """Test if importing data from a corrupt local path raises Error"""
    # given
    my_corrupt_path = "corrupt/path/to/folder"

    # Check if raises error
    with pytest.raises(FileNotFoundError) as e:
        mydb.import_data(my_corrupt_path)
    assert e.type is FileNotFoundError


@pytest.mark.imports
def test_import_data_wrong_url(mydb):
    """Test if importing data from a corrupt URL raises Error"""
    # given
    my_corrupt_url = "https://githubbb.com/3dgeo-heidelberg/pytreedb/raw/main/data/test/geojsons.zip"

    # Check if raises error
    with pytest.raises(ConnectionError) as e:
        mydb.import_data(my_corrupt_url)
    assert e.type is ConnectionError


@pytest.mark.imports
def test_import_data_not_a_zip(mydb):
    """Test if importing data from a URL which does not download a zip folder raises Error"""
    # given
    my_problematic_url = "https://github.com/3dgeo-heidelberg/pytreedb/tree/main/data/test/test_geojsons"

    # Check if raises error
    with pytest.raises(zipfile.BadZipFile) as e:
        mydb.import_data(my_problematic_url)
    assert e.type is zipfile.BadZipFile


@pytest.mark.export
def test_save(mydb, tmp_path):
    """Test for saving .db file"""
    test_db = f"{root_path}/data/test/data.db"
    out_db = tmp_path / "temp.db"

    mydb.import_db(test_db, overwrite=False)
    mydb.save(dbfile=out_db)

    assert out_db.exists()
    assert mydb.import_db(test_db, overwrite=True) == mydb.import_db(out_db, overwrite=True)
    assert pytreedb.db_utils.hash_file(mydb.dbfile) == pytreedb.db_utils.hash_file(out_db)


@pytest.mark.export
def test_export_data(mydb, tmp_path):
    """Test for exporting data: check if the correct number of files is written"""

    test_dbfile = f"{root_path}/data/test/data.db"
    mydb.load(test_dbfile)

    # expected
    n_trees = 20

    files_written = mydb.export_data(tmp_path, trees=[i for i in range(0, n_trees)])

    assert len(files_written) == n_trees
    for file in files_written:
        assert Path(file).exists()


@pytest.mark.export
def test_export_data_content(mydb, tmp_path):
    """Test for exporting data: check content of geojson files"""

    input_data = f"{root_path}/data/test/test_geojsons"

    mydb.import_data(input_data)

    mydb.export_data(tmp_path)

    first_read = list(Path(input_data).glob("*.*json"))[0]
    first_written = list(Path(tmp_path).glob("*.*json"))[0]

    with open(first_read) as f_read, open(first_written) as f_written:
        data_read = json.load(f_read)
        data_written = json.load(f_written)

    assert data_read == data_written


@pytest.mark.export
@pytest.mark.parametrize(
    "dir_name, i, trees, ncols_expected",
    [
        ("test_geojsons", 2, None, 9),
        ("test_geojsons", 0, [0, 2], 9),
        ("test_geojson_no_position", 0, None, 5),
    ],
)
def test_convert_to_csv_general(mydb, tmp_path, dir_name, i, trees, ncols_expected):
    """Test for exporting data to csv: check the general tree info"""
    input_data = f"{root_path}/data/test/{dir_name}"
    outdir_csv = tmp_path

    mydb.import_data(input_data, overwrite=True)

    all_jsons = sorted(list(Path(input_data).glob("*.*json")))
    one_json = all_jsons[i]
    csv_general = tmp_path / "result_general.csv"

    with open(one_json) as f:
        one_data_dict = json.load(f)

    if trees:
        mydb.convert_to_csv(outdir_csv, trees=trees)
        n = len(trees)
    else:
        mydb.convert_to_csv(outdir_csv)
        n = len(all_jsons)

    with open(csv_general, "r") as f:
        general_header = f.readline().strip().split(",")
    data = np.genfromtxt(csv_general, delimiter=",", skip_header=1, dtype=None, names=general_header, encoding=None)

    # table should contain as many rows as there are trees
    assert data.shape[0] == n
    # table should contain: tree_id, species, lat_epsg4326, long_epsg4326, elev_epsg4326
    assert {
        "tree_id",
        "species",
        "lat_epsg4326",
        "long_epsg4326",
        "elev_epsg4326",
    }.issubset(general_header)
    # table should contain expected number of cols
    # (9 if position is given in custom reference system as "measurement", otherwise 5)
    assert len(general_header) == ncols_expected

    # content of table should match contents of geojson
    assert data["tree_id"][i] == one_data_dict["properties"]["id"]
    assert data[i]["tree_id"] == one_data_dict["properties"]["id"]
    np.testing.assert_equal(
        structured_to_unstructured(data[["long_epsg4326", "lat_epsg4326", "elev_epsg4326"]][i]),
        one_data_dict["geometry"]["coordinates"],
    )


@pytest.mark.export
@pytest.mark.parametrize("i, trees", [(4, None), (1, [1, 3])])
def test_convert_to_csv_metrics(mydb, tmp_path, i, trees):
    """Test for exporting data to csv: check the source-specific tree metrics"""
    input_data = f"{root_path}/data/test/test_geojsons"
    outdir_csv = tmp_path

    mydb.import_data(input_data, overwrite=True)

    all_jsons = sorted(list(Path(input_data).glob("*.*json")))
    csv_metrics = tmp_path / "result_metrics.csv"

    if trees:
        mydb.convert_to_csv(outdir_csv, trees=trees)
        all_jsons = [all_jsons[tree] for tree in trees]
    else:
        mydb.convert_to_csv(outdir_csv)

    n_rows = 0
    for tree_json in all_jsons:
        with open(tree_json) as f:
            data_dict = json.load(f)
            n_source = len([1 for entry in data_dict["properties"]["measurements"] if "source" in entry.keys()])
            n_rows += n_source

    with open(csv_metrics, "r") as f:
        metrics_header = f.readline().strip().split(",")
    # this will (and should) throw an error if not all rows have the same amount of columns
    data = np.genfromtxt(csv_metrics, delimiter=",", skip_header=1, dtype=None, encoding=None, names=metrics_header)

    # table should contain n_trees x n_source (= number of sources for tree metrics) entries
    assert data.shape[0] == n_rows
    # check value of specific column
    # todo: more extensive testing here
    col = "mean_crown_diameter_m"
    assert data_dict["properties"]["measurements"][0][col] in data[col]


@pytest.mark.query
@pytest.mark.parametrize(
    "index, treeids_expected",
    [
        ([100], ["CarBet_BR01_P22T27"]),
        ([100, 101, 102], ["CarBet_BR01_P22T27", "CarBet_BR01_P22T34", "CarBet_BR01_P22T35"]),
    ],
)
def test_query_by_index(mydb_dbfile_local, index, treeids_expected):
    """Test for querying the database by index"""

    assert [fname["properties"]["id"] for fname in mydb_dbfile_local[index]] == treeids_expected
    assert mydb_dbfile_local.get_ids(mydb_dbfile_local[index]) == index


@pytest.mark.query
@pytest.mark.parametrize(
    "filter_dict, n_expected",
    [
        ({"properties.species": "Abies alba"}, 25),
        ({"properties.data.mode": "TLS"}, 264),
        ({"properties.measurements.source": "FI"}, 1060),
    ],
)
def test_query_single(mydb_dbfile_local, filter_dict, n_expected):
    """Test for using a single query"""

    assert len(mydb_dbfile_local.query(filter_dict)) == n_expected


@pytest.mark.query
@pytest.mark.parametrize(
    "filter_dict, n_expected",
    [
        ({"properties.data.point_count": {"$gt": 100000}}, 3),
        ({"properties.measurements.DBH_cm": {"$gt": 25}}, 3),
        ({"properties.measurements.height_m": {"$lt": 30}}, 5),
        ({"properties.data.quality": {"$lte": 2}}, 4),
    ],
)
def test_query_numeric_comparison(mydb_test_geojsons_local, filter_dict, n_expected):
    """Test for querying with numeric comparisons (greater than, etc.)"""

    assert len(mydb_test_geojsons_local.query(filter_dict)) == n_expected


@pytest.mark.query
@pytest.mark.parametrize(
    "filter_dict, n_expected",
    [
        (
            {"$and": [{"properties.data.quality": 1}, {"properties.data.mode": "TLS"}]},
            34,
        ),
        (
            {
                "$and": [
                    {"properties.data.quality": {"$lte": 2}},
                    {"properties.data.canopy_condition": "leaf-off"},
                ]
            },
            1036,
        ),
    ],
)
def test_query_logical(mydb_dbfile_local, filter_dict, n_expected):
    """Test for combining several queries using logical operators"""

    assert len(mydb_dbfile_local.query(filter_dict)) == n_expected


@pytest.mark.query
@pytest.mark.parametrize(
    "filter_dict, n_expected",
    [
        (
            {"properties.data": {"$elemMatch": {"quality": {"$lte": 2}, "mode": "TLS"}}},
            181,
        ),
        (
            {
                "$or": [
                    {"properties.data": {"$elemMatch": {"canopy_condition": "leaf-off", "mode": "ULS"}}},
                    {"properties.data.mode": "TLS"},
                ]
            },
            1215,
        ),
    ],
)
def test_query_elemmatch(mydb_dbfile_local, filter_dict, n_expected):
    """Test for queries using elemMatch operator"""

    assert len(mydb_dbfile_local.query(filter_dict)) == n_expected


@pytest.mark.query
def test_query_by_key_exists(mydb_test_geojsons_local):
    """Test for querying by the existence of a given key"""

    assert len(mydb_test_geojsons_local.query_by_key_exists("properties.measurements.DBH_cm")) == 5


@pytest.mark.query
@pytest.mark.parametrize(
    "regex, n_expected",
    [("Quercus*", 274), ("Quercus pet*", 156), ("[Aa]bies+", 230), ("Picea abies", 205)],
)
def test_query_by_species_regex(mydb_dbfile_local, regex, n_expected):
    """Test for querying by species using regex"""

    assert len(mydb_dbfile_local.query_by_species(regex)) == n_expected


@pytest.mark.query
@pytest.mark.parametrize(
    "key, value, regex, n_expected",
    [("properties.species", "Abies alba", False, 25), ("properties.id", "BR05+", True, 278)],
)
def test_query_by_key_value(mydb_dbfile_local, key, value, regex, n_expected):
    """Test for querying with key-value pairs (and regex)"""

    assert len(mydb_dbfile_local.query_by_key_value(key, value, regex)) == n_expected


@pytest.mark.query
@pytest.mark.parametrize(
    "key, start, end, n_expected",
    [
        ("properties.measurements.date", "2019-01-01", "2019-07-01", 618),
        ("properties.measurements.date", "2020-03-31", None, 62),
        ("properties.data.date", "2019-12-01", "2019-12-31", 1173),
    ],
)
def test_query_by_date(mydb_dbfile_local, key, start, end, n_expected):
    """Test for querying by date (start and end)"""

    assert len(mydb_dbfile_local.query_by_date(key=key, start=start, end=end)) == n_expected


@pytest.mark.query
def test_query_by_poly_geometry(mydb_dbfile_local):
    """Test for querying by geometry: within polygon"""

    coords = [
        [
            [8.657777973760469, 49.019526417240272],
            [8.6564204259407, 49.018633562408255],
            [8.655062878168346, 49.019526417240272],
            [8.656420425940698, 49.020419287904346],
            [8.657777973760469, 49.019526417240272],
        ]
    ]
    poly_dict = json.dumps({"type": "Polygon", "coordinates": coords})
    res = mydb_dbfile_local.query_by_geometry(poly_dict)

    assert len(res) == 22


@pytest.mark.query
def test_query_by_point_geometry(mydb_dbfile_local):
    """Test for querying by geometry: within distance to query point"""

    query_point = [8.6995085, 49.0131634]
    point_dict = json.dumps({"type": "Point", "coordinates": query_point})
    search_radius = 150.0
    res = mydb_dbfile_local.query_by_geometry(point_dict, distance=search_radius)

    assert len(res) == 40
