from pyinaturalist import *
import pandas as pd
from pandas import json_normalize
from pyinaturalist_convert import *
from pyinaturalist import get_observations
from pandas import json_normalize
import requests
import os, getpass
import time
import format_module
from dotenv import load_dotenv
import re
import numpy as np
import json

load_dotenv()
import plotly



# These lines allows to make sure that we are placed at the repo directory level 

from pathlib import Path

p = Path(__file__).parents[1]
print(p)
os.chdir(p)


data_out_path = './data/out/'

output_filename = 'test_inat_output_current'
filename_suffix = 'csv'
path_to_output_file = os.path.join(data_out_path, output_filename + "." + filename_suffix)


# import env variable
access_token=os.getenv('ACCESS_TOKEN')


response = get_observations(
    # user_id='pmallard',
    project_id=130644,
    page='all',
    per_page=300,
    #access_token=access_token
)


pprint(response)

df = to_dataframe(response)

df.info()

# Before exporting we move the id column to the beginning since it is needed to be at this position to be detected as a PK in airtbale or siomnilar dbs

# shift column 'id' to first position
first_column = df.pop('id')
  
# insert column using insert(position,column_name,
# first_column) function
df.insert(0, 'id', first_column)

#formatting of data
format_module.location_formatting(df,'location','swiped_loc')
format_module.dbgi_id_extract(df)

# We keep the table 
df.to_csv(path_to_output_file, index = False)


#update the database using update_db.py script
script = './src/update_db.py'
exec(open(script).read())

