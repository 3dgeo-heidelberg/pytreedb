# pytreedb-Server

This package provides a webserver as a frontend to a `pytreedb` instance.

<img src="../doc/_static/pytreedb_webserver_home.png" width="85%">

## Prerequisites
- Python packages:
  - `pytreedb`
  - `flask`
  - `dotenv`
  
## Deployment for local dev
### Setup using `.env`
We use the `dotenv` package to configure the server. Both `pytreedb` and `flask` parameters should be written to
the `.env`-File in the current directory: 
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
FLASK_ENV=development
FLASK_SERVER_NAME=0.0.0.0:5001
```

### Configuring pytreedb dataset
The dataset is not a prerequisite. Please follow the instructions after getting Flask to running on your machine.


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