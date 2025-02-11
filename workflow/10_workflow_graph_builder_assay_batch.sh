#!/bin/bash
set -e  # Stop on errors
source /home/quirosgu/anaconda3/bin/activate enpkg_full

echo "Running 01_a_rdf_enpkg_metadata_indi_para.py"
python /home/quirosgu/Desktop/Github/enpkg_full/06_enpkg_graph_builder/src/individual_processing/01_a_rdf_enpkg_metadata_indi_by_polarity_para.py

echo "Running 01_b_rdf_enpkgmodule_metadata_indi_dynamic.py"
python /home/quirosgu/Desktop/Github/enpkg_full/06_enpkg_graph_builder/src/individual_processing/01_b_rdf_enpkgmodule_metadata_indi_by_polarity_dynamic.py

echo "Running 02_a_rdf_features_indi_para.py"
python /home/quirosgu/Desktop/Github/enpkg_full/06_enpkg_graph_builder/src/individual_processing/02_a_rdf_features_indi_para.py

#echo "Running 02_b_rdf_features_spec2vec_indi_para.py"
#python /home/quirosgu/Desktop/Github/enpkg_full/06_enpkg_graph_builder/src/individual_processing/02_b_rdf_features_spec2vec_indi_para.py

echo "Running 05_rdf_isdb_annotations_indi_para.py"
python /home/quirosgu/Desktop/Github/enpkg_full/06_enpkg_graph_builder/src/individual_processing/05_rdf_isdb_annotations_indi_para.py

echo "Running 06_rdf_individual_mn_indi_para.py"
python /home/quirosgu/Desktop/Github/enpkg_full/06_enpkg_graph_builder/src/individual_processing/06_rdf_individual_mn_indi_para.py

echo "Running 07_rdf_structures_metadata_indi_para.py"
python /home/quirosgu/Desktop/Github/enpkg_full/06_enpkg_graph_builder/src/individual_processing/07_rdf_structures_metadata_indi_by_polarity_para.py

echo "Running 08_rdf_merger_by_polarity_metadata.py"
python /home/quirosgu/Desktop/Github/enpkg_full/06_enpkg_graph_builder/src/individual_processing/08_rdf_merger_by_polarity_metadata.py

echo "Running 08_rdf_merger_by_polarity_chemistry.py"
python /home/quirosgu/Desktop/Github/enpkg_full/06_enpkg_graph_builder/src/individual_processing/08_rdf_merger_by_polarity_chemistry.py

echo "Running 09_rdf_exporter.py"
python /home/quirosgu/Desktop/Github/enpkg_full/06_enpkg_graph_builder/src/individual_processing/09_rdf_exporter.py
