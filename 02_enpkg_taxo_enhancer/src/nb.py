import pandas as pd
import numpy as np
from pandas import json_normalize
import requests
import os
from taxo_resolver_wip import *
from pathlib import Path
import argparse
import textwrap
import yaml
import git
import opentree
from opentree import OT




from abstract_taxon import AbstractTaxon, Taxon



# We instantiate a Taxon object

taxon_a = Taxon(taxon_name="Arabidopsis thaliana")


taxon_a.taxon_name

taxon_a.get_taxon_name()


print(taxon_a)


tnrs = tnrs_lookup_oop(taxon=Taxon(taxon_name="Arabidopsis thaliana"))


tnrs.keys()



taxon_tnrs_matched = OT.tnrs_match(
    names = ['Arabidopsis thaliana'],
    context_name=None,
    do_approximate_matching=True,
    include_suppressed=False,
)
print(dir(taxon_tnrs_matched))

taxon_tnrs_matched.response_dict
taxon_tnrs_matched.taxon.uniq


print(dir(taxon_tnrs_matched.taxon))



print(taxon_tnrs_matched.taxon.ott_id)


df_species_tnrs_matched = json_normalize(
        taxon_tnrs_matched.response_dict, record_path=["results", "matches"]
    )