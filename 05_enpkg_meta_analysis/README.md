# enpkg_meta_analysis

![release_badge](https://img.shields.io/github/v/release/enpkg/enpkg_meta_analysis)
![license](https://img.shields.io/github/license/enpkg/enpkg_meta_analysis)

<p align="center">
 <img src="https://github.com/enpkg/enpkg_workflow/blob/main/logo/enpkg_logo_full.png" width="200">
</p>

Analyses  to enrich the Experimental Natural Products Knowledge Graph.

⚙️ Module part of [enpkg_workflow](https://github.com/enpkg_mn_isdb_taxo/enpkg_workflow).  

First data have to be organized using [enpkg_data_organization](https://github.com/enpkg/enpkg_data_organization), taxonomy resolved using [enpkg_taxo_enhancer](https://github.com/enpkg/enpkg_taxo_enhancer) and spectra annotated using [enpkg_mn_isdb_taxo](https://github.com/enpkg/enpkg_mn_isdb_taxo) and/or [enpkg_sirius_canopus](https://github.com/enpkg/enpkg_sirius_canopus). 

Available meta-analyses:
- Structures metadata fetcher: retrieve the NPClassifier taxonomy and the Wikidata ID of annotated structures.
- MEMO: compare the chemistry of large amount of samples.
- ChEMBL: retrieve compounds with an activity against a given target for biodereplication.

## 0. Clone repository and install environment

1. Clone this repository.
2. Create environment: 
```console 
conda env create -f environment.yml
```
3. Activate environment:  
```console 
conda activate meta_analysis
```

## 1. Fetching structures' metadata
To enrich our knowledge graph, we will fetch for dereplicated structures their Wikidata id and their [NPClassifier](https://pubs.acs.org/doi/10.1021/acs.jnatprod.1c00399) taxonomy. Because the NPClassifier API can be slow for large amount of structures, results are stored in a SQL database. You can use the same SQL DB in your different project to avoid processing multiple times the same structure. The first time you run the process, a new SQL DB will be created at the default location (**./output_data/sql_db/{sql_name.db}**).
### Worflow
To do so, use the following command:
```console
python .\src\chemo_info_fetcher.py -p path/to/your/data/directory/ --sql_name structures_metadata.db
```

## 2. MEMO analysis (optional)
Using individual fragmentation spectra files, it is possible to generate for each sample a MS2-based fingerprint, or [MEMO](https://github.com/mandelbrot-project/memo) vector. This allows to rapidly compare large amount of chemo-diverse samples to identify potential similarities in composition among them. Here, the aligned MEMO matrix of all samples' fingerprints will be generated.
### Worflow
```console
python .\src\memo_unaligned_repo.py -p path/to/your/data/directory/ --ionization {pos, neg or both} --output {output_name}
```

This will create 2 files in **path/to/your/data/directory/003_memo_analysis/**:

More parameters inherent to the vectorization process are available, for help use:
| Filename | Description |
| :------- | :-----------|
{output_name}\_params.csv | Parameters used to generate the corresponding MEMO matrix
{output_name}.gz | The MEMO matrix (with gzip compression)

Fo help about the MEMO vectorization parameters, use:

```console
python .\src\memo_unaligned_repo.py --help
```

## 3. Fetching ChEMBL compounds with activity against a given target (optional)
To enrich our knowledge graph, it is possible to include compounds from ChEMBL with activity against a target of interest. This could be fone using the ChEMBL KG itself, but it is unfortunately not available. Besides fetching compounds from ChEMBL, it is also possible to filter them according to their [NP likeliness](https://pubs.acs.org/doi/10.1021/ci700286x) score to remove synthetic compounds. 

To search for your target id go to https://www.ebi.ac.uk/chembl/. Format is CHEMBLXXXX e.g. https://www.ebi.ac.uk/chembl/target_report_card/CHEMBL364/

### Worflow
To do so, use the following command:
```console
python .\src\download_chembl.py -id {chembl_target_id} -npl {minimal_NP_like_score}
```
The resulting table will be placed in **./output_data/chembl/{target_id}\_np_like_min_{min_NPlike_score}.csv**.

## Citations
If you use this ENPKG module, please cite:  
- for MEMO:
[Gaudry et al. 2022, Frontiers in Bioinformatics](https://www.frontiersin.org/articles/10.3389/fbinf.2022.842964/full)  
- for ChEMBL:
[Davies et al. 2015, Nucleic Acids Research](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4489243/)  

