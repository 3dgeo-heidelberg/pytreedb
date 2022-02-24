#!/usr/bin/env python
# -- coding: utf-8 --

"""
description
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
    return render_template(r'newIndex.html', server=request.remote_addr)

@app.route('/about')
def about():
    return render_template(r'about.html')

@app.route('/contact')
def contact():
    return render_template(r'contact.html')

mydbfile='syssifoss.db'
mydb = db.PyTreeDB(dbfile=mydbfile, mongodb = {"uri": "mongodb://127.0.0.1:27017/", "db": "pytreedb", "col": "syssifoss"})
mydb.import_data(r'https://heibox.uni-heidelberg.de/f/05969694cbed4c41bcb8/?dl=1', overwrite=True)
# mydb = pytreedb.PyTreeDB(dbfile=r'D:\tmp\SYSSIFOSS\syssifoss.db') # instantiate pytreedb
# mydb.load_db(r'E:\tmp\SYSSIFOSS\syssifoss.db') # Jiani: loading local db file
#mydb.import_data(r'https://heibox.uni-heidelberg.de/f/05969694cbed4c41bcb8/?dl=1', overwrite=True) # download data

# automatically open in a new browser tab on start
if __name__ == 'main':
    webbrowser.open_new_tab('http://127.0.0.1:5000/')

@app.route('/stats')
def getStats():
    return mydb.get_stats()

@app.route('/listspecies')
def getListSpecies():
    print(mydb.get_list_species())
    return {'species': mydb.get_list_species()}

@app.route('/sharedproperties')
def getSharedProperties():
    return {'properties': mydb.get_shared_properties()}

@app.route('/search', methods=['POST'])
def query():
    query = request.get_json(force=True)['data']
    print(query)
    res = mydb.query(query, {'_id': False})
    print(len(res))
    return {'query': res}

def procSubquery(li):
    res = []
    for subQuery in li:
        if isinstance(subQuery, str):  # if subQuery not nested
            kv = subQuery.split(":")
            res.append(mydb.query(kv[0], kv[1]))
        elif type(subQuery) == list and subQuery[0] == "and":  # if nested AND query
            res.append(andQuery(subQuery))
        else:  # if nested OR query
            res.append(orQuery(subQuery))
    return res

@app.route('/getitem/<index>')
def getItem(index):
    if index == '':
        return dict()
    print(mydb[int(index)]['_json'])
    return {'item': mydb[int(index)]['_json']}
    # print({'item': json.loads(mydb[int(index)]['_json'])})
    # return {'item': json.loads(mydb[int(index)]['_json'])}

@app.route('/exportcsv', methods=['POST'])
def exportcsv():
    query = request.get_json(force=True)['data']
    trees = orQuery(query)
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