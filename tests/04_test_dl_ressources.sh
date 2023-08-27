cd ./03_enpkg_mn_isdb_isdb_taxo
wget https://zenodo.org/record/7534071/files/230106_frozen_metadata.csv.gz
wget https://zenodo.org/record/7534250/files/isdb_pos.mgf

mv 230106_frozen_metadata.csv.gz ./db_metadata
mv isdb_pos.mgf ./db_spectra