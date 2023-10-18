eval "$(conda shell.bash hook)"
conda activate graph_builder

python ./06_enpkg_graph_builder/src/individual_processing/01_a_rdf_enpkg_metadata_indi.py

conda deactivate