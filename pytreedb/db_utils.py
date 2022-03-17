import re
import sys
import hashlib  # importing the hashlib module
import tempfile
import ssl
import urllib
import urllib.request
import zipfile
from operator import *
import datetime


def flatten_json(y):
    """
    The code recursively extracts values out of the object into a flattened dictionary.
    json_normalize can be applied to the output of flatten_object to produce a python dataframe
       Source: https://towardsdatascience.com/flattening-json-objects-in-python-f5343c794b10
       Example:
           flat = flatten_json(sample_object2)
           json_normalize(flat)
    """
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out


def gen_dict_extract(key_, dict_):
    """
    Returns all values for the provided key in dict
    Source: https://stackoverflow.com/questions/9807634/find-all-occurrences-of-a-key-in-nested-dictionaries-and-lists
    """
    if hasattr(dict_, 'items'):
        for k, v in dict_.items():
            if k == key_:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract(key_, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract(key_, d):
                        yield result


def gen_dict_extract_regex(key_, dict_, regex_):
    """ Returns all values for the provided key and a value search string provided as regular expression in dict """
    if hasattr(dict_, 'items'):
        for k, v in dict_.items():
            if v is None:
                continue
            if k == key_ and re.search(regex_, v, re.IGNORECASE) is not None:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract_regex(key_, v, regex_):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract_regex(key_, d, regex_):
                        yield result


def gen_dict_extract_exact(key_, dict_, exact_):
    """ Returns all values for the provided key and a exact comparison of value search string"""
    if hasattr(dict_, 'items'):
        for k, v in dict_.items():
            if k == key_ and v == exact_:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract_exact(key_, v, exact_):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract_exact(key_, d, exact_):
                        yield result


def gen_dict_extract_numeric_comp(key_, dict_, exact_, operator_):
    """
    Returns all values for the provided key and a comparison of the numeric value
    Possible operators (see: ): https://docs.python.org/3.9/library/operator.html
        lt(a, b)
        le(a, b)
        eq(a, b)
        ne(a, b)
        ge(a, b)
        gt(a, b)
   """

    if hasattr(dict_, 'items'):
        for k, v in dict_.items():
            if k == key_ and operator_(float(v), exact_) is True:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract_numeric_comp(key_, v, exact_, operator_):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract_numeric_comp(key_, d, exact_, operator_):
                        yield result


def gen_dict_extract_date_comp(key_, dict_, date_, operator_):
    """
    Returns all values for the provided key and a comparison of the date provided as date object of datetime module
    """

    if hasattr(dict_, 'items'):
        for k, v in dict_.items():
            try:
                v_date_parts = v.split("-")
                v_date = datetime.date(int(v_date_parts[0]), int(v_date_parts[1]), int(v_date_parts[2]))
                if k == key_ and operator_(v_date, date_) is True:
                    yield v
            except:
                pass
            if isinstance(v, dict):
                for result in gen_dict_extract_date_comp(key_, v, date_, operator_):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract_date_comp(key_, d, date_, operator_):
                        yield result


def hash_file(filename):
    """
    This function returns the SHA-1 hash of the file passed into it
    [source: https://www.programiz.com/python-programming/examples/hash-file}
    """

    # make a hash object
    h = hashlib.sha1()

    # open file for reading in binary mode
    with open(filename, 'rb') as file:
        # loop till the end of the file
        chunk = 0
        while chunk != b'':
            # read only 1024 bytes at a time
            chunk = file.read(1024)
            h.update(chunk)

    # return the hex representation of digest
    return h.hexdigest()


def download_extract_zip_tempdir(url):
    """This function downloads a ZIP file and extracts it to a temporary directory
    - Input: URL
    - Return: full path to directory with extracted files """
    zip_temp_file = tempfile.NamedTemporaryFile().name
    zip_temp_dir = tempfile.TemporaryDirectory().name
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib.request.urlretrieve(url, zip_temp_file)
    # unzip dataset
    zip_ref = zipfile.ZipFile(zip_temp_file, 'r')
    zip_ref.extractall(zip_temp_dir)
    zip_ref.close()
    return zip_temp_dir


def download_file_to_tempdir(url):
    """This function downloads a  file and puts it to a temporary directory
    - Input: URL
    - Return: full path to file """
    temp_file = tempfile.NamedTemporaryFile().name
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib.request.urlretrieve(url, temp_file)
    return temp_file


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.
    - question: String is the query that's shown to the user in shell
    - default:String is the presumed answer if the user just hits <Enter>
    The return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    prompt = " [Y/n] "

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")
