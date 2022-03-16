# pytreedb-Server

This package provides a webserver as a frontend to a `pytreedb` instance.

## Prerequisites
- Python packages:
  - `pytreedb`
  - `flask`
  - `dotenv`
  
## Deployment for local dev
### Setup using `.env`
We use the `dotenv` package to configure the server. There are two different places for configurations:
1) The `.env`-File in the current directory contains options related to `pytreedb`: 
```
# path of the pytreedb package (if not installed via PIP)
PYTREEDB_LOCATION="../pytreedb"
# local filename for database file
PYTREEDB_FILENAME="syssifoss.db"
# if set, download (and overwrite local file) data from this URL
PYTREEDB_DOWNLOAD="https://heibox.uni-heidelberg.de/f/05969694cbed4c41bcb8/?dl=1"
# connection string to mongodb (e.g. 127.0.0.1, or "mongodb+srv://..." if using MongoDB Cloud)
CONN_URI = ""
# database name to connect to
CONN_DB = ""
# collection to connect to
CONN_COL = ""
```
2) The `.flaskenv`-File in the current directory contains options for the Flask webserver, e.g. (for the full
list, refer to the Flask documentation):
```
FLASK_ENV=development
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5001
```

### Configuring pytreedb dataset
The dataset is not a prerequisite. If you don't have the dataset locally, unquote  line 43 in [main.py](main.py), so that the dataset will be downloaded and imported into a "syssifoss.db" for you upon deploying.

If you already have a local `.db` dataset file, change the path in line 42 of [main.py](main.py).

More examples can be found in [example_queries.py](../../examples/example_queries.py).

### Serve the webserver locally
Under the root folder of pytreedb, run:

```
conda activate pytreedb
set FLASK_APP=webserver/main.py
python -m flask run
```

## Deployment for production
Note that Flask is not suitable for production. 
See https://flask.palletsprojects.com/en/2.0.x/deploying/ for deployment options