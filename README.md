# enpkg_full
The full enpkg workflow


## Installing the required environment

```bash
mamba env create -f environment.yml
```

## Installing Sirius locally

Follow instructions at https://boecker-lab.github.io/docs.sirius.github.io/install/

Once Sirius is installed, you will need to precise the path to the executable in [here](https://github.com/enpkg/enpkg_full/blob/6064834e9dbec131c923c95e62dbf6eb208fc1ab/04_enpkg_sirius_canopus/configs/user/user.yml#L3)

## Editing config files

You will need to edit the following files:

- ISDB parameters at [user.yaml](https://github.com/enpkg/enpkg_full/blob/6064834e9dbec131c923c95e62dbf6eb208fc1ab/03_enpkg_mn_isdb_isdb_taxo/configs/user/user.yaml)
- Sirius parameters at [user.yml](https://github.com/enpkg/enpkg_full/blob/6064834e9dbec131c923c95e62dbf6eb208fc1ab/04_enpkg_sirius_canopus/configs/user/user.yml)
- Knowledge Graph construction parameters at [params.yaml](https://github.com/enpkg/enpkg_full/blob/6064834e9dbec131c923c95e62dbf6eb208fc1ab/06_enpkg_graph_builder/config/params.yaml)


## Testing the workflow

From the root of the repository, run:

```bash
sh tests/00_test_all.sh
```

This will download a small dataset (https://zenodo.org/records/10018590/) and run the full workflow on it. It should take less than 10 minutes to complete.