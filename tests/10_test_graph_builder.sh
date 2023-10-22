eval "$(conda shell.bash hook)"
conda activate graph_builder

echo "Running test_01_a_rdf_enpkg_metadata_indi.sh"
sh ./tests/test_01_a_rdf_enpkg_metadata_indi.sh

echo "Running test_01_b_rdf_enpkgmodule_metadata_indi.sh"
sh ./tests/test_01_b_rdf_enpkgmodule_metadata_indi.sh

echo "Running test_02_a_rdf_features_indi.sh"
sh ./tests/test_02_a_rdf_features_indi.sh

echo "Running test_02_b_rdf_features_spec2vec_indi.sh"
sh ./tests/test_02_b_rdf_features_spec2vec_indi.sh

echo "Running test_03_rdf_csi_annotations_indi.sh"
sh ./tests/test_03_rdf_csi_annotations_indi.sh

echo "Running test_04_rdf_canopus_indi.sh"
sh ./tests/test_04_rdf_canopus_indi.sh

echo "Running test_05_rdf_isdb_annotations_indi.sh"
sh ./tests/test_05_rdf_isdb_annotations_indi.sh

echo "Running test_06_rdf_individual_mn_indi.sh"
sh ./tests/test_06_rdf_individual_mn_indi.sh

echo "Running test_07_rdf_structures_metadata_indi.sh"
sh ./tests/test_07_rdf_structures_metadata_indi.sh

echo "Running test_08_rdf_merger.sh"
sh ./tests/test_08_rdf_merger.sh

echo "Running test_09_rdf_exporter.sh"
sh ./tests/test_09_rdf_exporter.sh

conda deactivate