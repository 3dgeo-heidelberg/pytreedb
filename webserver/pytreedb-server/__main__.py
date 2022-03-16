#!/usr/bin/env python
# -- coding: utf-8 --

"""
Flask backend for PytreeDB
"""
import webbrowser
import io
import os
import flask
import shutil

from zipfile import ZipFile
from flask import Flask
from flask import request
from flask import render_template

from pytreedb import db

from dotenv import load_dotenv

load_dotenv()
conn_uri = os.environ.get("CONN_URI")
conn_db = os.environ.get("CONN_DB")
conn_col = os.environ.get("CONN_COL")

db_name = os.environ.get("PYTREEDB_FILENAME")
db_download = os.environ.get("PYTREEDB_DOWNLOAD")

app = Flask(__name__)
# when module is loaded, start flask server
if __name__ == '__main__':
    mydb = db.PyTreeDB(dbfile=db_name, mongodb={"uri": conn_uri, "db": conn_db, "col": conn_col})
    if db_download:
        mydb.import_db(db_download, overwrite=True)
    else:
        mydb.import_db(db_name, overwrite=False)
    app.config['CORS_HEADERS'] = 'Content-Type'
    dl_progress = {'currItem': 0, 'numAllItems': 0}
    app.run()

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

@app.route('/search', methods=['POST'])
def query():
    query = request.get_json(force=True)['data']
    res = mydb.query(query, {'_id': False})
    print(query)
    print(len(res))
    return {'query': res}

@app.route('/getitem/<index>')
def getItem(index):
    return {'item': mydb[int(index)]}

@app.route('/exportcsv', methods=['POST'])
def exportcsv():
    query = request.get_json(force=True)['data']
    trees = mydb.query(query, {'_id': False})
    # convert trees to csv files, save to disk
    outdir = r'E:\tmp\csv'
    mydb.convert_to_csv(outdir, trees)
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