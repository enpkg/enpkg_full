from abc import ABC, abstractmethod


class AbstractTaxon(ABC):

    @abstractmethod
    def get_taxon_name(self) -> str:
        """
        Returns the taxon name of the sample.
        """
        pass
        # raise NotImplementedError("This method should be implemented by a child class.")


class OTLTaxonInfo:
    def __init__(
        self,
        ott_id: int,
        otol_domain: str,
        otol_kingdom: str,
        otol_phylum: str,
        otol_class: str,
        otol_order: str,
        otol_family: str,
        otol_tribe: str,
        otol_genus: str,
        otol_species: str,
        taxon_source: str,
        taxon_rank: str,
        search_string: str,
        score: float,
        matched_name: str,
        is_synonym: bool,
        is_approximate_match: bool,
    ):
        self.ott_id = ott_id
        self.otol_domain = otol_domain
        self.otol_kingdom = otol_kingdom
        self.otol_phylum = otol_phylum
        self.otol_class = otol_class
        self.otol_order = otol_order
        self.otol_family = otol_family
        self.otol_tribe = otol_tribe
        self.otol_genus = otol_genus
        self.otol_species = otol_species
        self.taxon_source = taxon_source
        self.taxon_rank = taxon_rank
        self.search_string = search_string
        self.score = score
        self.matched_name = matched_name
        self.is_synonym = is_synonym
        self.is_approximate_match = is_approximate_match

    def get_ott_id(self) -> int:
        """
        Returns the OpenTree of Life ID of the sample.
        """
        return self.ott_id

    def get_otol_domain(self) -> str:
        """
        Returns the OpenTree of Life domain of the sample.
        """
        return self.otol_domain

    def get_otol_kingdom(self) -> str:
        """
        Returns the OpenTree of Life kingdom of the sample.
        """
        return self.otol_kingdom

    def get_otol_phylum(self) -> str:
        """
        Returns the OpenTree of Life phylum of the sample.
        """
        return self.otol_phylum

    def get_otol_class(self) -> str:
        """
        Returns the OpenTree of Life class of the sample.
        """
        return self.otol_class

    def get_otol_order(self) -> str:
        """
        Returns the OpenTree of Life order of the sample.
        """
        return self.otol_order

    def get_otol_family(self) -> str:
        """
        Returns the OpenTree of Life family of the sample.
        """
        return self.otol_family

    def get_otol_tribe(self) -> str:
        """
        Returns the OpenTree of Life tribe of the sample.
        """
        return self.otol_tribe

    def get_otol_genus(self) -> str:
        """
        Returns the OpenTree of Life genus of the sample.
        """
        return self.otol_genus

    def get_otol_species(self) -> str:
        """
        Returns the OpenTree of Life species of the sample.
        """
        return self.otol_species

    def get_taxon_source(self) -> str:
        """
        Returns the taxon source of the sample.
        """
        return self.taxon_source

    def get_taxon_rank(self) -> str:
        """
        Returns the taxon rank of the sample.
        """
        return self.taxon_rank

    def get_search_string(self) -> str:
        """
        Returns the search string of the sample.
        """
        return self.search_string

    def get_score(self) -> float:
        """
        Returns the score of the sample.
        """
        return self.score

    def get_matched_name(self) -> str:
        """
        Returns the matched name of the sample.
        """
        return self.matched_name

    def get_is_synonym(self) -> bool:
        """
        Returns whether the sample is a synonym.
        """
        return self.is_synonym

    def get_is_approximate_match(self) -> bool:
        """
        Returns whether the sample is an approximate match.
        """
        return self.is_approximate_match

    def __str__(self):
        return f"The OpenTree of Life ID of this object is {self.ott_id}. \
        It is a {self.taxon_rank} from {self.taxon_source}."

    @classmethod
    def create_fake_otl_output(cls):
        """
        Creates a fake OTLOutput object.
        """
        return OTLTaxonInfo(
            "111111",
            "domain",
            "kingdom",
            "phylum",
            "class_",
            "order",
            "family",
            "tribe",
            "genus",
            "unique_name",
        )


class WDTaxonInfo:
    def __init__(self, wd_qid: str, wd_qid_url: str, wd_img_url: str):
        self.wd_qid = wd_qid
        self.wd_qid_url = wd_qid_url
        self.wd_img_url = wd_img_url

    def get_wd_qid(self) -> str:
        """
        Returns the Wikidata QID of Taxon.
        """
        return self.wd_qid

    def get_wd_qid_url(self) -> str:
        """
        Returns the Wikidata QID URL of Taxon.
        """
        return self.wd_qid_url

    def get_wd_img_url(self) -> str:
        """
        Returns the Wikidata image URL of Taxon.
        """
        return self.wd_img_url

    def __str__(self):
        return f"The Wikidata QID of this object is {self.wd_qid}."
