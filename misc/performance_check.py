#Compute performance for database queries
# B. Höfle
##########################################

#--------------------- CONFIG #---------------------
cfg_path_to_dbfile_small = r'D:\tmp\SYSSIFOSS\syssifoss_small.db'
cfg_path_to_dbfile_large = r'D:\tmp\SYSSIFOSS\syssifoss_large.db'
cfg_url_to_jsons =  r'https://heibox.uni-heidelberg.de/f/fc5e3cc8d93d4e0ca53b/?dl=1'
#--------------------- /CONFIG #---------------------

#load modules
import pytreedb.db as pytreedb
import sys
import time
import cProfile
import os.path

def create_data_set(dbfile_output,  replications=2):
    mydb = pytreedb.PyTreeDB(dbfile=dbfile_output)
    for i in range (0,replications):
        mydb.import_data(cfg_url_to_jsons, overwrite=False)
    print("Big pytreedb %s generation with %s tree objects"  %(dbfile_output, mydb.get_stats()))
    return mydb

def andQuery(li):
    return mydb.inner_join(procSubquery(li[1:]))
def orQuery(li):
    return mydb.outer_join(procSubquery(li))
def procSubquery(li):
    res = []
    for subQuery in li:
        if isinstance(subQuery, str):  # if subQuery not nested
            kv = subQuery.split(":")
            res.append(mydb.query(kv[0], kv[1]))
        elif type(subQuery) == list and subQuery[0] == "and":  # if nested AND query
            res.append(andQuery(subQuery))
        else:  # if nested OR query
            res.append(orQuery(subQuery))
    return res

def retrievalTest():
    start_time = time.time()
    mydb.get_stats()
    print("Get stats             --- %s seconds ---" % (time.time() - start_time))
    
    start_time = time.time()
    mydb.query('species', 'abies')
    print("Query species         --- %s seconds ---" % (time.time() - start_time))
    
    start_time = time.time()
    query = [[["and","species:abies alba","mode:uls"]]]
    print(len(orQuery(query)))
    print("Simulate backend query --- %s seconds ---" % (time.time() - start_time))


#Create database files if they not yet exist
if not os.path.isfile(cfg_path_to_dbfile_small):
    create_data_set(cfg_path_to_dbfile_small, 1)

if not os.path.isfile(cfg_path_to_dbfile_large):
    create_data_set(cfg_path_to_dbfile_large, 100)

sys.exit()

mydb = pytreedb.PyTreeDB(dbfile=cfg_path_to_dbfile_small)
print("################# SMALL DATA ###################")
print(mydb.get_stats())
cProfile.run('retrievalTest()')


print("################# BIG DATA ###################")
mydb = pytreedb.PyTreeDB(dbfile=cfg_path_to_dbfile_large)
print(mydb.get_stats())
cProfile.run('retrievalTest()')

sys.exit()






