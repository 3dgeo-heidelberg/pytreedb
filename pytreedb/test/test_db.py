#!/usr/bin/env python
# -- coding: utf-8 --

import os
import sys
import pytest
from pytreedb import db
from dotenv import load_dotenv

load_dotenv()
conn_uri = os.environ.get("CONN_URI")
conn_db = os.environ.get("CONN_DB")
conn_col = os.environ.get("CONN_COL")

# functions to test:

##### export
# save()
# export_data()
# export_to_csv()

#### import
# initiate db
# load()
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