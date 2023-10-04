from taxo_enricher import tnrs_lookup, otl_taxon_lineage_appender, wd_taxo_fetcher
from abstract_taxon import AbstractTaxon, Taxon, OTLTaxonInfo, WDTaxonInfo


# Instantiate a Taxon object with the taxon name of interest, here Arabidopsis thaliana

taxon_test = Taxon(taxon_name="Arabidopsis thaliana")

# Return the an OTLTaxonInfo object with the taxonomic lineage of the taxon of interest

taxon_lineage = otl_taxon_lineage_appender(taxon_test)

# Retrieve the ott_id of the taxon of interest

taxon_lineage.get_ott_id()

# Retrieve the taxon rank of the taxon of interest

taxon_lineage.get_taxon_rank()

# Return Wikidata information about the taxon of interest

wd_info = wd_taxo_fetcher(ott_id=taxon_lineage.get_ott_id()[0])

# Return the Wikidata QID of the taxon of interest

print(wd_info)
