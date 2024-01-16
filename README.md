# enpkg_full
The full enpkg workflow


## Install the required environment

```bash
mamba env create -f environment.yml
```

## Activate the environment

```bash
conda activate enpkg_full
```

## Install Sirius locally


Check details at https://boecker-lab.github.io/docs.sirius.github.io/install/

To get the latest version for your platform, run the `install_sirius.sh` script specifying the path chosen for the installation. For example, from the root of the repository:

```bash
bash src/install_sirius.sh /home/username/sirius
```

Once Sirius is installed, you will need to precise the path to the executable in [here](https://github.com/enpkg/enpkg_full/blob/6064834e9dbec131c923c95e62dbf6eb208fc1ab/04_enpkg_sirius_canopus/configs/user/user.yml#L3)

Setting up the environment variables. To login to Sirius, you will need to set up the following environment variables (SIRIUS_USERNAME and SIRIUS_PASSWORD). You can do so launching the following command:

```bash
bash src/setup_sirius_env.sh
```


## Editing config files

You will need to edit the following parameters files:

- Parameters at [user.yaml](https://github.com/enpkg/enpkg_full/blob/c8e649290ee72f000c3385e7669b5da2215abad8/params/user.yml)

All parameters are commented and should be self-explanatory.


### E.g. selection of the dataset to process

For example you can enter the record_id and record_name of a Zenodo dataset on [line](https://github.com/enpkg/enpkg_full/blob/c8e649290ee72f000c3385e7669b5da2215abad8/params/user.yml#L8)
As it is set up here, this will download a small test dataset (https://zenodo.org/records/10018590/).

## Launching the workflow

From the root of the repository, run:

```bash
sh workflow/00_workflow_all.sh
```

On the previous test dataset, this should take about 10 minutes to run.

## Exploring the generated Knowledge Graph

You can use GraphDB to explore the generated Knowledge Graph. To do so, you will need to install GraphDB (https://graphdb.ontotext.com/download/) and import the generated .ttl files.


# Note

This workflow is currently being ported to the EMIKG framework (https://github.com/earth-metabolome-initiative/emikg).
