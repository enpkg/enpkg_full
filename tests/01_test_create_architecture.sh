python ./01_enpkg_data_organization/src/create_architecture.py\
    --source_path tests/data/input/dbgi_tropical_mini_toy_dataset/msdata/processed \
    --target_path tests/data/output\
    --source_metadata_path tests/data/input/dbgi_tropical_mini_toy_dataset/metadata \
    --sample_metadata_filename dbgi_tropical_toydataset_metadata.tsv \
    --lcms_method_params_filename dbgi_tropical_toydataset_lcms_params.txt \
    --lcms_processing_params_filename dbgi_tropical_toydataset_mzmine_params.xml \
    --polarity pos