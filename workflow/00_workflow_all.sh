# echo "Launching 01_0_workflow_data_download.sh"
# sh ./workflow/01_0_workflow_data_download.sh

# echo "Launching 01_1_workflow_create_architecture.sh"
# sh ./workflow/01_1_workflow_create_architecture.sh

# echo "Launching 02_massive_id.sh"
# sh ./workflow/02_workflow_massive_id.sh

# echo "Launching 03_workflow_taxo_enhancer.sh"
# sh ./workflow/03_workflow_taxo_enhancer.sh

# echo "Launching 04_workflow_dl_ressources.sh"
# sh ./workflow/04_workflow_dl_ressources.sh

# echo "Launching 05_workflow_make_adducts.sh"
# sh ./workflow/05_workflow_make_adducts.sh

# echo "Launching 06_workflow_annotate_mn_isdb.sh"
# sh ./workflow/06_workflow_annotate_mn_isdb.sh

# echo "Launching 07_workflow_annotate_sirius.sh"
# sh ./workflow/07_workflow_annotate_sirius.sh

# echo "Launching 08_workflow_chemo_info_fetcher.sh"
# sh ./workflow/08_workflow_chemo_info_fetcher.sh

# echo "Launching 09_workflow_memo.sh"
# sh ./workflow/09_workflow_memo.sh

echo "Launching 10_workflow_graph_builder.sh"
sh ./workflow/10_workflow_graph_builder.sh

echo "Done !"