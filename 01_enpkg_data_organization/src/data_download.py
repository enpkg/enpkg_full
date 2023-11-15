import glob
import os
import yaml
from pathlib import Path
from downloaders import BaseDownloader
from downloaders.extractors import AutoExtractor


# def retrieve_zenodo_data():
#     """Retrieve the data from Zenodo."""
#     downloader = BaseDownloader()
#     downloader.download("https://zenodo.org/records/10018590/files/enpkg_toy_dataset.zip?download=1","./data/input/enpkg_toy_dataset.zip")
#     # ALSO EXTRACT ALL OF THE THINGS!
#     extractor = AutoExtractor(delete_original_after_extraction=True)
#     paths = glob("./data/input/**/*.zip", recursive=True)
#     extractor.extract(paths)

# Same function, with Zenodo record id as parameter

def retrieve_zenodo_data(record_id, record_name, output_path):
    """Retrieve the data from Zenodo.
    Parameters
    ----------
    record_id : str
        The Zenodo record ID.
    record_name : str
        The Zenodo record name.
    """
    downloader = BaseDownloader()
    downloader.download(urls = "https://zenodo.org/records/"+str(record_id)+"/files/"+record_name+"?download=1",
    paths = output_path+'/'+record_name)
    # ALSO EXTRACT ALL OF THE THINGS!
    extractor = AutoExtractor(delete_original_after_extraction=True)
    paths = glob.glob(f"{output_path}/**/*.zip", recursive=True)
    extractor.extract(paths)



if __name__ == "__main__":
    os.chdir(os.getcwd())

    p = Path(__file__).parents[1]
    os.chdir(p)

    # Loading the parameters from yaml file

    if not os.path.exists('../params/user.yml'):
        print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
    with open (r'../params/user.yml') as file:    
        params_list_full = yaml.load(file, Loader=yaml.FullLoader)

    params_list = params_list_full['data-download']

    # Parameters can now be accessed using params_list['level1']['level2'] e.g. params_list['options']['download_gnps_job']

  

    # First, we retrieve the data from Zenodo if we have not done so already.
    # Toy ENPKG dataset is at https://zenodo.org/records/10018590
    retrieve_zenodo_data(record_id=params_list['record_id'],
    record_name=params_list['record_name'],
    output_path=os.path.normpath(params_list['output_path'])
    )