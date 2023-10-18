# eval "$(conda shell.bash hook)"
# conda activate taxo_enhancer

python ./02_enpkg_taxo_enhancer/src/taxo_info_fetcher.py \
    -p ../tests/data/output \
    -f

# conda deactivate
