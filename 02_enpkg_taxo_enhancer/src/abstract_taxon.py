class AbstractTaxon:

    def get_taxon_name(self) -> str:
        """
        Returns the taxon name of the sample.
        """
        raise NotImplementedError(
            "This method should be implemented by a child class."
        )

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




        

class OTLOutput:

    def __init__(self, ott_id: int, domain: str, kingdom: str, phylum: str, class_: str, order: str, family: str, tribe: str, genus: str, unique_name: str):
        self.ott_id = ott_id
        self.domain = domain
        self.kingdom = kingdom
        self.phylum = phylum
        self.class_ = class_
        self.order = order
        self.family = family
        self.tribe = tribe
        self.genus = genus
        self.unique_name = unique_name

    def get_ott_id(self) -> int:
        """
        Returns the OpenTree of Life ID of the sample.
        """
        return self.ott_id
    
    def get_domain(self) -> str:
        """
        Returns the domain of the sample.
        """
        return self.domain

    def get_kingdom(self) -> str:
        """
        Returns the kingdom of the sample.
        """
        return self.kingdom

    def get_phylum(self) -> str:
        """
        Returns the phylum of the sample.
        """
        return self.phylum

    def get_class(self) -> str:
        """
        Returns the class of the sample.
        """
        return self.class_

    def get_order(self) -> str:
        """
        Returns the order of the sample.
        """
        return self.order

    def get_family(self) -> str:
        """
        Returns the family of the sample.
        """
        return self.family

    def get_tribe(self) -> str:
        """
        Returns the tribe of the sample.
        """
        return self.tribe

    def get_genus(self) -> str:
        """
        Returns the genus of the sample.
        """
        return self.genus

    def get_unique_name(self) -> str:
        """
        Returns the unique name of the sample.
        """
        return self.unique_name

    @classmethod
    def create_fake_otl_output(cls):
        """
        Creates a fake OTLOutput object.
        """
        return OTLOutput('111111', 'domain', 'kingdom', 'phylum', 'class_', 'order', 'family', 'tribe', 'genus', 'unique_name')
