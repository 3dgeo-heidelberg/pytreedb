#!/usr/bin/env python
# -- coding: utf-8 --

"""
Flask backend for PytreeDB
"""
import webbrowser
import requests
import io
import os
import flask
import threading
import shutil

from zipfile import ZipFile
from flask import Flask
from flask import request
from flask import render_template

from pytreedb import db
import sys
import json

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
dl_progress = {'currItem': 0, 'numAllItems': 0}

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
    return render_template(r'newIndex.html', query = query)

mydbfile='syssifoss.db'
mydb = db.PyTreeDB(dbfile=mydbfile, mongodb = {"uri": "mongodb://127.0.0.1:27017/", "db": "pytreedb", "col": "syssifoss"})
mydb.import_db(r'syssifoss.db', overwrite=False)
# mydb.import_data(r'https://heibox.uni-heidelberg.de/f/05969694cbed4c41bcb8/?dl=1', overwrite=True)

# automatically open in a new browser tab on start
if __name__ == 'main':
    webbrowser.open_new_tab('http://127.0.0.1:5000/')

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

@app.route('/list_pointclouds')
def listPointClouds():
    urls = ['https://3dweb.geog.uni-heidelberg.de/database_sample/PinSyl_KA10_01_2019-07-05_q2_ALS-on.laz',
            'https://3dweb.geog.uni-heidelberg.de/database_sample/PinSyl_KA10_01_2019-07-30_q4_TLS-on.laz',
            'https://3dweb.geog.uni-heidelberg.de/database_sample/PinSyl_KA10_01_2019-09-13_q2_ULS-on.laz']
    return {'urls': urls}
    
@app.route('/progress')
def progress():
    global dl_progress
    return dl_progress