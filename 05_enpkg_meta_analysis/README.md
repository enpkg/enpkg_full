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
Set `general.treated_data_path`, `chemo-info-fetching.sql_db_path` (directory with trailing slash), and `chemo-info-fetching.sql_db_name` in `params/user.yml`. Relative paths resolve from `05_enpkg_meta_analysis`. For a benchmark replay, use a copy of the trial database or a new database and keep the retained trial unchanged. Run from the repository root.

```sh
python 05_enpkg_meta_analysis/src/chemo_info_fetcher.py
```

Enrichment reads ISDB annotations, an optional GNPS job and both `structure_identifications.tsv` and `compound_identifications.tsv` in each positive and negative SIRIUS workspace. The fetcher looks up distinct 14-letter InChIKey connectivity blocks in the [QLever Wikidata snapshot](https://qlever.dev/wikidata), in batches of 100. Each matching Wikidata `P235` full InChIKey and chemical entity is retained. A connectivity match can include multiple stereoisomers or isotopologues. NPClassifier supplies the classification for SIRIUS-only structures.

`no_wikidata_match` denotes a successful lookup with no matching entry in the queried snapshot. An HTTP or response error stops enrichment before any rows are written. Rerun the command after service recovery. A cached row with `wikidata_id = 'no_wikidata_match'` and `inchikey = short_inchikey` is retried when its connectivity key occurs in the input. Keep the resulting SQLite database with the benchmark inputs and record the lookup date because the public snapshot changes. Sample taxon links are generated separately.

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

