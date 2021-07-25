#!/usr/bin/env python
# -- coding: utf-8 --

"""
description
"""
import webbrowser
import requests
import io
import flask
import threading

from zipfile import ZipFile
from flask import Flask
from flask import request
from flask import render_template

import pytreedb.pytreedb as pytreedb

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
dl_progress = {'currItem': 0, 'numAllItems': 0}
# downloading_thread = None

# class DownloadingThread(threading.Thread):
#     def __init__(self, urls, o):
#         self.progress = 0
#         self.urls = urls
#         self.num_urls = len(urls)
#         self.data = o
#         super().__init__()

#     def run(self):
#         with ZipFile(self.data, 'w') as zf:
#             for i in range(self.num_urls):
#                 res = requests.get(self.urls[i]).content
#                 zf.writestr('file_{:02d}.laz'.format(i), res)
#                 # self.progress += 1/self.num_urls
#         # zf.close()
#         self.data.seek(0)

@app.route('/')
def index():
    return render_template(r'newIndex.html', server=request.remote_addr)

@app.route('/about')
def about():
    return render_template(r'about.html')

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
    fields = request.args.get('field').split(',')
    values = request.args.get('value').split(',')
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

@app.route('/getitem')
def getItem():
    index = request.args.get('index')
    if index == '':
        return dict()
    print(mydb[int(index)]['_json'])
    return {'item': mydb[int(index)]['_json']}
    # print({'item': json.loads(mydb[int(index)]['_json'])})
    # return {'item': json.loads(mydb[int(index)]['_json'])}

@app.route('/downloadpointclouds')
def downloadPointClouds():
    global dl_progress
    
    # urls = ['https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2021-05-28/2021-05-07-raspios-buster-armhf-lite.zip']
    urls = ['https://heibox.uni-heidelberg.de/f/3e52b2c164b247fe85ec/?dl=1',
            'https://heibox.uni-heidelberg.de/f/ad707892be7e41dcabe3/?dl=1',
            'https://heibox.uni-heidelberg.de/f/7d45579bd93d4b6080c2/?dl=1',
            'https://heibox.uni-heidelberg.de/f/0ad8e4ff417148d0a6c6/?dl=1',
            'https://heibox.uni-heidelberg.de/f/4305958abd184a328883/?dl=1',
            'https://heibox.uni-heidelberg.de/f/bcb95a59940e46a4ab49/?dl=1',
            'https://heibox.uni-heidelberg.de/f/2c596eb6a9994219b7da/?dl=1',
            'https://heibox.uni-heidelberg.de/f/8bb1148aa07148c19a62/?dl=1',
            'https://heibox.uni-heidelberg.de/f/6f747477a00446478909/?dl=1',
            'https://heibox.uni-heidelberg.de/f/68a9caba76104a3488ce/?dl=1',
            'https://heibox.uni-heidelberg.de/f/15ea8cd53f274a3a87a7/?dl=1',
            'https://heibox.uni-heidelberg.de/f/9f60b9dd8c074c70bb4d/?dl=1',
            'https://heibox.uni-heidelberg.de/f/dafe73a0e66f4433a023/?dl=1',
            'https://heibox.uni-heidelberg.de/f/5140fb024f6c46e484ae/?dl=1',
            'https://heibox.uni-heidelberg.de/f/60a912c9e83a46e780ea/?dl=1']
    dl_progress['numAllItems'] = len(urls)
    dl_progress['currItem'] = 0
    
    # send requests and add to zip    
    o = io.BytesIO()
    with ZipFile(o, 'w') as zf:
            for i in range(len(urls)):
                res = requests.get(urls[i]).content
                zf.writestr('file_{:02d}.laz'.format(i), res)
                dl_progress['currItem'] += 1
    zf.close()
    o.seek(0)
    
    return flask.send_file(
        o,
        mimetype='application/zip',
        as_attachment=True,
        attachment_filename='pointclouds.zip'
    )

@app.route('/list_pointclouds')
def listPointClouds():
    # urls = ['https://nodejs.org/dist/v16.5.0/node-v16.5.0-x64.msi']
    urls = ['https://3dweb.geog.uni-heidelberg.de/database_sample/PinSyl_KA10_01_2019-07-05_q2_ALS-on.laz',
            'https://3dweb.geog.uni-heidelberg.de/database_sample/PinSyl_KA10_01_2019-07-30_q4_TLS-on.laz',
            'https://3dweb.geog.uni-heidelberg.de/database_sample/PinSyl_KA10_01_2019-09-13_q2_ULS-on.laz']
    return {'urls': urls}
    
@app.route('/progress')
def progress():
    global dl_progress
    return dl_progress