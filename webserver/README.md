# pytreedb-Server

This package provides a webserver as a frontend to a `pytreedb` instance.

<img src="https://github.com/3dgeo-heidelberg/pytreedb/blob/main/doc/_static/pytreedb_webserver_home.png?raw=true" width="85%">

## Prerequisites
- Python packages:
  - `pytreedb`
  - `flask`
  - `dotenv`
  
## Deployment for local dev
### Installation
The `pytreedb_server` package can be a) installed via PyPI, b) installed via pip from the git repo or c) used as a local directory.

a) \[Recommended\]: Run `python -m pip install pytreedb_server` in a prepared (e.g., conda) environment, which will also install `pytreedb`. You can then import `pytreedb_server` and `pytreedb` from anywhere.

b) Clone the git repository, and change directory into the `webserver` dir. Then run `python -m pip install .`, which will take the local files to create a package, and copy it to the environment's `site-packages` directory. You  can then import `pytreedb_server` and `pytreedb` from anywhere.

c) Clone the git repository, and change directory into the `webserver` dir. Run the commands to run the local webserver (see below) *from this directory*. You will need to provide the `PYTREEDB_LOCATION` parameter (see next subsection).

### Setup using `.env`
We use the `dotenv` package to configure the server. Both `pytreedb` and `flask` parameters should be written to
the `.env`-File in the current directory: 
```
# path of the pytreedb package (if not installed via PIP)
PYTREEDB_LOCATION="../pytreedb"
# local filename for database file
PYTREEDB_FILENAME="syssifoss.db"
# if set, download (and overwrite local file) data from this URL
PYTREEDB_DOWNLOAD="https://github.com/3dgeo-heidelberg/pytreedb/raw/main/data/test/geojsons.zip"
# connection string to mongodb (e.g. 127.0.0.1, or "mongodb+srv://..." if using MongoDB Cloud)
CONN_URI = ""
# database name to connect to
CONN_DB = ""
# collection to connect to
CONN_COL = ""
# FLASK settings

FLASK_RUN_HOST="0.0.0.0"
FLASK_RUN_PORT="5001"
```

### Configuring pytreedb dataset
The dataset is not a prerequisite. Please follow the instructions after getting Flask to running on your machine.


### Serve the webserver locally
Under the webserver folder, run:

```
conda activate pytreedb
python -m pytreedb_server
```

## Deployment for production
Note that Flask is not suitable for production. However, it is possible to use the package *as-is* in Apache WGSI, following these steps:

1) Install `mod_wsgi` **in the conda environment used for the server**. In the following, it is assumed that the environment is called `pytreedb`.
```
conda create -n pytreedb python=3.8
conda activate pytreedb
conda install mod_wsgi -c conda-forge -y
python -m pip install python-dotenv pandas pymongo[srv]
```

2) Install `pytreedb_server` from pip:
```
python -m pip install pytreedb_server
```

3) Get the path to the WSGI library:
```
mod_wsgi-express module-config
```

This e.g. gives
```
LoadModule wsgi_module "/opt/miniconda3/envs/pytreedb/lib/python3.9/site-packages/mod_wsgi/server/mod_wsgi-py39.cpython-39-x86_64-linux-gnu.so"
WSGIPythonHome "/opt/miniconda3/envs/pytreedb"
```

4) Create/edit the apache server configuration. Here, we will overwrite the default configuration. Edit the file `/etc/apache2/sites-enabled/000-default.conf` with a text editor of your choice (`vim`, `nano`) as `root`, and insert these lines.
Be sure to adapt all the paths related to your `conda` installation and the location where you want to have your database placed (in this example: `/var/www/pytreedb`)
```
WSGIPythonHome "/opt/miniconda3/envs/pytreedb"
LoadModule wsgi_module "/opt/miniconda3/envs/pytreedb/lib/python3.8/site-packages/mod_wsgi/server/mod_wsgi-py38.cpython-38-x86_64-linux-gnu.so"

<VirtualHost *:80>
    ServerAdmin webmaster@localhost

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    WSGIDaemonProcess pytreedb python-path=/opt/miniconda3/envs/pytreedb/lib/python3.8/site-packages home=/var/www/pytreedb/webserver
    WSGIScriptAlias / /var/www/pytreedb/pytreedb_server.wsgi

    <Directory /var/www/pytreedb/>
        WSGIProcessGroup pytreedb
        WSGIApplicationGroup %{GLOBAL}
        Order deny,allow
        Allow from all
    </Directory>
</VirtualHost>
```

5) Create a new file `/var/www/pytreedb/pytreedb_server.wsgi` (adapt paths as required) and add the following line:
```
from pytreedb_server.__main__ import app as application
```
If you have not installed `pytreedb` and `pytreedb_server` via pip, you need to add the paths to the installations prior:
```
import sys
sys.path.insert(0, '/var/www/pytreedb/webserver/')
sys.path.insert(0, '/var/www/pytreedb/')
from pytreedb_server.__main__ import app as application
```

6) Create a new environment file `/var/www/pytreedb/webserver/.env` and fill out the following parameters:
```
CONN_URI = ""
CONN_DB = ""
CONN_COL = ""

PYTREEDB_FILENAME="/var/www/pytreedb/syssifoss.db"
PYTREEDB_DOWNLOAD=""
```
See the above section for details on the parameters. The `PYTREEDB_FILENAME` needs to be writable by the web user (typically `www-data`). When running for the first time, it might be neccessary to download data using `PYTREEDB_DOWNLOAD`. 

7) Restart apache and check the status:
```
sudo systemctl restart apache2
systemctl status apache2.service
```

8) Navigate to http://127.0.0.1/ and check if everything works as expected.

In case of any changes (e.g. in the `.env`-File), reload apache2 as in step 7. If you used the `PYTREEDB_DOWNLOAD`, make sure to remove it again **and** reload the server, otherwise the database will be downloaded with every http request.

See https://flask.palletsprojects.com/en/2.0.x/deploying/ for other deployment options.


## Usage
In the "Get tree by index" search box, you can directly search for a tree according to its index.

In the "Search the DB" area, we predefined following filters:

| Filter  | Corresponding fields|
| ------- |-------------|
| Species | properties.species |
| Mode    | properties.data.mode |
| Canopy  | properties.data.canopy_condition |
| Quality | properties.data.quality |
| Source  | properties.measurements.source |
| DBH     | properties.measurements.DBH_cm |
| Height  | properties.measurements.height_m |
| CrownDia. | properties.measurements.mean_crown_diameter_m |

The filters have the default logic operator AND. You can toggle it between AND/OR by clicking on the preceding button of each filter.

We also allow brackets with a depth of 3. By moving a filter to the right, a bracket will be added to embrace the previous filter with the current filter. If you are still unfamiliar to our search interface and not sure if you are configuring the search correctly, just press "Update Preview" button to check if it aligns to your desired query.

You can export your query as a Json file to save to local, and import such a query for future use. Clicking on the "Permalink" button will also copy a link to your current query.


## API

You can access the API of our example server http://pytreedb.geog.uni-heidelberg.de/ with the following key presented in the QR code:

<img src="pytreedb_server/static/img/QR.png"/>

Scan the QR code and save the key. Set the X-Api-Key value with the key in your request header, otherwise your request would not be authorized. 

If you are using curl:
```
curl -v -H "X-Api-Key:{api key here}" {URL here}
```

If you are using API platforms, for example Postman, select "API Key" from the authorization types, and set the key name to "X-Api-Key".


GET methods:

| Request  | Description |
| ------- |-------------|
| /stats | The number of trees and species in DB |
| /listspecies | Unique species names in DB |
| /sharedproperties | A list of all object.properties that are shared among all objects |
| /getitem/\<index> | Get a specific tree by its index |
| /download/exportcollection/\<query> | Generate a feature collection of all trees from query results |
| /download/lazlinks/tree/\<index> | Get a list of point-cloud-URLs for a tree by its index |
| /download/lazlinks/\<query> | Get a list of point-cloud-URLs for all trees from query results |
| /download/exportcsv/\<query> | Get csv files containing information of all trees from query results |


POST methods:

| Request  | Description | Example Message|
| ------- |-------------|-------------|
| /search | Search based on a given query. Returns a Json objects containing search results |  {"properties.species": "Abies alba"} |
| /search/wssearch | This endpoint is created only for search requests from the frontend UI in order to improve site performance |  {"properties.species": "Abies alba", "limit": 10, "nthEntrySet": 3, "getCoords": false} |

Note: all \<query> parameters in GET methods should be encoded with base64.

See [example_queries](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/examples/example_queries.py) for more examples on how to query.
