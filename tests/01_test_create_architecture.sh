python ./01_enpkg_data_organization/src/create_architecture.py\
    --source_path tests/data/input/enpkg_toy_dataset/msdata/processed \
    --target_path tests/data/output\
    --source_metadata_path tests/data/input/enpkg_toy_dataset/metadata \
    --sample_metadata_filename metadata.tsv \
    --lcms_method_params_filename lcms_method_params.txt \
    --lcms_processing_params_filename lcms_processing_params.xml \
    --polarity pos