# enpkg_mn_isdb_taxo

![release_badge](https://img.shields.io/github/v/release/enpkg/enpkg_mn_isdb_taxo)
![license](https://img.shields.io/github/license/enpkg/enpkg_mn_isdb_taxo)

<p align="center">
 <img src="https://github.com/enpkg/enpkg_workflow/blob/main/logo/enpkg_logo_full.png" width="200">
</p>

Repository gathering scripts to perform MS/MS annotation using ISDB, MS1 annotation, Molecular Networking and annotations reweighting on a set of individual files.  

⚙️ Module part of [enpkg_workflow](https://github.com/enpkg/enpkg_workflow).    

First data have to be organized using [data_organization](https://github.com/enpkg/enpkg_data_organization) and taxonomy resolved using [taxo_enhancer](https://github.com/enpkg/enpkg_taxo_enhancer).  

## Required starting architecture

```
data/
└─── sample_a/
|     └─── sample_a_metadata.tsv
|     └─── pos/
|     |     sample_a_features_quant_pos.csv
|     |     sample_a_features_ms2_pos.mgf     
|     └─── neg/
|     |     sample_a_features_quant_neg.csv
|     |     sample_a_features_ms2_neg.mgf
|     └─── taxo_output/
|           └─── sample_a_species.json
|           └─── sample_a_taxon_info.json
|           └─── sample_a_taxo_metadata.tsv
|
└─── sample_b/
|
└─── sample_n/
```
NB: Only one ionization mode is required. 

## 1. Clone repository and install environment

1. Clone this repository.
2. Create environment: 
```console 
conda env create -f environment.yml
```
3. Activate environment:  
```console 
conda activate indifiles_annotation_env
```

## 2. Get structure-organism pairs and spectral database
Thanks to the [LOTUS initiative](https://lotus.nprod.net/), a large number of NPs with their associated biosources are made available. *In silico* fragmented spectra of these NPs are also available.  
1. Download structure-organism pairs: e.g. https://zenodo.org/record/6582124#.YqwzU3ZBxPY (latest version always available at https://doi.org/10.5281/zenodo.5794106).

For example:

```console
wget https://zenodo.org/record/7534071/files/230106_frozen_metadata.csv.gz
```
2. Download *in silico* fragmentation spectra (positive and negative mode): https://zenodo.org/record/6939173#.YvX2Q3ZByUk (latest version always available at https://doi.org/10.5281/zenodo.7534250).

For example:

```console
wget https://zenodo.org/record/7534250/files/isdb_pos.mgf
```

3. Move the structure-organism pairs file into:  
<code>../indifiles_annotation/db_metadata/</code>
4. Move the spectra file(s) into:  
<code>../indifiles_annotation/db_spectra/</code>

## 3. Prepare potential adducts

We will use the structure-organism pairs database to compute the *m/z* of potential adducts. To do so, use the following command:

```console
python src/adducts_formatter.py -p db_metadata/220525_frozen_metadata.csv.gz # Replace according to your version
```
This will create adducts 2 adducts files (pos/neg) and the adducts used (params) in:  
<code>../indifiles_annotation/data_loc/220525_frozen_metadata/</code>

NB: To edit the calculated adducts, modify this script according to your needs:  
https://github.com/mandelbrot-project/indifiles_annotation/blob/main/src/adducts_formatter.py

## 3. Adapt parameters and launch the process! 🚀

1. Copy and rename the parameters file <code>../indifiles_annotation/configs/default/default.yaml</code> into <code>../indifiles_annotation/configs/user/user.yaml</code>
2. Modifiy the user.yaml file according to your needs (especially the paths).
3. Launch the process:
```console
python src/nb_indifile.py
```

##  Target architecture

```
data/
└─── sample_a/
|     └───  sample_a_metadata.tsv
|     └─── pos/
|     |     |  sample_a_features_quant_pos.csv
|     |     |  sample_a_features_ms2_pos.mgf
|     |     └─── isdb/
|     |     |      └─── sample_a_isdb_pos.tsv                       # MS2 annootations
|     |     |      └─── sample_a_isdb_reweighted_pos.tsv            # MS2 annotations reweighted, cytoscape ready (1 feature by line)
|     |     |      └─── sample_a_isdb_reweighted_flat_pos.tsv       # MS2 annotations flat (1 annotation by line)
|     |     |      └─── sample_a_treemap_chemo_counted_pos.html     # NPClassifier treemap using annotation count
|     |     |      └─── sample_a_treemap_chemo_intensity_pos.html   # NPClassifier treemap using annotation average intensity
|     |     |      └─── config.yaml                                 # configuration used
|     |     └─── molecular_network/
|     |     |      └─── sample_a_mn_pos.graphml                     # Moleculat network
|     |     |      └─── sample_a_mn_metadata_pos.tsv                # Moleculat network metadata (component id, precursor m/z)
|     |     |      └─── config.yaml                                 # configuration used
|     └─── taxo_output/
|            └─── sample_a_species.json
|            └─── sample_a_taxon_info.json
|            └─── sample_a_taxo_metadata.tsv
|
└─── sample_b/
|
└─── sample_n/
```
##  Citations
If you use this ENPKG module, please cite:  
[Allard et al. 2016, Analytical Chemistry](https://pubs.acs.org/doi/10.1021/acs.analchem.5b04804)  
[Rutz et al. 2016, Frontiers in Plant Science](https://www.frontiersin.org/articles/10.3389/fpls.2019.01329/full)  
[Rutz et al. 2022, Elife](https://elifesciences.org/articles/70780)  
[Huber et al. 2020, Journal of Open Source Software](https://joss.theoj.org/papers/10.21105/joss.02411)  



