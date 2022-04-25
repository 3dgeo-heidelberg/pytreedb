import os
import urllib.request
import shutil

source_file = None  # location of the .txt file containing point cloud urls
output_folder = None  # local folder to save the files under

def download(urls, dest_folder):
    """
    Downloads point clouds (.laz) data from a list of source URLs

    :param list[str] urls: list of URLs
    :param str dest_folder: destination folder to save data
    """
    # create folder if it doesn't exist yet
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    for url in urls:
        filename = url.split('/')[-1]
        file_path = os.path.join(dest_folder, filename)
        # download the file from url and save locally
        with urllib.request.urlopen(url) as response, open(file_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            print("saving to", os.path.abspath(file_path))

if __name__ == '__main__':
    # Prompt user to enter paths if not given
    if source_file is None:
        source_file = input("Enter the path of the point cloud URLs:").strip('\"')
    if output_folder is None:
        output_folder = input("Enter the output directory:").strip('\"')

    with open(source_file, "r") as f:  # read input file
        urls = f.read().split(",")     # save content into a list of urls
        download(urls, output_folder)  # download data to the output folder
