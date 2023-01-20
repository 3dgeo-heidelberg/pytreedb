"""

`pytreedb`: Object-based Python library and simple interface to access and share information and 3D point clouds of plant objects (e.g. trees)
==========

pytreedb has three main components and usage directions:

   1. Python library: In case you need to access the tree database in your Python scripts during runtime of data processing and analysis.
   2. REST API: In case you want to provide your datasets to any software over a REST API. The pytreedb server application is using the Flask framework for local(host) usage and we provide instructions to setup for production deployment with Apache WGSI.
   3. Web frontend: In case you want to share your valuable tree data to the community. Based on the REST API we showcase in this repository how a Web frontend can be easily implemented, which provides several query options, data export and also map views of query results. A showcase presenting the tree data of Weiser et al. 2022 is given on http://pytreedb.geog.uni-heidelberg.de/.

The `PyTreeDB` class is the starting point and the core component. It is responsible, e.g., for
    - data import, data export, data validation, automatic sync with MongoDB
    - all kind of queries.

The Python REST interface and all clients, such as the web frontend, simply use the methods and functionality of the Python class.
MongoDB is used as database backend via the PyMongo driver. This enables scaling to large global datasets, e.g. connecting to MongoDB Atlas Cloud for big datasets.

"""

from __future__ import absolute_import

__version__ = "1.0.0.post1"
name = "pytreedb"

import pytreedb.db
import pytreedb.db_conf
import pytreedb.db_utils

