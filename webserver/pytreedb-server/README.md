## Prerequisites
- Python
- pytreedb environment (env yaml to be uploaded)

## Deployment for local dev

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