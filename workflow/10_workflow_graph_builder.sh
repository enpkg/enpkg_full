eval "$(conda shell.bash hook)"
conda activate graph_builder

# echo "Running 01_a_rdf_enpkg_metadata_indi.py"
# python ./06_enpkg_graph_builder/src/individual_processing/01_a_rdf_enpkg_metadata_indi.py

# echo "Running 01_b_rdf_enpkgmodule_metadata_indi.py"
# python ./06_enpkg_graph_builder/src/individual_processing/01_b_rdf_enpkgmodule_metadata_indi.py

echo "Running 02_a_rdf_features_indi_para.py"
python ./06_enpkg_graph_builder/src/individual_processing/02_a_rdf_features_indi_para.py

# echo "Running 02_b_rdf_features_spec2vec_indi_para.py"
# python ./06_enpkg_graph_builder/src/individual_processing/02_b_rdf_features_spec2vec_indi_para.py

# echo "Running 03_rdf_csi_annotations_indi.py"
# python ./06_enpkg_graph_builder/src/individual_processing/03_rdf_csi_annotations_indi.py

# echo "Running 04_rdf_canopus_indi.py"
# python ./06_enpkg_graph_builder/src/individual_processing/04_rdf_canopus_indi.py

# echo "Running 05_rdf_isdb_annotations_indi.py"
# python ./06_enpkg_graph_builder/src/individual_processing/05_rdf_isdb_annotations_indi.py

# echo "Running 06_rdf_individual_mn_indi_para.py"
# python ./06_enpkg_graph_builder/src/individual_processing/06_rdf_individual_mn_indi_para.py

# echo "Running 07_rdf_structures_metadata_indi.py"
# python ./06_enpkg_graph_builder/src/individual_processing/07_rdf_structures_metadata_indi.py

# echo "Running 08_rdf_merger_para.py"
# python ./06_enpkg_graph_builder/src/individual_processing/08_rdf_merger_para.py

# echo "Running 09_rdf_exporter.py"
# python ./06_enpkg_graph_builder/src/individual_processing/09_rdf_exporter.py

conda deactivate