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
from urllib.error import URLError
import socket
from ._types import PathLike, URL, DateString
from typing import Iterator


def flatten_json(y: dict) -> dict:
    """
    The code recursively extracts values out of the object into a flattened dictionary.
    json_normalize can be applied to the output of flatten_object to produce a python dataframe
    Source: https://towardsdatascience.com/flattening-json-objects-in-python-f5343c794b10
    Example:
        flat = flatten_json(sample_object2)
        json_normalize(flat)
    :param dict y: A dictionary
    :return: flattened dictionary
    """
    out = {}

    def flatten(x, name=""):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + "_")
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + "_")
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out


def gen_dict_extract(key_: str, dict_: dict) -> Iterator:
    """
    Returns all values for the provided key in dict
    Source: https://stackoverflow.com/questions/9807634/find-all-occurrences-of-a-key-in-nested-dictionaries-and-lists
    :param str key_:
    :param dict dict_:
    :return:
    """
    if hasattr(dict_, "items"):
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


def gen_dict_extract_regex(key_: str, dict_: dict, regex_: str) -> Iterator:
    """
    Returns all values for the provided key and a value search string provided as regular expression in dict
    :param str key_:
    :param dict dict_:
    :param str regex_:
    :return:
    """
    if hasattr(dict_, "items"):
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


def gen_dict_extract_exact(key_: str, dict_: dict, exact_: str) -> Iterator:
    """
    Returns all values for the provided key and a exact comparison of value search string
    :param str key_:
    :param dict dict_:
    :param str exact_:
    :return:
    """
    if hasattr(dict_, "items"):
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


def gen_dict_extract_numeric_comp(key_: str, dict_: dict, exact_: str, operator_: str) -> Iterator:
    """
    Returns all values for the provided key and a comparison of the numeric value
    Possible operators (see: ): https://docs.python.org/3.9/library/operator.html
        lt(a, b)
        le(a, b)
        eq(a, b)
        ne(a, b)
        ge(a, b)
        gt(a, b)

    :param str key_:
    :param dict dict_:
    :param str exact_:
    :param str operator_:
    :return:
    """

    if hasattr(dict_, "items"):
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


def gen_dict_extract_date_comp(key_: str, dict_: dict, date_: DateString, operator_: str) -> Iterator:
    """
    Returns all values for the provided key and a comparison of the date provided as date object of datetime module

    :param str key_:
    :param dict dict_:
    :param DateString date_:
    :param str operator_:
    :return:
    """

    if hasattr(dict_, "items"):
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


def hash_file(filename: PathLike) -> str:
    """
    This function returns the SHA-1 hash of the file passed into it
    [source: https://www.programiz.com/python-programming/examples/hash-file]
    :param PathLike filename: Path to the file for which to return the SHA-1 hash
    :return: SHA-1 hash
    :rtype: str
    """

    # make a hash object
    h = hashlib.sha1()

    # open file for reading in binary mode
    with open(filename, "rb") as file:
        # loop till the end of the file
        chunk = 0
        while chunk != b"":
            # read only 1024 bytes at a time
            chunk = file.read(1024)
            h.update(chunk)

    # return the hex representation of digest
    return h.hexdigest()


def download_extract_zip_tempdir(url: URL) -> PathLike:
    """
    This function downloads a ZIP file and extracts it to a temporary directory

    :param URL url: URL to zip file
    :return: full path to directory with extracted files
    :rtype: PathLike

    """
    zip_temp_file = tempfile.NamedTemporaryFile().name
    zip_temp_dir = tempfile.TemporaryDirectory().name
    ssl._create_default_https_context = ssl._create_unverified_context
    try:
        urllib.request.urlretrieve(url, zip_temp_file)
    except (socket.gaierror, urllib.error.URLError) as err:
        raise ConnectionError(f"Could not download {url} due to {err}\nThe URL you provided might be corrupt.")
    # unzip dataset
    try:
        zip_ref = zipfile.ZipFile(zip_temp_file, "r")
    except zipfile.BadZipFile as e:
        raise zipfile.BadZipFile(f"Problem reading zip file from URL: {e}")
    zip_ref.extractall(zip_temp_dir)
    zip_ref.close()
    return zip_temp_dir


def download_file_to_tempdir(url: URL) -> PathLike:
    """
    This function downloads a file and puts it to a temporary directory

    :param URL url: URL fo the file to download
    :return: full path to temporary directory
    :rtype: PathLike

    """
    temp_file = tempfile.NamedTemporaryFile().name
    ssl._create_default_https_context = ssl._create_unverified_context
    try:
        urllib.request.urlretrieve(url, temp_file)
    except (socket.gaierror, urllib.error.URLError) as err:
        raise ConnectionError(f"Could not download {url} due to {err}\nThe URL you provided might be corrupt.")
    return temp_file


def query_yes_no(question: str, default: str = "yes") -> bool:
    """
    Ask a yes/no question via raw_input() and return their answer.

    :param str question: query that's shown to the user in shell
    :param str default: presumed answer if the user just hits <Enter>
    :return: True for "yes" or False for "no"
    :rtype: bool

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


def write_list_to_csv(outfile_name: str, content_list: list, none_str: str = "") -> str:
    """
    Write 2D list to CSV file.

    :param str outfile_name: Name of the output file
    :param list content_list: List to write to CSV
    :param none_str: String to write for NaN values
    :return: Name of output file
    :rtype: str

    """
    try:
        with open(outfile_name, "w") as f:
            for row in content_list:
                f.write("%s\n" % ",".join(none_str if col is None else str(col) for col in row))
        return outfile_name
    except:
        print(f"Could not write CSV file {outfile_name}. Check path and file write permissions.")
        return None
