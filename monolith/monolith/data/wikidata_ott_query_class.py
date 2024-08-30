"""Submodule providing the data class to handle a response from the wikidata ott query."""

from dataclasses import dataclass


@dataclass
class WikidataOTTQuery:
    """Class to handle a response from the wikidata ott query."""

    ott: int
    wd: str
    img: str

    @staticmethod
    def from_dict(data: dict) -> "WikidataOTTQuery":
        """Creates an instance of WikidataOTTQuery from a dictionary.

        Args:
            data (dict): A dictionary containing the data.

        Returns:
            WikidataOTTQuery: An instance of the WikidataOTTQuery class.
        """
        data = data["results"]["bindings"][0]

        return WikidataOTTQuery(
            ott=int(data["ott"]["value"]),
            wd=data["wd"]["value"],
            img=data["img"]["value"] if "img" in data else None,
        )
