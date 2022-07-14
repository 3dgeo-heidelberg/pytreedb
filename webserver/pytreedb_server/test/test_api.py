#!/usr/bin/env python
# -- coding: utf-8 --

import os
import time
import zipfile
import io

import pytest
from dotenv import load_dotenv
from pathlib import Path
import requests

# from requests.adapters import HTTPAdapter, Retry

import threading
import json
import base64

load_dotenv()
run_flask = os.environ.get("FLASK_RUN")
if run_flask is None:
    run_flask = "1"
if run_flask == "1":
    conn_uri = os.environ.get("CONN_URI")
    conn_db = os.environ.get("CONN_DB")
    conn_col = os.environ.get("CONN_COL")

host = os.environ.get("FLASK_RUN_HOST")
flask_host = host
if not host.startswith("http"):  # could be http or https
    host = "http://" + host
port = os.environ.get("FLASK_RUN_PORT")

root_path = str(Path(__file__).parent.parent.parent)


@pytest.fixture(
    scope="module"
)  # module scope to create server only once for all tests in this module
def myserver(tmp_path_factory):
    if run_flask == "1":
        db_path = tmp_path_factory.mktemp("db_path")
        os.environ["PYTREEDB_FILENAME"] = str(db_path / "temp.db")
        from ..__main__ import app

        th = threading.Thread(
            target=lambda: app.run(port=port, host=flask_host, use_reloader=False)
        )
        th.daemon = True  # run as daemon so that it stops automatically when the parent process (i.e., this test) exits
        th.start()
        time.sleep(5)  # 5 seconds for the server to start
        yield th
        os.remove(
            os.environ.get("PYTREEDB_FILENAME")
        )  # clean up db file after running tests
    else:
        yield None


@pytest.fixture()
def session():
    s = requests.Session()
    # retries = Retry(total=5,
    #                backoff_factor=0.1)
    # s.mount('*', HTTPAdapter(max_retries=retries))
    return s


def test_get_tree_number(myserver, session):
    response = get_query(session, f"{host}:{port}/stats")
    assert response.status_code == 200
    values = json.loads(response.content.decode())
    assert values["n_species"] == 22
    assert values["n_trees"] == 1491


def get_query(session, url, **kwargs):
    return session.get(url, timeout=(5, 15), **kwargs)


def post_query(session, url, **kwargs):
    return session.post(url, timeout=(5, 15), **kwargs)


def test_get_listspecies(myserver, session):
    response = get_query(session, f"{host}:{port}/listspecies")
    assert response.status_code == 200
    values = json.loads(response.content.decode())
    assert len(values["species"]) == 22
    assert sorted(values["species"])[12] == "Prunus serotina"


def test_get_sharedproperties(myserver, session):
    response = get_query(session, f"{host}:{port}/sharedproperties")
    assert response.status_code == 200
    values = json.loads(response.content.decode())
    assert values["properties"][0] == "data"
    assert values["properties"][1] == "id"
    assert values["properties"][2] == "measurements"
    assert values["properties"][3] == "measurements_metadata"
    assert values["properties"][4] == "source"
    assert values["properties"][5] == "species"


def test_get_uls_only(myserver, session):
    query = {
        "query": '{"properties.data.mode":"ULS"}',
        "limit": "3",
        "nthEntrySet": "0",
        "getCoords": "true",
    }
    response = post_query(session, f"{host}:{port}/search/wssearch", data=query)
    assert response.status_code == 200
    values = json.loads(response.content.decode())
    assert values["num_res"] == 1291


def test_get_complex1_and(myserver, session):
    query = {
        "query": '{"$and":['
        '{"properties.measurements.DBH_cm":{"$lt":14,"$gt":1}},'
        '{"properties.measurements.source":"FI"},'
        '{"properties.data.mode":"ALS"}'
        "]}",
        "limit": "3",
        "nthEntrySet": "0",
        "getCoords": "true",
    }
    response = post_query(session, f"{host}:{port}/search/wssearch", data=query)
    assert response.status_code == 200
    values = json.loads(response.content.decode())
    assert values["num_res"] == 186


def test_get_complex2_and_or(myserver, session):
    query = {
        "query": '{"$or":['
        '{"$and":['
        '{"$and":['
        '{"properties.data.quality":1},'
        '{"properties.data.quality":2}'
        "]},"
        '{"properties.data.canopy_condition":"leaf-on"}'
        "]},"
        '{"properties.species":"Acer campestre"}'
        "]}",
        "limit": "3",
        "nthEntrySet": "0",
        "getCoords": "true",
    }
    response = post_query(session, f"{host}:{port}/search/wssearch", data=query)
    assert response.status_code == 200
    values = json.loads(response.content.decode())
    assert values["num_res"] == 39


def test_get_exportcsv(myserver, session):
    query = {
        "data": '{"$or":['
        '{"$and":['
        '{"$and":['
        '{"properties.data.quality":1},'
        '{"properties.data.quality":2}'
        "]},"
        '{"properties.data.canopy_condition":"leaf-on"}'
        "]},"
        '{"properties.species":"Acer campestre"}'
        "]}"
    }
    response = get_query(
        session,
        f"{host}:{port}/download/exportcsv/{base64.b64encode(query['data'].encode()).decode()}",
    )
    assert response.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(response.content), "r")
    filelist = sorted(zf.infolist(), key=lambda x: x.file_size)
    assert filelist[0].filename == "result_general.csv"
    assert abs(filelist[0].file_size - 4_390) < 4_096
    assert filelist[1].filename == "result_metrics.csv"
    assert abs(filelist[1].file_size == 12_024) < 4_096


def test_get_exportcollection(myserver, session):
    query = {
        "data": '{"$or":['
        '{"$and":['
        '{"$and":['
        '{"properties.data.quality":1},'
        '{"properties.data.quality":2}'
        "]},"
        '{"properties.data.canopy_condition":"leaf-on"}'
        "]},"
        '{"properties.species":"Acer campestre"}'
        "]}"
    }
    response = get_query(
        session,
        f"{host}:{port}/download/exportcollection/{base64.b64encode(query['data'].encode()).decode()}",
    )
    assert response.status_code == 200
    values = json.loads(response.content.decode())
    assert len(values["features"]) == 39


def test_get_lazlinks(myserver, session):
    query = {"data": '{"properties.data.mode":"TLS"}'}
    response = get_query(
        session,
        f"{host}:{port}/download/lazlinks/{base64.b64encode(query['data'].encode()).decode()}",
    )
    assert response.status_code == 200
    values = json.loads(response.content.decode())
    assert len(values["links"]) == 1009


def test_get_lazlinks_single_tree(myserver, session):
    response = get_query(session, f"{host}:{port}/download/lazlinks/tree/42")
    assert response.status_code == 200
    values = json.loads(response.content.decode())
    assert len(values["links"]) == 3
