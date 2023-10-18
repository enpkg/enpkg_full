# eval "$(conda shell.bash hook)"
# conda activate meta_analysis

python ./05_enpkg_meta_analysis/src/memo_unaligned_repo.py \
-p ./tests/data/output \
--ionization pos \
--output memo_matrix

# conda deactivate