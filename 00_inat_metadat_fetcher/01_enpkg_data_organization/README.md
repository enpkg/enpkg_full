# enpkg_data_organization
![release_badge](https://img.shields.io/github/v/release/enpkg/enpkg_data_organization)
![license](https://img.shields.io/github/license/enpkg/enpkg_data_organization)

<p align="center">
 <img src="https://github.com/enpkg/enpkg_workflow/blob/main/logo/enpkg_logo_full.png" width="200">
</p>

Script to organize unaligned metabolomics sample files for the ENPKG workflow.

⚙️ Module part of [enpkg_workflow](https://github.com/enpkg/enpkg_workflow).  

## Workflow

For each ionization mode, proceed as follows:

### 0) Requirements
To install the package requirements, you can run the following command:

```bash
pip install -r requirements.txt
```

### 1) MzMine2 processing

In MzMine (2 or 3), process your files according to the [FBMN workflow](https://ccms-ucsd.github.io/GNPSDocumentation/featurebasedmolecularnetworking-with-mzmine2/) until the "Isotope Grouping" step. At this step, filter the obtained feature lists to keep only features linked to an MS/MS spectrum.  
:warning: Don't forget to use "Reset feature ID" when filtering features with MS/MS only. This will cause inconsistencies in GNPS links if not done.

Once this is done, export all your **unaligned** feature lists using the "Export to GNPS" module. Select the targeted folder and as a filename insert empty curly brackets so MzMine will name files according to the feature list names (ex: "path/to/your/data/directory/{}"). Do the same using the "Export to Sirius" module, this time adding a "_sirius.mgf" suffix (ex: "path/to/your/data/directory/{}_sirius.mgf"). 

:warning: **1. Export PI mode and NI mode data in 2 separate folders.**

:warning: **2. If some samples were not analyzed using the same LC-MS method, export them in different folders (i.e. one export folder by LC-MS method AND ionization mode).**

### 2) Additional files required

**3 additional files** are required at this step:
- samples' metadata file (.tsv format)
- a LC-MS metadata file (any text-based format)
- a LC-MS processing metadata file (any text-based format)

#### 2.1 Samples' metadata file

You have to include samples' metadata in a **.tsv file.**  

**5 columns are required**: sample_filename_pos, sample_filename_neg, sample_id, sample_type & sample_organism.
NB: if you have only pos files, no need for sample_filename_neg column (and the opposite if you have only neg files).

- **`sample_filename_pos`**: the name of the mzML or mzXML LC-MS file (ex: `211027_AG_ZC012714_pos_20211028181555.mzML`).
- **`sample_filename_neg`**: the name of the mzML or mzXML LC-MS file (ex: `211027_AG_ZC012714_neg_20211029132336.mzML`).
- **`sample_id`**: the sample ID corresponding to the file (ex: `AG_ZC012714`)
- **`sample_type`**: one of `QC`, `blank` or `sample`.
- **`source_id`**: the ID of the biological material used to prepare the sample. For example, the ID of the raw plant material used to generate the extract.
- **`source_taxon`**: for samples (not QC and blanks), the taxon name of the source_id (ex: `Ailanthus` or `Ailanthus altissima`).

You can also add as many additional columns as you wish (bioactivity, injection date, LC method, ...). These will be kept in individual metadata files but ignored in the processing.

An example of samples' metadata file can be found [here](https://github.com/enpkg/enpkg_data_organization/blob/main/data/metadata.tsv).

#### 2.2 LC-MS parameters metadata file
This file must contain the LC-MS method details. It can be free text saved as .txt file (such as the method section in an article for example), or a more structured file (such as a .yaml file). **Only one requirment: always use the same format when referring to the same LC-MS method!**

An example of LC-MS metadata file can be found [here](https://github.com/enpkg/enpkg_data_organization/blob/main/data/lcms_method_params.txt).

#### 2.3 LC-MS processing parameters metadata file
This file must contain the LC-MS processing details (the parameters used in MZmine). As for the LC-MS metadata file, it can be free text saved as .txt file (such as the method section in an article for example), or a more structured file (such as a .yaml file). **Only one requirment: always use the same format when referring to the same LC-MS processing parameters!**

**For this file, we recommend you to use the .xml parameters file you can export directly from MZmine.**

An example of LC-MS processing metadata file can be found [here](https://github.com/enpkg/enpkg_data_organization/blob/main/data/lcms_processing_params.xml).

▶️ **Finally, place the 3 metadata files in the folder where you exported your feature lists files.**

### 3) Create architecture!

Once this is done, lauch the create_architecture.py script to organize your files using the following command adapted to your case:

```bash
python .\src\create_architecture.py --source_path {path/to/your/data/in/directory/} --target_path {path/to/your/data/out/directory/}  --sample_metadata_filename {metadatafilename.tsv} --lcms_method_params_filename {lcms_method_params_filename}
--lcms_processing_params_filename {lcms_processing_params_filename} --polarity {pos}
```
If existing, do the same for the other ionization mode (using the same target_path).

```bash
python .\src\create_architecture.py --source_path {path/to/your/data/in/directory/} --target_path {path/to/your/data/out/directory/}  --sample_metadata_filename {metadatafilename.tsv} --lcms_method_params_filename {lcms_method_params_filename}
--lcms_processing_params_filename {lcms_processing_params_filename} --polarity {neg}
```
For help with the arguments:

```bash
python .\src\create_architecture.py --help
```

## Desired architecture

```
data/
└─── sample_a/
|     └─── sample_a_metadata.tsv                     # Metadata of sample_a
|     └─── pos/
|     |     sample_a_features_quant_pos.csv          # Features intensity table in positive mode
|     |     sample_a_features_ms2_pos.mgf            # Features fragmentations spectra in positive mode
|     |     sample_a_sirius_pos.mgf                  # Features fragmentations spectra for sirius (with MS1 isotope pattern) in positive mode 
|     └─── neg/
|           sample_a_features_quant_neg.csv
|           sample_a_features_ms2_neg.mgf
|           sample_a_sirius_neg.mgf
|
└─── sample_b/
|
└─── sample_n/
|
└─── for_massive_upload_pos/                         # All *_features_ms2_pos.mgf files ready for upload on MassIVE
|     └─── sample_a_features_ms2_pos.mgf                     
|     └─── ...                    
|     └─── sample_n_features_ms2_pos.mgf
|
└─── for_massive_upload_neg/                         # All *_features_ms2_neg.mgf files ready for upload on MassIVE
      └─── sample_a_features_ms2_neg.mgf                    
      └─── ...                    
      └─── sample_n_features_ms2_neg.mgf                    
```

NB: In this example both pos and neg ionization mode are present for samples, but having only one is fine too.

### 4) Add GNPS MassIVE information

To enjoy links to [GNPS LCMS dasboard](https://gnps-lcms.ucsd.edu/) and visualization of your MS/MS spectra directly from the knowldege graph, your data (.mz(X)ML files and feature_MS2_pos/neg.mgf) have to be uplaoded to the [GNPS MassIVE](https://massive.ucsd.edu/ProteoSAFe/static/massive.jsp) repository. For an easy upload of your features' fragmentation spectra, you can directly upload the content of the **for_massive_upload_<ionization_mode>** folder(s). See [GNPS documentation](https://ccms-ucsd.github.io/GNPSDocumentation/datasets/) for details on the MassIVE upload process.

:warning: The filenames of the .mz(X)ML files you upload on MassIVE have to match the filenames in your metadata file.

Once this is done, add the MassIVE ID to the medatadata using the following command:

```bash
python .\src\add_massive_id.py --massive_id {massive_id} -p {path/to/your/data/ouptut/}
```

### 5) Next step 🚀

https://github.com/enpkg/enpkg_taxo_enhancer
