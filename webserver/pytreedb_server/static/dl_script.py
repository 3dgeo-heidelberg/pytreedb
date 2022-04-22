import os

source_file = None
output_folder = None

if source_file is None:
    source_file = input("Enter the path of the point cloud URLs:")

if output_folder is None:
    output_folder = input("Enter the output directory:")

f = open(source_file, "r")
urls = f.read().split(",")

def download(urls, dest_folder):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)