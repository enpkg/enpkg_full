eval "$(conda shell.bash hook)"
conda activate enpkg_full

# cd ./tests/
# python -m pytest
# cd ..

# echo "Launching 01_test_create_architecture.sh"
# sh ./tests/01_test_create_architecture.sh

# echo "Launching 02_massive_id.sh"
# sh ./tests/02_test_massive_id.sh

# echo "Launching 03_test_taxo_enhancer.sh"
# sh ./tests/03_test_taxo_enhancer.sh

# echo "Launching 04_test_dl_ressources.sh"
# sh ./tests/04_test_dl_ressources.sh

# echo "Launching 05_test_make_adducts.sh"
# sh ./tests/05_test_make_adducts.sh

# echo "Launching 06_test_annotate_mn_isdb.sh"
# sh ./tests/06_test_annotate_mn_isdb.sh

# echo "Launching 07_test_annotate_sirius.sh"
# sh ./tests/07_test_annotate_sirius.sh

# echo "Launching 08_test_chemo_info_fetcher.sh"
# sh ./tests/08_test_chemo_info_fetcher.sh

# echo "Launching 09_test_memo.sh"
# sh ./tests/09_test_memo.sh

echo "Launching 10_test_graph_builder.sh"
sh ./tests/10_test_graph_builder.sh


conda deactivate

echo "Done !"

