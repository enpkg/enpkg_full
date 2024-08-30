import pystow
import requests
import os
import json
from tqdm import tqdm


ACCESS_TOKEN_SANDBOX = pystow.get_config(
    "zenodo", "sandbox_api_token", raise_on_missing=True
)


path_to_files = os.path.normpath("/Users/arnaudgaudry/Desktop/vgf_individuals_v2/")


plate = "VGF138"

for plate in tqdm(
    [
        "VGF138",
        "VGF139",
        "VGF140",
        "VGF141",
        "VGF142",
        "VGF143",
        "VGF144",
        "VGF145",
        "VGF146",
        "VGF147",
        "VGF150",
        "VGF151",
        "VGF152",
        "VGF153",
        "VGF154",
        "VGF155",
        "VGF156",
        "VGF157",
        "VGF158",
        "VGF159",
    ]
):

    # Create new empty upload fir each plate
    headers = {"Content-Type": "application/json"}
    params = {"access_token": ACCESS_TOKEN_SANDBOX}
    r = requests.post(
        "http://sandbox.zenodo.org/api/deposit/depositions",
        params=params,
        json={},
        headers=headers,
    )
    bucket_url = r.json()["links"]["bucket"]
    id = r.json()["id"]

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
        "metadata": {
            "title": f"Individual .ttl files for plate {plate} samples v1.0.1",
            "upload_type": "dataset",
            "description": f"Individual .ttl files for plate {plate} samples processed using the ENPKG framework",
            "creators": [
                {
                    "name": "Gaudry, Arnaud",
                    "affiliation": "University of Geneva",
                    "orcid": "0000-0002-3648-7362",
                },
                {
                    "name": "Pagni, Marco",
                    "affiliation": "Swiss Institute of Bioinformatics",
                    "orcid": "0000-0001-9292-9463",
                },
                {
                    "name": "Mehl, Florence",
                    "affiliation": "Swiss Institute of Bioinformatics",
                    "orcid": "0000-0002-9619-1707",
                },
                {
                    "name": "Allard, Pierre-Marie",
                    "affiliation": "University of Fribourg",
                    "orcid": "0000-0003-3389-2191",
                },
            ],
            "access_right": "open",
            "license": "cc-zero",
            "keywords": ["knowledge graphs", "enpkg", "natural products"],
            "communities": [{"identifier": "enpkg"}],
            "version": "1.0.1",
            "language": "eng",
        }
    }
    r = requests.put(
        f"https://zenodo.org/api/deposit/depositions/{id}",
        params={"access_token": ACCESS_TOKEN},
        data=json.dumps(data),
        headers=headers,
    )


# Retrieve some records
results = requests.get(
    "https://zenodo.org/api/records/", params={"communities": "enpkg", "size": "2000"}
)
results = r.json()
record_to_keep = []
for record in results["hits"]["hits"]:
    if ("Individual .ttl files for plate" in record["metadata"]["title"]) & (
        "v1.0.1" in record["metadata"]["title"]
    ):
        record_to_keep.append(record["id"])

record_to_keep = []
for record in results.json()["hits"]["hits"]:
    if ("Individual .ttl files for plate" in record["metadata"]["title"]) & (
        "v1.0.1" in record["metadata"]["title"]
    ):
        record_to_keep.append({record["metadata"]["title"]: record["id"]})

plate_records = []
for dic in record_to_keep:
    new_key = str(dic.keys()).split(" ")[-3]
    plate_records.append((new_key, str(list(dic.values())[0])))


# Create new empty upload for each plate
headers = {"Content-Type": "application/json"}
params = {"access_token": ACCESS_TOKEN_SANDBOX}

# URL for the Zenodo Sandbox API
url = "http://sandbox.zenodo.org/api/deposit/depositions"

# Make the POST request
response = requests.post(url, params=params, json={}, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    if "links" in data and "bucket" in data["links"] and "id" in data:
        bucket_url = data["links"]["bucket"]
        deposition_id = data["id"]
        print("Deposition created successfully.")
        print("Bucket URL:", bucket_url)
        print("Deposition ID:", deposition_id)
    else:
        print("Response JSON does not contain expected data.")
else:
    print("Failed to create deposition.")
    print("Status Code:", response.status_code)
    print("Response:", response.text)
