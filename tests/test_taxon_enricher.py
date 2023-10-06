from src.taxo_enricher.taxo_enricher import tnrs_lookup, otl_taxon_lineage_appender, wd_taxo_fetcher
from src.classes.abstract_taxon import AbstractTaxon, OTLTaxonInfo, WDTaxonInfo


class Taxon(AbstractTaxon):
    def __init__(self, taxon_name: str):
        self.taxon_name = taxon_name

    def __str__(self):
        return f"The taxon name of this object is {self.taxon_name}."

    def get_taxon_name(self) -> str:
        """
        Returns the taxon name of the sample.
        """
        return self.taxon_name


def test_otl_taxon_lineage_appender():
    """
    Test that the taxonomic lineage of the taxon of interest is returned.
    """
    taxon_test = Taxon(taxon_name="Arabidopsis thaliana")
    taxon_lineage = otl_taxon_lineage_appender(taxon_test)
    assert taxon_lineage.get_ott_id()[0] == 309263, f"Expected 309263, but got {taxon_lineage.get_ott_id()[0]}"
    assert taxon_lineage.get_taxon_rank()[0] == 'species', f"Expected species, but got {taxon_lineage.get_taxon_rank()[0]}"


def test_wd_taxo_fetcher():
    """
    Test that the Wikidata information of the taxon of interest is returned.
    """
    wd_info = wd_taxo_fetcher(ott_id=309263)
    assert wd_info.get_wd_qid() == "Q158695", f"Expected Q158695, but got {wd_info.get_wd_qid()}"

