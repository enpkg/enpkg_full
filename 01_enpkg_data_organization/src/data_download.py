import glob
import os
import time
import urllib.error
import urllib.request
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

def _download_via_urllib(url, output_file, retries=3, retry_wait_s=5, timeout_s=30):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout_s) as response:
                status = response.getcode()
                if status and status >= 400:
                    raise urllib.error.HTTPError(
                        url, status, f"HTTP {status}", response.headers, None
                    )
                total = response.getheader("Content-Length")
                total = int(total) if total and total.isdigit() else None
                downloaded = 0
                next_report = 10 * 1024 * 1024
                with open(output_file, "wb") as handle:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
                        downloaded += len(chunk)
                        if downloaded >= next_report:
                            if total:
                                pct = downloaded / total * 100
                                print(f"Downloaded {downloaded/1024/1024:.1f} MB ({pct:.1f}%)")
                            else:
                                print(f"Downloaded {downloaded/1024/1024:.1f} MB")
                            next_report += 10 * 1024 * 1024
            return
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(retry_wait_s)
    if last_error is not None:
        raise last_error


def retrieve_zenodo_data(record_id, record_name, output_path, retries=3, retry_wait_s=5):
    """Retrieve the data from Zenodo.
    Parameters
    ----------
    record_id : str
        The Zenodo record ID.
    record_name : str
        The Zenodo record name.
    retries : int
        Number of retries per URL if Zenodo returns a non-200 status.
    retry_wait_s : int
        Seconds to wait between retries.
    """
    os.makedirs(output_path, exist_ok=True)

    output_file = os.path.join(output_path, record_name)
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        # Skip download if the file already exists.
        print(f"Found existing file: {output_file}")
    else:
        downloader = BaseDownloader()
        urls = [
            f"https://zenodo.org/records/{record_id}/files/{record_name}?download=1",
            f"https://zenodo.org/api/records/{record_id}/files/{record_name}/content",
        ]
        last_error = None
        for url in urls:
            try:
                _download_via_urllib(
                    url,
                    output_file,
                    retries=retries,
                    retry_wait_s=retry_wait_s,
                )
                last_error = None
                break
            except (urllib.error.URLError, urllib.error.HTTPError) as exc:
                last_error = exc
        if last_error is not None:
            for url in urls:
                for attempt in range(1, retries + 1):
                    try:
                        downloader.download(urls=url, paths=output_file)
                        last_error = None
                        break
                    except ValueError as exc:
                        last_error = exc
                        if attempt < retries:
                            time.sleep(retry_wait_s)
                if last_error is None:
                    break
        if last_error is not None:
            raise last_error
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

    # Parameters can now be accessed using params_list['level1']['level2'] e.g. params_list['options']['download_gnps_job']


    # First, we retrieve the data from Zenodo if we have not done so already.
    # Toy ENPKG dataset is at https://zenodo.org/records/10018590
    retrieve_zenodo_data(record_id=params_list_full['data-download']['record_id'],
    record_name=params_list_full['data-download']['record_name'],
    output_path=os.path.normpath(params_list_full['general']['raw_data_path'])
    )
