import sys
import shutil
import argparse
import urllib.request
from pathlib import Path, PurePath
from urllib.parse import urlparse

parser = argparse.ArgumentParser()
parser.add_argument("-input", required=True, help="path of the input text file containing urls")
parser.add_argument("-output", required=True, help="path to the download destination directory")
args = parser.parse_args()
source_file = args.input 
output_folder = args.output

def download(urls, dest_folder):
    """
    Downloads point clouds (.laz) data from a list of source URLs

    :param list[str] urls: list of URLs
    :param str dest_folder: destination folder to save data
    """
    for url in urls:
        filename = PurePath(urlparse(url).path).name  # extract file name from the url
        file_path = PurePath(dest_folder).joinpath(filename)
        # download the file from url and save locally
        with urllib.request.urlopen(url) as response, open(file_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            print("saving to", Path(file_path).resolve())

if __name__ == '__main__':
    try:
        f = open(source_file, "r")
    except OSError:
        print(f"Error: Could not open file: \"{source_file}\"")
        print("-- Original error follows below --")
        raise
    
    # create output folder if it doesn't exist yet
    if not Path(output_folder).exists():
        Path(output_folder).mkdir()
        print(f"\"{output_folder}\" created")

    print(f"Input file path: \"{source_file}\" \nOutput directory path: \"{output_folder}\"")

    with f:  # read input file
        try:
            urls = f.read().split(",")     # save content into a list of urls
        except:
            print(f"Error: Could not read file: \"{source_file}\"")
            print("-- Original error follows below --")
            raise

        download(urls, output_folder)  # download data to the output folder
