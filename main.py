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

import pytreedb.pytreedb as pytreedb

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

mydb = pytreedb.PyTreeDB(dbfile=r'E:\tmp\SYSSIFOSS\syssifoss.db') # instantiate pytreedb
# mydb.load_db(r'E:\tmp\SYSSIFOSS\syssifoss.db') # Jiani: loading local db file
# mydb.import_data(r'https://heibox.uni-heidelberg.de/f/05969694cbed4c41bcb8/?dl=1', overwrite=True) # download data

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

@app.route('/trees/<fields>/<values>')
def naiveQuery(fields, values):
    fields = fields.split(',')
    values = values.split(',')
    res = []
    if fields == [''] or values == ['']:
        return dict()
    j = 0
    for i in range(len(fields)):
        if fields[i] == 'quality':
            if values[j] == values[j+1]:
                res.append(mydb.query_by_numeric_comparison('quality', float(values[j]), pytreedb.eq))
            else:
                res.append(mydb.query_by_numeric_comparison('quality', float(values[j]), pytreedb.ge))
                res.append(mydb.query_by_numeric_comparison('quality', float(values[j+1]), pytreedb.le))
            j += 2
        else:
            res.append(mydb.query(fields[i], values[j]))
            j += 1
    return {'query': mydb.inner_join(res)}

@app.route('/search', methods=['POST'])
def query():
    query = request.get_json(force=True)['data']
    print(query[0])
    # res = andQuery(json)
    return {'query': res}

def andQuery(jsonObj):
    res = []
    for key, value in jsonObj.items():
        if key.startswith('or'):
            res.append(orQuery(jsonObj[key])) # recursively call or-query fct.
        else:
            res.append(mydb.query(key, value))
    return mydb.inner_join(res)

def orQuery(jsonArr):
    res = []
    for obj in jsonArr:
        res.append(andQuery(obj)) # recursively call and-query fct.
    return mydb.outer_join(res)

@app.route('/getitem/<index>')
def getItem(index):
    if index == '':
        return dict()
    print(mydb[int(index)]['_json'])
    return {'item': mydb[int(index)]['_json']}
    # print({'item': json.loads(mydb[int(index)]['_json'])})
    # return {'item': json.loads(mydb[int(index)]['_json'])}

@app.route('/exportcsv/<fields>/<values>')
def exportcsv(fields, values):
    trees = query(fields, values)['query']
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