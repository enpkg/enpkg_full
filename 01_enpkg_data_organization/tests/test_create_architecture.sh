python ./src/create_architecture.py\
    --source_path tests/data/dbgkg_tropical_toydataset/msdata/processed\
    --target_path tests/data/output\
    --source_metadata_path tests/data/dbgkg_tropical_toydataset/metadata\
    --sample_metadata_filename dbgi_tropical_toydataset_metadata_inat.tsv\
    --lcms_method_params_filename dbgi_tropical_toydataset_lcms_params.txt\
    --lcms_processing_params_filename dbgi_tropical_toydataset_mzmine_params.xml\
    --polarity pos