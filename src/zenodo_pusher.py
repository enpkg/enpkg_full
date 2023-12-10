# We work with https://github.com/cthoyt/zenodo-client
# Install using pip install git+ 
# pip install git+https://github.com/cthoyt/zenodo-client.git


from zenodo_client import Creator, Metadata, ensure_zenodo

# Define the metadata that will be used on initial upload
data = Metadata(

    title='lc_ms_method_params',
    upload_type='dataset',
    description='Test upload of a dataset',
    creators=[
        Creator(
            name='Allard, Pierre-Marie',
            affiliation='University of Fribourg',
            orcid='0000-0003-3389-2191',
        ),
    ],
)


res = ensure_zenodo(
    key='lc_ms_method_params_01',  # this is a unique key you pick that will be used to store
                  # the numeric deposition ID on your local system's cache
    data=data,
    paths=[
        '/home/allardpm/git_repos/ENPKG/enpkg_full/data/input/enpkg_toy_dataset/metadata/lcms_method_params.txt',
    ],
    sandbox=False,  # remove this when you're ready to upload to real Zenodo
)

from pprint import pprint

pprint(res.json())



from zenodo_client import Zenodo
zenodo = Zenodo(sandbox=True)


from zenodo_client import update_zenodo, get_record


# The ID from your deposition
SANDBOX_DEP_ID = '10156827'

# Paths to local files. Good to use in combination with resources that are always
# dumped to the same place by a given script
paths = [
    # os.path.join(DATABASE_DIRECTORY, 'alts_sample.tsv')
    '/home/allardpm/git_repos/ENPKG/enpkg_full/data/input/enpkg_toy_dataset/metadata/lcms_method_params.txt',
]


# Don't forget to set the ZENODO_API_TOKEN environment variable or
# any valid way to get zenodo/api_token from PyStow.
update_zenodo(SANDBOX_DEP_ID, paths, sandbox=False)

record = zenodo.get_record(SANDBOX_DEP_ID)


from pprint import pprint

pprint(record.json())


zenodo.update(SANDBOX_DEP_ID, paths)




OOH_NA_NA_RECORD = '10156827'
new_record = zenodo.get_latest_record(OOH_NA_NA_RECORD)


import pystow


apikey_sandbox=pystow.get_config("zenodo", "sandbox_api_token", raise_on_missing=True)
# apikey=pystow.get_config("zenodo", "zenodo_api_token", raise_on_missing=True)




