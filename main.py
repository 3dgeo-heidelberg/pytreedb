#!/usr/bin/env python
# -- coding: utf-8 --

"""
description
"""
import json
import webbrowser

from flask import Flask
from flask import request
from flask import render_template

import pytreedb.pytreedb as pytreedb

app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template(r'newIndex.html', server=request.remote_addr)

mydb = pytreedb.PyTreeDB(dbfile=r'E:\tmp\SYSSIFOSS\syssifoss.db') # instantiate pytreedb
mydb.load_db(r'E:\tmp\SYSSIFOSS\syssifoss.db') # Jiani: loading local db file
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

@app.route('/trees')
def query():
    field = request.args.get('field')
    value = request.args.get('value')
    if field == '' or value == '':
        return dict()
    return {'query': mydb.query(field, value)}

@app.route('/getitem')
def getItem():
    index = request.args.get('index')
    if index == '':
        return dict()
    # print(mydb[int(index)])
    print({'item': json.loads(mydb[int(index)]['_json'])})
    return {'item': json.loads(mydb[int(index)]['_json'])}

