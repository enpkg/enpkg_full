from abc import ABC, abstractmethod

from matchms.importing import load_from_mgf
from pydantic import BaseModel

from monolith.data.analysis_loader import AnalysisLoader
from monolith.configuration.network_enricher_config import NetworkEnricherConfig
from monolith.pipeline.taxonomical_enrichment_step import TaxonomicalEnrichmentStep
from monolith.pipeline.molecular_networking_step import MolecularNetworkingStep
        


if __name__ == "__main__":
    import pandas as pd

    analysis = AnalysisLoader.from_files(
        path_to_spectra="/home/llegregam/git_projects/enpkg_full/monolith/data/tests/actea_EtOAc-1_pos.mgf",
        path_to_metadata="/home/llegregam/git_projects/enpkg_full/monolith/data/tests/qualome_metadata.tsv",
        ionization_mode="pos"
    )

    taxonomical_enrichment_step = TaxonomicalEnrichmentStep()
    molecular_networking_step = MolecularNetworkingStep(
        NetworkEnricherConfig(
            mn_msms_mz_tol=0.01,
            mn_score_cutoff=0.7,
            mn_top_n=15,
            mn_max_links=10
        )
    )
    
    # for step in [taxonomical_enrichment_step, molecular_networking_step]:
    for step in [molecular_networking_step]:
        print(f"Running step: {step.name()}")
        if step.can_run(analysis):
            analysis = step.process(analysis)
            print(f"Step {step.name()} completed.")
            step.export_components(analysis, "/home/llegregam/git_projects/enpkg_full/src/monolith/pipeline/test_components.tsv")
        else:
            print(f"Step {step.name()} cannot run on this analysis.")

        
    
    # print(f"OTT matches for analysis: {analysis.ott_matches}")
    # print(f"Loaded {len(analysis.spectra)} spectra from MGF file.")
    # print(f"Molecular network nodes: {analysis.molecular_network.nodes}")