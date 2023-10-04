from src.abstract_taxon import AbstractTaxon, Taxon
from src.taxo_resolver_wip import tnrs_lookup_oop

def test_taxon_name():
    taxon = Taxon(taxon_name="Arabidopsis thaliana")
    assert taxon.get_taxon_name() == "Arabidopsis thaliana"

def test_tnrs_lookup():
    tnrs_lookup(taxon=Taxon(taxon_name="Arabidopsis thaliana"))


