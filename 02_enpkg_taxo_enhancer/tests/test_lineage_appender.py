from src.abstract_taxon import AbstractTaxon
from src.taxo_resolver import taxa_lineage_appender


class TaxonPatch(AbstractTaxon):

    def get_taxon_name(self) -> str:
        """
        Returns the taxon name of the sample.
        """
        return "Arabidopsis thaliana"


def test_taxon_name():
    taxon_metadata_patch = TaxonMetadataPatch()
    assert taxon_metadata_patch.get_taxon_name() == "Arabidopsis thaliana"

# def test_taxa_lineage_appender():
#     taxon_metadata_patch = TaxonMetadataPatch()
#     taxo_df = taxa_lineage_appender(
#         taxon_metadata_patch, True, "path_to_results_folders", "directory"
#     )
