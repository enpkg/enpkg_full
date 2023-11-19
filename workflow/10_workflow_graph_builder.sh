eval "$(conda shell.bash hook)"
conda activate graph_builder

echo "Running workflow_01_a_rdf_enpkg_metadata_indi.sh"
sh ./workflow/workflow_01_a_rdf_enpkg_metadata_indi.sh

echo "Running workflow_01_b_rdf_enpkgmodule_metadata_indi.sh"
sh ./workflow/workflow_01_b_rdf_enpkgmodule_metadata_indi.sh

echo "Running workflow_02_a_rdf_features_indi.sh"
sh ./workflow/workflow_02_a_rdf_features_indi.sh

echo "Running workflow_02_b_rdf_features_spec2vec_indi.sh"
sh ./workflow/workflow_02_b_rdf_features_spec2vec_indi.sh

echo "Running workflow_03_rdf_csi_annotations_indi.sh"
sh ./workflow/workflow_03_rdf_csi_annotations_indi.sh

echo "Running workflow_04_rdf_canopus_indi.sh"
sh ./workflow/workflow_04_rdf_canopus_indi.sh

echo "Running workflow_05_rdf_isdb_annotations_indi.sh"
sh ./workflow/workflow_05_rdf_isdb_annotations_indi.sh

echo "Running workflow_06_rdf_individual_mn_indi.sh"
sh ./workflow/workflow_06_rdf_individual_mn_indi.sh

echo "Running workflow_07_rdf_structures_metadata_indi.sh"
sh ./workflow/workflow_07_rdf_structures_metadata_indi.sh

echo "Running workflow_08_rdf_merger.sh"
sh ./workflow/workflow_08_rdf_merger.sh

echo "Running workflow_09_rdf_exporter.sh"
sh ./workflow/workflow_09_rdf_exporter.sh

conda deactivate