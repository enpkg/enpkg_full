![release_badge](https://img.shields.io/github/v/release/enpkg/enpkg_full)
![license](https://img.shields.io/github/license/enpkg/enpkg_full)

# Welcome to the ENPKG Full Workflow!

<p align="center">
 <img src="https://github.com/enpkg/enpkg_workflow/blob/main/logo/enpkg_logo_full.png" width="400">
</p>


🌟 We're delighted to have you explore our computational workflow. This guide will walk you through the installation, setup, and execution of the ENPKG full workflow.
Interested in the science behind ENPKG? Check out the paper (https://doi.org/10.1021/acscentsci.3c00800) ! It's packed with insights and methodologies that power this workflow.

## 🌱 Getting Started

### Clone the repository

First, clone the repository to your local machine:

```bash
git clone https://github.com/enpkg/enpkg_full.git
```

Navigate to the newly created folder:

```bash
cd enpkg_full
```


### Install the required environment

We now rely on [uv](https://docs.astral.sh/uv/latest/) for dependency management. Install it if needed (see the [uv docs](https://docs.astral.sh/uv/latest/#installation) for alternative methods):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

With uv installed, sync the project dependencies into an isolated `.venv`:

```bash
# optional: install the Python version you want to use
uv python install 3.11

# install runtime dependencies and create .venv
uv sync
```

If you also want the development tooling (pytest, linters, etc.), add the dev dependency group:

```bash
uv sync --group dev
```

### Activate or use the environment

`uv sync` creates a `.venv` in the project root. Activate it with:

```bash
source .venv/bin/activate
```

You can also run commands without activating by prefixing them with `uv run`, e.g.:

```bash
uv run pytest
```

## 🌐 Install Sirius Locally


Check details at https://boecker-lab.github.io/docs.sirius.github.io/install/

Run `src/install_sirius.sh <install_dir>` to download and unpack the latest release for your platform, e.g.:

```bash
bash src/install_sirius.sh /opt/sirius
```

The script auto-detects the OS/CPU, but you can override them (e.g. `macos x64`) if needed. After installation, identify the full path to the `sirius` binary (`/opt/sirius/sirius/bin/sirius` on Linux, `/opt/sirius/sirius.app/Contents/MacOS/sirius` on macOS, etc.) and store it in `.env` as `PATH_TO_SIRIUS`. The workflow reads that variable when launching Sirius.


## 🔐 Environment Variables (.env)

Runtime secrets and machine-specific paths (e.g., `PATH_TO_SIRIUS`, `SIRIUS_USERNAME`, `SIRIUS_PASSWORD`) live in a `.env` file that is ignored by git. Configure it as follows:

```bash
cp .env.example .env
```

Edit `.env` with your editor of choice and provide the correct values (absolute path to the Sirius executable, Sirius account credentials, etc.). Before running the workflow, load the file into your shell session:

```bash
set -a
source .env
set +a
```

Because `.env` is ignored by git, you can safely customize it without leaking credentials.


## 🛠 Editing Config Files

You will need to edit the following parameters files:

- Parameters at [user.yaml](https://github.com/enpkg/enpkg_full/blob/main/params/user.yml)

All parameters are commented and should be self-explanatory.


### E.g. selection of the dataset to process

For example you can enter the record_id and record_name of a Zenodo dataset on [line](https://github.com/enpkg/enpkg_full/blob/main/params/user.yml#L8).
As it is set up here, this will download a small test dataset (https://doi.org/10.5281/zenodo.10018590).

## 🚀 Launching the Workflow

From the root of the repository, run:

```bash
sh workflow/00_workflow_all.sh
```

On the previous test dataset, this should take about 10 minutes to run.

## 🎉 Explore your newly generated Knowledge Graph

You can use GraphDB to explore the generated Knowledge Graph. To do so, you will need to install GraphDB (https://graphdb.ontotext.com/download/) and import the generated .ttl files.
Make sure to read the latest Graph DB documentation (https://graphdb.ontotext.com/documentation/) to get started.


## 🌟 Your Feedback Matters

Facing an Issue? Encountering a glitch or have a suggestion? Your input is crucial for us. Here’s how you can help:

- Report Issues: Use the 'Issues' tab in our GitHub repo to report any problems or ideas.
- Detailed Descriptions Help: Include as much detail as possible - error messages, steps to reproduce, and screenshots are all super helpful.
- Stay Updated: We’ll keep you in the loop as we work on fixing the issue or considering your suggestion.


## 🔎 Explore the ENPKG graph 

A Knowledge Graph, has been build on a collection of 1600 tropical plants extracts (https://doi.org/10.1093/gigascience/giac124). This KG also integrates data from a metabolomics study led over 337 medicinal plants of the Korean Pharmacopeia (https://doi.org/10.1038/s41597-022-01662-2). It can be explored following these links.

- The ENPKG graph is available at the following address https://enpkg.commons-lab.org/graphdb/. No need for login !
- The SPARQL research interface can be reached at https://enpkg.commons-lab.org/graphdb/sparql. Make sure to check the [paper](https://doi.org/10.1021/acscentsci.3c00800) for examples of queries.
- The ENPKG vocabulary is described at https://enpkg.commons-lab.org/doc/index.html


## 📜 Citations 

This set of script represents a pipeline calling multiple tools. Please make sure to cite the original authors of the tools used in this workflow.

[Allard et al. 2016, Analytical Chemistry](https://pubs.acs.org/doi/10.1021/acs.analchem.5b04804)  
[Davies et al. 2015, Nucleic Acids Research](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4489243/)  
[Djoumbou et al. 2016, Journal of Cheminformatics](https://jcheminf.biomedcentral.com/articles/10.1186/s13321-016-0174-y)  
[Dührkop et al. 2015, Nature Methods](https://www.pnas.org/doi/full/10.1073/pnas.1509788112)  
[Dührkop et al. 2019, Nature Methods](https://www.nature.com/articles/s41592-019-0344-8)  
[Dührkop et al. 2020, Nature Biotechnology](https://www.nature.com/articles/s41587-020-0740-8)  
[Gaudry et al. 2022, Frontiers in Bioinformatics](https://www.frontiersin.org/articles/10.3389/fbinf.2022.842964/full)  
[Hoffmann et al. 2022, Nature Biotechnology](https://www.nature.com/articles/s41587-021-01045-9)  
[Huber et al. 2020, Journal of Open Source Software](https://joss.theoj.org/papers/10.21105/joss.02411)  
[Kim et al. 2021, Journal of Natural Products](https://pubs.acs.org/doi/10.1021/acs.jnatprod.1c00399)  
[Ludwig et al. 2020, Nature Machine Intelligence](https://pubs.acs.org/doi/10.1021/acs.jnatprod.1c00399)  
[McTavish et al. 2021, Systematic Biology](https://academic.oup.com/sysbio/article/70/6/1295/6273200)  
[Rutz et al. 2016, Frontiers in Plant Science](https://www.frontiersin.org/articles/10.3389/fpls.2019.01329/full)  
[Rutz et al. 2022, Elife](https://elifesciences.org/articles/70780)  

To cite the ENPKG workflow, please use the following reference [Gaudry et al. 2023](https://doi.org/10.1021/acscentsci.3c00800).


## 📋 Note

This workflow describes a pilot application aiming to transition from classical metabolomics datasets to [Linked Open Data](https://5stardata.info/en/) in such datasets. It is currently being ported to the more generic EMIKG framework (https://github.com/earth-metabolome-initiative/emikg) that we are developping in the frame of the Earth Metabolome Initiative (http://www.earthmetabolome.org/). Stay tuned.
