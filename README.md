# pytreedb

`pytreedb` is a 🐍 Python software package providing an object-based database to handle vegetation tree objects that were captured as 3D point clouds. The main objective is to provide a Python library which enables the view of trees as objects by enabling the storage and sharing of single tree-based point clouds and all relevant (forest intentory) tree measurements. The data includes all tree related information, measurements, metadata, geoinformation and also links to the 3D point clouds as LAS. As `GeoJSON` is used as data format to provide all tree-related information, exchange and visualization with other software (e.g. GIS) and also modification of the datasets is straightforward.

`pytreedb` can be used as 
1. a standard Python library for usage in your scripts during runtime and 
2. it can also be used as a server application using the [Flask](https://pypi.org/project/Flask/) web application framework. 

[MongoDB](https://www.mongodb.com/) is used as database backend via the [PyMongo](https://pypi.org/project/pymongo/) driver. This enables scaling to large datasets, e.g. connecting to [MongoDB Atlas Cloud](https://www.mongodb.com/cloud/atlas) for big datasets.

## Main Features



## 💻 Download and Installation

### Installation
Install and update using [pip](https://pypi.org/):

`$ pip install -U pytreedb`

### Using Anaconda / Conda Environment
Simply use the given Conda environment file [environment.yml](environment.yml) provided in this distribution.

`$ conda env create --file environment.yml`

### Connect to MongoDB
xxx
Install 

### Known Issues
- add here

### Software Dependencies

xx

## ℹ Documentation

As a starting point, please have a look to the [examples](examples) and [notebooks](Jupyter Notebooks) available in the repository. Each of the subfolders contains a readme.md for further details.

==> _CREATE VIDEO or GIFs of usage as code (notebook slideshow) and as server on 3DGeo Youtube and put here._

### Use the pytreedb class
Usage: 


### Run it as a server
Usage from main directory in command line:
```
set FLASK_APP=webserver/main.py
python -m flask run
```

### GeoJSON Template

x

## Test Data
xxx

## Citation
Please cite the following publication when using pytreedb in your research and reference the appropriate release version. All releases of pytreedb are listed on Zenodo where you will find the citation information including DOI.

```
article{pytreedb,
author = {Bernhard Höfle and Jiani Qu and Lukas Winiwarter and Hannah Weiser and Jannika Schäfer and Fabian E. Fassnacht}
title = {pytreedb: library for point clouds of tree vegetation objects},
journal = {The Journal of Open Source Software},
year = {2022},
number = {},
volume = {-},
doi = {-},
url = {-},
} 
 ```
## Funding / Acknowledgements
The initial software development was supported by the DFG - German Research Foundation (Grant no. 411263134) within the research project [SYSSIFOSS](https://uni-heidelberg.de/syssifoss).

## Contact / Bugs / Feature Requests

You think you have found a bug or have specific request for a new feature. Please open a new issue in the online code repository on Github. Also for general questions please use the issue system. 

Scientific requests can be directed to the [3DGeo Research Group Heidelberg](https://uni-heidelberg.de/3dgeo) and its respective members.

## 📜 License

See [LICENSE.md](LICENSE.md)
