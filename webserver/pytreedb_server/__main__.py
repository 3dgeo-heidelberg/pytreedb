#!/usr/bin/env python
# -- coding: utf-8 --

"""
Flask backend for PytreeDB
"""
import sys
import io
import os
import flask
import shutil
import tempfile
import json
import base64
from pathlib import Path

from zipfile import ZipFile

from flask import Flask
from flask import request
from flask import Response
from flask import render_template

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), '.env'))  # load from current user dir

pytreedb_loc = os.environ.get("PYTREEDB_LOCATION")
if pytreedb_loc:
    pytreedb_loc = Path(pytreedb_loc) / ".."
    sys.path.append(str(pytreedb_loc.absolute()))
try:
    from pytreedb import db
except:
    print("Error: Could not import pytreedb.")
    print("       Ensure you have installed pytreedb via pip.")
    print("       You can alternatively set the location to the pytreedb directory ")
    print("       in an `.env`-File (see README.md for details):")
    print("       PYTREEDB_LOCATION=\"path/to/pytreedb\"")
    print("-- Original error follows below --")
    raise

conn_uri = os.environ.get("CONN_URI")
conn_db = os.environ.get("CONN_DB")
conn_col = os.environ.get("CONN_COL")

if not conn_uri or not conn_db or not conn_col:
    print("Error: connection to MongoDB not set.")
    print("       Please provide the connection parameters in a `.env`-File.")
    print("       Refer to README.md for more information")
    sys.exit(1)

db_name = os.environ.get("PYTREEDB_FILENAME")
if not db_name:
    print("Warning: no filename for the local pytreedb supplied.")
    print("         using 'pytree.db' (in the current directory) instead.")
    print("         To set it in the future, put an 'PYTREEDB_FILENAME' statement in a `.env`-File.")
    print("         Refer to README.md for more information")

db_download = os.environ.get("PYTREEDB_DOWNLOAD")

app = Flask("pytreedb-server",
            static_folder=os.path.join(os.path.dirname(__file__), 'static'),
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

@app.route('/')
def index():
    return render_template(r'index.html', server=request.remote_addr)

@app.route('/about')
def about():
    return render_template(r'about.html')

@app.route('/contact')
def contact():
    return render_template(r'contact.html')

@app.route('/query/<query>')
def showQuery(query=None):
    return render_template(r'index.html', query=query)

@app.route('/stats')
def getStats():
    return mydb.get_stats()

@app.route('/listspecies')
def getListSpecies():
    return {'species': mydb.get_list_species()}

@app.route('/sharedproperties')
def getSharedProperties():
    return {'properties': mydb.get_shared_properties()}

@app.route('/getitem/<index>')
def getItem(index):
    return {'item': mydb[int(index)]}

@app.route('/search', methods=['POST'])
def query():
    query = json.loads(request.form['query'])
    res = mydb.query(query, {'_id': False})
    print(query)
    print(len(res))
    return {'query_res': res}

@app.route('/search/wssearch', methods=['POST'])
def webserverQuery():
    query = json.loads(request.form['query'])
    trees = mydb.query(query, {'_id': False})
    # return only full geojson file within the preview limit
    limit = int(request.form['limit'])
    entry_set = int(request.form['nthEntrySet'])
    num_res = len(trees)
    res_coords = None
    if request.form['getCoords'] == 'true':
        # return all resulting tree coordinates to show on the map
        res_coords = mydb.query(query, {'_id': False, '_id_x': 1, 'geometry': 1, 'type': 1, 'properties.id': 1})
    print('User query: ', query)
    print('Number of results: ', num_res)
    return {'res_preview': trees[limit*entry_set:limit*(entry_set+1)], 'res_coords': res_coords, 'num_res': num_res}

def decodeB64Query(query):
    return json.loads(base64.b64decode(query).decode("utf-8"))

@app.route('/download/exportcollection/<query>', methods=['GET'])
def exportFC(query):
    query = decodeB64Query(query)
    res = mydb.query(query, {'_id': False})
    collection = json.dumps({'type': 'FeatureCollection', 'features': res})
    return Response(collection,
            mimetype='application/json',
            headers={'Content-Disposition':'attachment; filename=res_feature_collection.json'})

@app.route('/download/lazlinks/tree/<index>', methods=['GET'])
def exportTreeLazLinks(index):
    links = mydb.get_pointcloud_urls([mydb[int(index)]])
    return {'links': links}

@app.route('/download/lazlinks/<query>', methods=['GET'])
def exportQueryLazLinks(query):
    query = decodeB64Query(query)
    links = mydb.get_pointcloud_urls(mydb.query(query, {'_id': False, 'properties.data': 1}))
    return {'links': links}

@app.route('/download/exportcsv/<query>', methods=['GET'])
def exportcsv(query):
    query = decodeB64Query(query)
    # get ids of resulting trees
    trees_idx = [tree['_id_x'] for tree in mydb.query(query, {'_id': False, '_id_x': 1})]
    # convert trees to csv files, save to disk
    outdir = tempfile.mkdtemp()
    mydb.convert_to_csv(outdir, trees_idx)
    # zip csv files
    o = io.BytesIO()
    with ZipFile(o, 'w') as zf:
        zf.write(outdir + '/result_general.csv', 'result_general.csv')
        zf.write(outdir + '/result_metrics.csv', 'result_metrics.csv')
    zf.close()
    o.seek(0)
    # remove local csv
    shutil.rmtree(outdir)
    os.mkdir(outdir)
    
    return flask.send_file(
        o,
        mimetype='application/zip',
        as_attachment=True,
        attachment_filename='csv.zip'
    )


mydb = db.PyTreeDB(dbfile=db_name, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col})
if db_download:
    mydb.import_data(db_download, overwrite=True)
else:
    try:
        mydb.import_db(db_name, overwrite=False)
    except:
        print(f"Error: could not import database file '{db_name}'.")
        print("       You probably need to download/import data beforehand, e.g.")
        print("       by providing a link in the 'PYTREEDB_DOWNLOAD' variable in the '.env'-File.")
        print("       Refer to README.md for more information")
        print("-- Original error follows below --")
        raise

app.config['CORS_HEADERS'] = 'Content-Type'
dl_progress = {'currItem': 0, 'numAllItems': 0}

# when module is loaded, start flask server
if __name__ == '__main__':
    app.run(port=os.environ.get("FLASK_RUN_PORT"), host=os.environ.get("FLASK_RUN_HOST"))
