#!/usr/bin/env python
# -- coding: utf-8 --

import os
import sys
import pytest
from pytreedb import db
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
conn_uri = os.environ.get("CONN_URI")
conn_db = os.environ.get("CONN_DB")
conn_col = os.environ.get("CONN_COL")

# functions to test:

##### export
# save()
# export_data()
# export_to_csv()

@pytest.mark.export
def test_save(tmp_path):
    """Test function to save .db file"""
    test_db = "data/test/data.db"
    out_db = tmp_path / "temp.db"

    mydbfile = tmp_path / "temp.db"
    mydb = db.PyTreeDB(
        dbfile=mydbfile, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col}
    )
    mydb.import_db(test_db, overwrite=False)
    mydb.save(dbfile=out_db)

    assert out_db.exists()
    assert mydb.import_db(str(test_db), overwrite=True) == mydb.import_db(str(out_db), overwrite=True)


@pytest.mark.export
def test_export_data():
    """Test function to export data"""
    pass

#### import

#p@pytest.mark.import # marker "import" can be used to run only tests with this marker
def test_import_data():
    """Tests reading data (json files) from local file or from URL of ZIP archive with files named like *.*json"""

    # given
    db_file = r"data/test_data/data.db"
    mydb = db.PyTreeDB(
        dbfile = db_file, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col}
    )
    data_url = r"https://heibox.uni-heidelberg.de/f/92dcfa3eecb240a6b550/?dl=1"

    # expected
    cnt_trees_expected = 1491

    assert (mydb.import_data(db_file, data_url) == cnt_trees_expected)



# clear()
# import_data()
# import_db()

#### query
# indexing db
# different queries
# also cases where we expect errors to be caught
# get_ids

# get_tree_as_json (is this function even needed?)
# validate_json()

#### utils

# needed: small db for fast testing purposes?

# also think beyond: e.g., users with their own data with different tree properties
# make sure these can also be queried!