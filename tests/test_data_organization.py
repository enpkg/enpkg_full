"""Test module to evaluate the current module of the ENPKG workflow."""
from .utils import retrieve_zenodo_data


def test_data_organization():
    """Test whether the data organization is correct."""
    # First, we retrieve the data from Zenodo if we have not done so already.
    # Toy ENPKG dataset is at https://zenodo.org/records/10018590
    retrieve_zenodo_data(record_id="10018590", record_name="enpkg_toy_dataset.zip")


import yaml

p = Path(__file__).parents[1]
os.chdir(p)


# Loading the parameters from yaml file

if not os.path.exists('../params/user.yml'):
    print('No ../params/user.yml: copy from ../params/template.yml and modify according to your needs')
with open (r'../params/user.yml') as file:    
    params_list_full = yaml.load(file, Loader=yaml.FullLoader)

params_list = params_list_full['chemo-info-fetching']

# Parameters can now be accessed using params_list['level1']['level2'] e.g. params_list['options']['download_gnps_job']

sample_dir_path =os.path.normpath(params_list['sample_dir_path'])
sql_path = os.path.join(os.getcwd() + '/output_data/sql_db/' + params_list['sql_name'])
gnps_id = params_list['gnps_id']


