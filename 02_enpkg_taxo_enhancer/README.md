# enpkg_taxo_enhancer

![release_badge](https://img.shields.io/github/v/release/enpkg/enpkg_taxo_enhancer)
![license](https://img.shields.io/github/license/enpkg/enpkg_taxo_enhancer)

<p align="center">
 <img src="https://github.com/enpkg/enpkg_workflow/blob/main/logo/enpkg_logo_full.png" width="200">
</p>

Retrieve taxonomy and Wikidata ID from the biosource of ENPKG formatted samples.  

⚙️ Module part of [enpkg_workflow](https://github.com/enpkg/enpkg_workflow).  

## Required starting architecture

```
data/
└─── sample_a/
|     └─── sample_a_metadata.tsv
|
└─── sample_b/
|
└─── sample_n/
```
See https://github.com/enpkg/enpkg_data_organization for data organization.

## Workflow

1. Clone this repository.
2. Create (<code>conda env create -f environment.yml</code>) and activate environment (<code>conda activate taxo_enhancer</code>).
3. Lauch the script: only 1 argument needed here, the path to your data directory.

```console
python ./src/taxo_info_fetcher.py -p path/to/your/data/directory/
```

## Target architecture

```
data/
└─── sample_a/
|     └─── sample_a_metadata.tsv 
|     └─── taxo_output/
|            └─── sample_a_species.json                # OTT matched species
|            └─── sample_a_taxon_info.json             # OTT taxonomy for matched species
|            └─── sample_a_taxo_metadata.tsv           # metadata enhanced with taxonomy
|            └─── params.yaml                          # The parameters used to generate the results
|
└─── sample_b/
|
└─── sample_n/
```

## Citations
If you use this ENPKG module, please cite:    
[McTavish et al. 2021, Systematic Biology](https://academic.oup.com/sysbio/article/70/6/1295/6273200)
