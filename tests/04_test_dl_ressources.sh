cd ./03_enpkg_mn_isdb_isdb_taxo
wget https://zenodo.org/record/7534071/files/230106_frozen_metadata.csv.gz
wget https://zenodo.org/records/8287341/files/isdb_pos_cleaned.pkl

mv 230106_frozen_metadata.csv.gz ./db_metadata
mv isdb_pos_cleaned.pkl ./db_spectra