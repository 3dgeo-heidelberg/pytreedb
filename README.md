# <img src="https://github.com/3dgeo-heidelberg/pytreedb/blob/main/pytreedb_logo_low.png?raw=true" alt="logo" style="width:200px;"/>

[![License](https://img.shields.io/badge/license-GPLv3%2C%20LGPLv3-blue)](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/LICENSE.md)
[![Documentation Status](https://readthedocs.org/projects/pytreedb/badge/)](https://pytreedb.readthedocs.io)
[![GitHub Workflow Status](https://github.com/3dgeo-heidelberg/pytreedb/actions/workflows/python-app.yml/badge.svg)](https://github.com/3dgeo-heidelberg/pytreedb/actions)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7551310.svg)](https://doi.org/10.5281/zenodo.7551310)

`pytreedb` is a `Python` software package providing an object-based library to provide a simple database interface and REST API of vegetation tree objects that were captured as 3D point clouds. The main objective is to provide a Python library for the storage and sharing of single tree-based point clouds and all relevant (forest inventory) tree measurements. The tree data include all tree related information, measurements, metadata, geoinformation and also links to the 3D point clouds linked in any file format (e.g. LAS/LAZ). `GeoJSON` including all tree-related information is used as data format  for data exchange and visualization with other software (e.g. direct import into most GIS). Thereby view and modification of the tree datasets (*.geojson) is straightforward.

[MongoDB](https://www.mongodb.com/) is used as database backend via the [PyMongo](https://pypi.org/project/pymongo/) driver. This enables scaling to large global datasets, e.g. connecting to [MongoDB Atlas Cloud](https://www.mongodb.com/cloud/atlas) for big datasets. Working only locally using a local MongoDB installation is also possible, if the database is only needed during runtime of data processing and sharing on the Web is not required.

## Main Features

`pytreedb` has three main components and usage directions:

1. **Python library**: In case you need to access the tree database in your Python scripts during runtime of data processing and analysis. 
2. **REST API**: In case you want to provide your datasets to any software over a REST API. The `pytreedb` server application is using the [Flask](https://pypi.org/project/Flask/) framework for local(host) usage and we provide instructions to setup for production deployment with [Apache WGSI](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/webserver#deployment-for-production). Further info on the REST API of `pytreedb` can be found [here](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/webserver#deployment-for-local-dev), e.g. including setup of server and usage of API keys.
3. **Web frontend**: In case you want to share your valuable tree data to the community. Based on the REST API we showcase in this repository how a Web frontend can be easily implemented, which provides several query options, data export and also map views of query results. A showcase presenting the tree data of [Weiser et al. 2022](https://doi.org/10.5194/essd-14-2989-2022) and further [datasets](https://github.com/3dgeo-heidelberg/pytreedb?tab=readme-ov-file#published-test-data) is given on http://pytreedb.geog.uni-heidelberg.de/.


<img src="https://github.com/3dgeo-heidelberg/pytreedb/blob/main/doc/_static/pytreedb_components_details.png?raw=true" alt="overview of the components of pytreedb" width="45%">



The [`PyTreeDB`](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/pytreedb/db.py) class is the starting point and the core component. It is responsible, e.g., for 
- data **import**, data **export**, data validation, automatic sync with MongoDB
- all kind of **queries**. 

The `Python` REST interface and all clients, such as the web frontend, simply use the methods and functionality of the Python class.

The main concept of the `pytreedb` software was explained in a <a href="https://youtu.be/tUBoLCXkpV0?list=PLjb7Qrh6QTH0xh9qTmida6jZEWd938dEO&t=446" target="_blank">scientific talk</a> by Bernhard Höfle at the <a href="https://3dforecotech.eu/">3DForEcoTech</a> Workshop in Prague in 2022:

<a href="https://youtu.be/tUBoLCXkpV0?list=PLjb7Qrh6QTH0xh9qTmida6jZEWd938dEO&t=446" target="_blank"><img src="https://github.com/3dgeo-heidelberg/pytreedb/blob/main/doc/_static/pytreedb_3dforecotech2022_youtube_screenshot.png?raw=true" alt="" width="400" /></a>


## 💻 Download and Installation

### Installation

Install and update using [pip](https://pypi.org/) for 1) core library and 2) server library using the core library:

**1) Core library**

`$ pip install -U pytreedb`

**2) Server library**

`$ pip install -U pytreedb-server`

### Alternative Installation

**Clone this Repo and Use Anaconda Environment**

Clone this repository with `git clone` and use it as your working directory.

Simply use the given `Anaconda` environment file [environment.yml](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/environment.yml) provided in this distribution, which contains all dependencies to run and build resources.

`$ conda env create --file environment.yml --force`

Instead, you can also install the dependencies from the requirements file with pip.

`$ python -m pip install -r requirements.txt`

or the entire package:

`$ python -m pip install .`

Finally, if you want to contribute to the library's development you should also install its additional Python dependencies for testing and documentation building:

`$ python -m pip install -r requirements-dev.txt`

### Connect to MongoDB (localhost / server / Atlas cloud)
`pytreedb` requires a working connection to a `MongoDB` database. It does not matter where the MongoDB is running as connection is simply made via `pymongo` (see code in [examples](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/examples) and our [Jupyter notebooks](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/notebooks)). We successfully tested localhost, server and [MongoDB Atlas cloud](https://www.mongodb.com/basics/mongodb-atlas-tutorial) connections. For your own MongoDB installation, just follow the [official installation instructions](https://docs.mongodb.com/manual/installation/)).

The required **MongoDB connection** with credentials is made with a `.env` file (_yes, the file has no name_) that you place in the folder of your Python scripts or search path. [dotenv](https://pypi.org/project/python-dotenv/) is used for providing credentials - 1) URI to server, 2) database and 3) collection name - outside your source code (see [sample.env](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/sample.env) as template).

Example `.env` file for connection to local MongoDB installation. ℹ️ Replace <database_name> and <collection_name> with your settings:
```
CONN_URI = "mongodb://127.0.0.1:27017/"
CONN_DB = "<database_name>"
CONN_COL = "<collection_name>"
```

Example CONN_URI in `.env` file for connection to MongoDB Atlas cloud where the respective settings need to be replaced with yours:

```
CONN_URI = "mongodb+srv://<username>:<password>@<your_cluster_details>.mongodb.net/<database_name>?retryWrites=true&w=majority"
```

### Software Dependencies

All dependencies (i.e. required third-party Python packages) are listed in the Anaconda [environment.yml](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/environment.yml) definition and can be installed with [conda / pip](https://github.com/3dgeo-heidelberg/pytreedb/tree/main#installation). When creating the conda environment from our definition file, all dependencies are resolved.

## Documentation of Software Usage

### `PyTreeDB` class 🐍
As a starting point, please have a look to the [examples](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/examples) and [Jupyter Notebooks](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/notebooks) available in the repository. Further, each of the subfolders contains a README.md with respective details on the repository section.


### Run it as a API server 💻
In order to provide a REST API to share your tree data you can use `pytreedb` in server mode. After installation of the `pytreedb-server` Python package you can follow the instructions here [webserver/README.md](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/webserver#readme).

### Run it as a web server and frontend
An example web frontend instance is running here: http://pytreedb.geog.uni-heidelberg.de/. The respective instructions and codes to install a webpage via the `pytreedb-server` Python package can be found in the webserver code section of `pytreedb`: [pytreedb/webserver](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/webserver#readme). Web frontend codes can be easily adapted to your needs - see web programming codes in [static](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/webserver/pytreedb_server/static) and [templates](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/webserver/pytreedb_server/templates).

### Use it as via the REST API also from other programming languages (e.g. R stats)
Straightforward access from any programming language is made possible via the REST API. We provide examples scripts for http API access, e.g. for R statistics in [examples_api](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/examples_api). The [R function example](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/examples_api/example.R) allows simple query and also download of the LAZ files for all trees of the query result.


### GeoJSON Format and Template
An example tree is given in [data/geojson/AbiAlb_BR03_01.geojson](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/data/geojson/AbiAlb_BR03_01.geojson?raw=true) and the GeoJSON template for tree objects is defined here [pytreedb/db_conf.py](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/pytreedb/db_conf.py).

The single tree information (incl. URLs to the point clouds) has to be provided as `GeoJSON` file per tree. We use a straightforward format that is a valid GeoJSON and can be opened with any GIS software. The main idea of the pytreedb GeoJSON format is to define a minimum set of tree metadata, which can be extended by any further data that is needed by the user. Thus, it is just required that your GeoJSON file complies with the minimum set to enable import into the database. The [`PyTreeDB`](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/pytreedb/db.py) class offers the method `validate_json` to check the validity of the file. Also the import of files checks the validity automatically and will only import tree objects that are conformal with the defined template. The used [GeoJSON template](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/pytreedb/db_conf.py) can also be modified for your use case and application. Note that modification (e.g. removal of mandatory fields from our template) will - most probably - require modifications for the API and web frontend component. 

## Published Test Data

The test data is provided in [`data`](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/data) as 1) single [GeoJSON files and as ZIP archive](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/data/geojson), and 2) also as serialized and zipped [pytreedb database dump](https://github.com/3dgeo-heidelberg/pytreedb/tree/main/data/db_dump) files that can be directly imported and used to start the API server.

### 1) SYSSIFOSS-Data

We provide metadata (incl. links to point clouds) of 1481 trees that have been captured with airborne (ALS), UAV-borne (ULS) and terrestrial (TLS) laser scanning as well as field inventory data. This data was acquired and processed as part of the DFG project [syssifoss](https://www.geog.uni-heidelberg.de/gis/SYSSIFOSS_en.html) and the trees are located in the forests of Bretten and Karlsruhe (Germany). Please check our data publication for full details:

> Weiser, H., Schäfer, J., Winiwarter, L., Krašovec, N., Fassnacht, F.E. & Höfle, B. (2022): Individual tree point clouds and tree measurements from multi-platform laser scanning in German forests. Earth System Science Data. Vol. 14 (7), pp. 2989-3012. https://doi.org/10.5194/essd-14-2989-2022

The data can be downloaded from PANGAEA: https://doi.org/10.1594/PANGAEA.942856

[<img src="https://github.com/3dgeo-heidelberg/pytreedb/blob/main/doc/_static/syssifoss_data_figure_pc_viz.png?raw=true" width="50%">](https://doi.org/10.5194/essd-14-2989-2022)

For 11 trees, this dataset was extended by labelled versions of the TLS point clouds which have pointwise annotations for the semantic classes leaf and wood. The point clouds can be filtered using the "Labels" filter and are also available from heiDATA.

> Weiser, H., Ulrich, V., Winiwarter, L., Esmorís, A, M. & Höfle, B. (2024): Manually labeled terrestrial laser scanning point clouds of individual trees for leaf-wood separation. heiDATA, V1, https://doi.org/10.11588/DATA/UUMEDI.

[<img src="https://github.com/3dgeo-heidelberg/pytreedb/blob/main/doc/_static/syssifoss_trees_labelled.png?raw=true" width="600">](https://doi.org/10.11588/DATA/UUMEDI)

### 2) Landmark trees in Heidelberg, Germany

Over time, we additionally added two landmark trees scanned in Heidelberg, Germany:
- [Holdermannseiche](https://pytreedb.geog.uni-heidelberg.de/query/eyJiYWNrZW5kUXVlcnkiOnsiJGFuZCI6W3sicHJvcGVydGllcy5tZWFzdXJlbWVudHMuaGVpZ2h0X20iOnsiJGx0IjoyNCwiJGd0IjoyM319LHsicHJvcGVydGllcy5kYXRhLm1vZGUiOiJUTFMifSx7InByb3BlcnRpZXMuc3BlY2llcyI6IlF1ZXJjdXMgcm9idXIifV19LCJmaWx0ZXJzIjpbInNwZWNpZXM6UXVlcmN1cyByb2J1ciIsImhlaWdodDoyMy0yNCIsIm1vZGU6VExTIl0sIm9wZXJhbmRzIjpbIi4iLCJBTkQiLCJBTkQiXSwiYnJhY2tldHMiOlswLDAsMF0sInByZXZpZXdTdHJpbmciOiJcInNwZWNpZXM6UXVlcmN1cyByb2J1clwiIEFORCBcImhlaWdodDoyMy0yNFwiIEFORCBcIm1vZGU6VExTXCIiLCJlbGVtTWF0Y2giOmZhbHNlLCJwcmV2aWV3TGltaXQiOjMsInJlbmRlck1hcmtlcnMiOnRydWV9) (*Quercus robur*), Heiligenberg
- [Giant sequoia](https://pytreedb.geog.uni-heidelberg.de/query/eyJiYWNrZW5kUXVlcnkiOnsicHJvcGVydGllcy5zcGVjaWVzIjoiU2VxdW9pYWRlbmRyb24gZ2lnYW50ZXVtIn0sImZpbHRlcnMiOlsic3BlY2llczpTZXF1b2lhZGVuZHJvbiBnaWdhbnRldW0iXSwib3BlcmFuZHMiOlsiLiJdLCJicmFja2V0cyI6WzBdLCJwcmV2aWV3U3RyaW5nIjoiXCJzcGVjaWVzOlNlcXVvaWFkZW5kcm9uIGdpZ2FudGV1bVwiIiwiZWxlbU1hdGNoIjpmYWxzZSwicHJldmlld0xpbWl0IjozLCJyZW5kZXJNYXJrZXJzIjp0cnVlfQ==) (*Sequoiadendron giganteum*), Arboretum 1

Quick tutorial:

<a href="https://www.youtube.com/watch?v=8SBi5mwDUVU" target="_blank"><img src="https://github.com/3dgeo-heidelberg/pytreedb/blob/main/doc/_static/pytreedb_youtube_tutorial_giant_sequoia.png?raw=true" alt="" width="500" /></a>

### 3) LiPheStream catalogue

LiPheStream is the first external dataset that we added to `pytreedb`. LiPheStream is a time series tree dataset from a permanent laser scanning (PLS) system in Finland. 

> Wittke, S., Campos, M., Ruoppa, L., Echrit, R., Wang, Y., Gołoś, A., Kukko, A., Hyyppä, J. & Puttonen, E. (2024): LiPheStream - A 18-month high spatiotemporal resolution point cloud time series of Boreal trees from Finland. Scientific Data, Vol. 11, 1281. https://doi.org/10.1038/s41597-024-04143-w.

The entire LiPheStream dataset is available from the Finnish Fairdata service: https://doi.org/10.23729/cf81f7f3-faaa-4729-aa1c-aa4dd38951aa

## Citation
Please cite the following publication when using pytreedb in your research and reference the appropriate release version. All releases of pytreedb are listed on Zenodo where you will find the citation information including DOI. 

> Höfle, B., Qu, J., Winiwarter, L., Weiser, H., Zahs, V., Schäfer, J. & Fassnacht, F. E. (2023). pytreedb - library for point clouds of tree vegetation objects (1.0.0). Zenodo. https://doi.org/10.5281/zenodo.7551310

```
@software{hofle_bernhard_2023_7551310,
  author       = {Höfle, Bernhard and
                  Qu, Jiani and
                  Winiwarter, Lukas and
                  Weiser, Hannah and
                  Zahs, Vivien and
                  Schäfer, Jannika and
                  Fassnacht, Fabian E.},
  title        = {{pytreedb - library for point clouds of tree 
                   vegetation objects}},
  month        = jan,
  year         = 2023,
  publisher    = {Zenodo},
  version      = {1.0.0},
  doi          = {10.5281/zenodo.7551310},
  url          = {https://doi.org/10.5281/zenodo.7551310}
}
 ```
## Funding / Acknowledgements
The initial software development was supported by the **DFG - German Research Foundation** (Grant no. 411263134) within the research project [SYSSIFOSS](https://uni-heidelberg.de/syssifoss).

[<img src="https://github.com/3dgeo-heidelberg/pytreedb/blob/main/doc/_static/dfg_logo_englisch_blau_en.gif?raw=true" width="30%">](https://www.dfg.de/en/)

## Contact / Bugs / Feature Requests

You think you have found a bug or have specific request for a new feature. Please open a new issue in the online code repository on Github. Also for general questions please use the issue system. 

Scientific requests can be directed to the [3DGeo Research Group Heidelberg](https://uni-heidelberg.de/3dgeo) and its respective members.

## 📜 License

See [LICENSE.md](https://github.com/3dgeo-heidelberg/pytreedb/blob/main/LICENSE.md)
