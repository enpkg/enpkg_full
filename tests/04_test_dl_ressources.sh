cd ./03_enpkg_mn_isdb_isdb_taxo

# First, check wether the directories are already here

if [ -d "./db_metadata" ]
then
    echo "db_metadata already exists"
else
    mkdir db_metadata
fi

if [ -d "./db_spectra" ]
then
    echo "db_spectra already exists"
else
    mkdir db_spectra
fi

# Then check wether the files are already here

if [ -f "./db_metadata/230106_frozen_metadata.csv.gz" ]
then
    echo "230106_frozen_metadata.csv.gz already exists"
else
    wget https://zenodo.org/record/7534071/files/230106_frozen_metadata.csv.gz
    mv 230106_frozen_metadata.csv.gz ./db_metadata
fi

if [ -f "./db_spectra/isdb_pos_cleaned.pkl" ]
then
    echo "isdb_pos_cleaned.pkl already exists"
else
    wget https://zenodo.org/records/8287341/files/isdb_pos_cleaned.pkl
    mv isdb_pos_cleaned.pkl ./db_spectra
fi


# wget https://zenodo.org/record/7534071/files/230106_frozen_metadata.csv.gz
# wget https://zenodo.org/records/8287341/files/isdb_pos_cleaned.pkl

# mv 230106_frozen_metadata.csv.gz ./db_metadata
# mv isdb_pos_cleaned.pkl ./db_spectra