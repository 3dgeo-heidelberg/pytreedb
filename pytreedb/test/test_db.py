#!/usr/bin/env python
# -- coding: utf-8 --

import os
import sys
import pytest
import json
from pytreedb import db
from dotenv import load_dotenv
from pathlib import Path

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
    """Test function to export data regarding the content of files"""
    my_dbfile = tmp_path / "temp.db"
    input_data = f"{dir_path}/data/test/test_geojsons"

    mydb = db.PyTreeDB(
        dbfile=my_dbfile, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col}
    )
    mydb.import_data(input_data)

    mydb.export_data(tmp_path)

    # assert input_data = exported data (check/compare contents of geojsons)
    pass


@pytest.mark.export
def test_export_to_csv():
    pass


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
def test_import_data_wrong_path(tmp_path):
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
