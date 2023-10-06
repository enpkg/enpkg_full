import sys 
sys.path.append('../')


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



# Instantiate a Taxon object with the taxon name of interest, here Arabidopsis thaliana

taxon_test = Taxon(taxon_name="Arabidopsis thiana")

taxon_test.get_taxon_name()

print(taxon_test)

# Return the an OTLTaxonInfo object with the taxonomic lineage of the taxon of interest

taxon_lineage = otl_taxon_lineage_appender(taxon_test)

# Retrieve the ott_id of the taxon of interest

taxon_lineage.get_ott_id()[0]

# Retrieve the taxon rank of the taxon of interest

taxon_lineage.get_taxon_rank()[0]


# Return Wikidata information about the taxon of interest

wd_info = wd_taxo_fetcher(ott_id=taxon_lineage.get_ott_id()[0])

# Return the Wikidata QID of the taxon of interest

print(wd_info)


wd_info.get_wd_qid()
