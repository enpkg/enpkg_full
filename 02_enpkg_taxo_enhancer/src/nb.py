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


tnrs_lookup_oop(taxon=Taxon(taxon_name="Arabidopsis thaliana"))
