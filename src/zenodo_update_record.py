import requests
import os
import json 
from tqdm import tqdm

ACCESS_TOKEN = ''
path_to_files = os.path.normpath('/Users/arnaudgaudry/Desktop/vgf_individuals/')


results = requests.get('https://zenodo.org/api/records/',
                  params={'communities':'enpkg',
                          'size':'2000'})
record_to_keep = []
for record in results.json()['hits']['hits']:
    if 'Individual .ttl files for plate' in record['metadata']['title']:
        record_to_keep.append({record['metadata']['title']:record['id']})

plate_records = []
for dic in record_to_keep:
    new_key = str(dic.keys()).split(' ')[-2]
    plate_records.append((new_key, str(list(dic.values())[0])))


# Edit record
for plate_record in plate_records:
    plate = plate_record[0]
    id = plate_record[1]
    r = requests.post(f'https://zenodo.org/api/deposit/depositions/{id}/actions/newversion',
                    params={'access_token': ACCESS_TOKEN})
    bucket_url = r.json()["links"]["bucket"]

    old_files_id = []
    for existing_file in r.json()['files']:
        old_files_id.append(existing_file['id'])
    #Remove old files
    for old_file_id in old_files_id:
        r = requests.delete(f'https://zenodo.org/api/deposit/depositions/{id}/files/{old_file_id}',
                    params={'access_token': ACCESS_TOKEN})


    # get the files from this plate
    plate_files = []
    for file in os.listdir(path_to_files):
        if plate in file:
            plate_files.append(file)
    
    # add the files to the record
    params = {'access_token': ACCESS_TOKEN}

    for file in plate_files:
        path_file = os.path.join(path_to_files, file)
        with open(path_file, "rb") as fp:
            r = requests.put(
                "%s/%s" % (bucket_url, file),
                data=fp,
                params=params,
            )

    data = {
            'metadata': {
                'version':'1.0.1'
                }
        }
    headers = {"Content-Type": "application/json"}
    r = requests.put(f'https://zenodo.org/api/deposit/depositions/{id}',
                    params={'access_token': ACCESS_TOKEN}, data=json.dumps(data),
                    headers=headers)




for plate in tqdm(['VGF138', 'VGF139', 'VGF140', 'VGF141', 'VGF142',
              'VGF143', 'VGF144', 'VGF145', 'VGF146', 'VGF147',
              'VGF150', 'VGF151', 'VGF152', 'VGF153', 'VGF154',
              'VGF155', 'VGF156', 'VGF157', 'VGF158', 'VGF159']):
        
    # Create new empty upload fir each plate
    headers = {"Content-Type": "application/json"}
    params = {'access_token': ACCESS_TOKEN}
    r = requests.post('https://zenodo.org/api/deposit/depositions',
                    params=params,
                    json={},
                    headers=headers)
    bucket_url = r.json()["links"]["bucket"]
    id = r.json()['id']
    
    # get the files from this plate
    plate_files = []
    for file in os.listdir(path_to_files):
        if plate in file:
            plate_files.append(file)
    
    # add the files to the record
    for file in plate_files:
        path_file = os.path.join(path_to_files, file)
        with open(path_file, "rb") as fp:
            r = requests.put(
                "%s/%s" % (bucket_url, file),
                data=fp,
                params=params,
            )

    # Add the metadata to the record
    data = {
        'metadata': {
            'title': f'Individual .ttl files for plate {plate} samples',
            'upload_type': 'dataset',
            'description': f'Individual .ttl files for plate {plate} samples processed using the ENPKG framework',
            'creators': [{'name':'Gaudry, Arnaud',
                          'affiliation': 'University of Geneva',
                          'orcid': '0000-0002-3648-7362'},
                          {'name':'Pagni, Marco',
                          'affiliation': 'Swiss Institute of Bioinformatics',
                          'orcid': '0000-0001-9292-9463'},
                          {'name':'Mehl, Florence',
                          'affiliation': 'Swiss Institute of Bioinformatics',
                          'orcid': '0000-0002-9619-1707'},
                          {'name':'Allard, Pierre-Marie',
                          'affiliation': 'University of Fribourg',
                          'orcid': '0000-0003-3389-2191'}],
            'access_right': 'open',
            'license': 'cc-zero',
            'keywords': ['knowledge graphs', 'enpkg', 'natural products'],
            'communities' : [{'identifier':'enpkg'}],
            'version':'1.0.0',
            'language':'eng'
        }
    }
    r = requests.put(f'https://zenodo.org/api/deposit/depositions/{id}',
                    params={'access_token': ACCESS_TOKEN}, data=json.dumps(data),
                    headers=headers)

# Retrieve some records
r = requests.get('https://zenodo.org/api/records/',
                  params={'communities':'enpkg',
                          'size':'2000'})
results = r.json()
record_to_keep = []
for record in results['hits']['hits']:
    if 'Individual .ttl files for plate' in record['metadata']['title']:
        record_to_keep.append(record['metadata']['doi'])
