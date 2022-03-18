#!/usr/bin/env python
# -- coding: utf-8 --

import os
import pytest
import json
from pytreedb import db
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import numpy as np

load_dotenv()
conn_uri = os.environ.get("CONN_URI")
conn_db = os.environ.get("CONN_DB")
conn_col = os.environ.get("CONN_COL")

dir_path = str(Path(__file__).parent.parent.parent)


@pytest.mark.export
def test_save(tmp_path):
    """Test function to save .db file"""
    test_db = f"{dir_path}/data/test/data.db"
    out_db = tmp_path / "temp.db"

    mydbfile = tmp_path / "temp.db"
    mydb = db.PyTreeDB(
        dbfile=mydbfile, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col}
    )
    # TODO: use load() instead?
    mydb.import_db(test_db, overwrite=False)
    mydb.save(dbfile=out_db)

    assert out_db.exists()
    # TODO: use load() instead?
    assert mydb.import_db(test_db, overwrite=True) == mydb.import_db(out_db, overwrite=True)
    assert db.hash_file(mydb.dbfile) == db.hash_file(out_db)


@pytest.mark.export
def test_export_data(tmp_path):
    """Test function to export data regarding writing the correct number of files"""
    my_dbfile = tmp_path / "temp.db"

    test_dbfile = f"{dir_path}/data/test/data.db"
    mydb = db.PyTreeDB(
        dbfile=my_dbfile, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col}
    )
    mydb.load(test_dbfile)

    # expected
    n_trees = 20

    files_written = mydb.export_data(tmp_path, trees=[i for i in range(0, n_trees)])

    assert len(files_written) == n_trees
    for file in files_written:
        assert Path(file).exists()


@pytest.mark.export
def test_export_data_content(tmp_path):
    """Test function to export data regarding the content of geojson files"""
    my_dbfile = tmp_path / "temp.db"
    input_data = f"{dir_path}/data/test/test_geojsons"

    mydb = db.PyTreeDB(
        dbfile=my_dbfile, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col}
    )
    mydb.import_data(input_data)

    mydb.export_data(tmp_path)

    first_read = list(Path(input_data).glob("*.*json"))[0]
    first_written = list(Path(tmp_path).glob("*.*json"))[0]

    with open(first_read) as f_read, open(first_written) as f_written:
        data_read = json.load(f_read)
        data_written = json.load(f_written)

    assert data_read == data_written


@pytest.mark.export
@pytest.mark.parametrize('i, trees',
                         [(2, None),
                          (0, [0, 2])
                          ])
def test_convert_to_csv_general(tmp_path, i, trees):
    """Test function to export data to csv - checking the general tree info"""
    my_dbfile = tmp_path / "temp.db"
    input_data = f"{dir_path}/data/test/test_geojsons"
    outdir_csv = tmp_path

    mydb = db.PyTreeDB(
        dbfile=my_dbfile, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col}
    )
    mydb.import_data(input_data)

    all_jsons = list(Path(input_data).glob("*.*json"))
    one_json = all_jsons[i]
    csv_general = tmp_path / "result_general.csv"

    with open(one_json) as f:
        data_dict = json.load(f)

    if trees:
        mydb.convert_to_csv(outdir_csv, trees=trees)
        n = len(trees)
    else:
        mydb.convert_to_csv(outdir_csv)
        n = len(all_jsons)

    df_general = pd.read_csv(csv_general)

    # table should contain as many rows as there are trees
    assert df_general.shape[0] == n
    # table should contain: tree_id, species, lat_epsg4326, long_epsg4326, elev_epsg4326
    assert {"tree_id", "species", "lat_epsg4326", "long_epsg4326", "elev_epsg4326"}.issubset(df_general.columns)
    # content of table should match with geojson
    assert df_general.loc[i]["tree_id"] == data_dict["properties"]["id"]
    assert df_general.loc[i]["species"] == data_dict["properties"]["species"]
    np.testing.assert_equal(
                            df_general.loc[i][["long_epsg4326", "lat_epsg4326", "elev_epsg4326"]].to_numpy(),
                            data_dict["geometry"]["coordinates"]
    )


@pytest.mark.export
@pytest.mark.parametrize('i, trees',
                         [(4, None),
                          (1, [1, 3])
                          ])
def test_convert_to_csv_metrics(tmp_path, i, trees):
    """Test function to export data to csv - checking the source-specific tree metrics"""
    my_dbfile = tmp_path / "temp.db"
    input_data = f"{dir_path}/data/test/test_geojsons"
    outdir_csv = tmp_path

    mydb = db.PyTreeDB(
        dbfile=my_dbfile, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col}
    )
    mydb.import_data(input_data)

    all_jsons = list(Path(input_data).glob("*.*json"))
    one_json = all_jsons[i]
    csv_metrics = tmp_path / "result_metrics.csv"

    if trees:
        mydb.convert_to_csv(outdir_csv, trees=trees)
        all_jsons = [all_jsons[tree] for tree in trees]
    else:
        mydb.convert_to_csv(outdir_csv)

    n_cols = 0
    n_trees = len(all_jsons)
    for tree_json in all_jsons:
        with open(tree_json) as f:
            data_dict = json.load(f)
            n_source = len(data_dict["properties"]["measurements"])
            n_cols += n_source

    df_metrics = pd.read_csv(csv_metrics)
    some_columns = list(data_dict["properties"]["measurements"][0].keys())
    print(some_columns)

    # table should contain n_trees x n_source (= number of sources for tree metrics) entries
    assert df_metrics.shape[0] == n_cols
    # check for the measurements of the last trees if all dict keys are in the table
    assert set(data_dict["properties"]["measurements"][0].keys()).issubset(df_metrics.columns)


@pytest.mark.imports
def test_import_data(tmp_path):
    """Tests reading data (json files) from local file or from URL of ZIP archive with files named like *.*json"""

    # given
    db_file = tmp_path / "temp.db"
    mydb = db.PyTreeDB(
        dbfile=db_file, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col}
    )
    data_url = r"https://heibox.uni-heidelberg.de/f/05969694cbed4c41bcb8/?dl=1"

    # expected
    cnt_trees_expected = 1491

    # TODO: Shall the import_data() function really return the number of trees?
    assert (mydb.import_data(data_url) == cnt_trees_expected)


@pytest.mark.imports
def test_import_data_wrong_local_path(tmp_path):
    """Tests importing data from a corrupt local path"""
    # given
    db_file = tmp_path / "temp.db"
    mydb = db.PyTreeDB(
        dbfile=db_file, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col}
    )
    my_corrupt_path = "corrupt/path/to/folder"

    # Check if raises error
    with pytest.raises(FileNotFoundError) as e:
        mydb.import_data(my_corrupt_path)
    assert e.type is FileNotFoundError

# clear()
# import_data()
# import_db()

# query

# indexing db
# different queries
# also cases where we expect errors to be caught
# get_ids

# get_tree_as_json (is this function even needed?)
# validate_json()

# utils

# needed: small db for fast testing purposes?

# also think beyond: e.g., users with their own data with different tree properties
# make sure these can also be queried!
