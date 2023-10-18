from abc import ABC, abstractmethod
from matchms.networking import SimilarityNetwork
from matchms import Spectrum
from matchms.typing import SpectrumType
from typing import List


class AbstractMSOutput(ABC):
    """ Abstract class to represent a MS output.
    """

    # Here actually we want smt that is closer to and "interface" than an "abstractclass"
    # Interface : no implemented method. Only name of a thing with some methods
    # You cannot (or rather shouldnt) inherit an interface

    # For input object : interfaces

    # Below this is a constructor. I am still not suzre how they will be implemented so for now we comment
    # def __init__(self, ms_output_name: str, ms_output_type: str, ms_output_polarity: str):
    #     self.ms_output_name = ms_output_name
    #     self.ms_output_type = ms_output_type
    #     self.ms_output_polarity = ms_output_polarity

    @property
    def talk(self):
        return f"This is a MS output of type {self.get_ms_output_type()} named {self.get_ms_output_name()}."

    @abstractmethod
    def get_ms_output_name(self) -> str:
        """
        Returns the name of the MS output.
        """
        pass

    @abstractmethod
    def get_ms_output_type(self) -> str:
        """
        Returns the type of the MS output.
        """
        pass

    @abstractmethod
    def get_ms_output_polarity(self) -> str:
        """
        Returns the polarity of the MS output.
        """
        pass


class MSOutput(AbstractMSOutput):
    """ Class to represent a MS output.
    """

    def __init__(self, ms_output_name: str, ms_output_type: str, ms_output_polarity: str):
        self.ms_output_name = ms_output_name
        self.ms_output_type = ms_output_type
        self.ms_output_polarity = ms_output_polarity

    def get_ms_output_name(self) -> str:
        """
        Returns the name of the MS output.
        """
        return self.ms_output_name

    def get_ms_output_type(self) -> str:
        """
        Returns the type of the MS output.
        """
        return self.ms_output_type

    def get_ms_output_polarity(self) -> str:
        """
        Returns the polarity of the MS output.
        """
        return self.ms_output_polarity



class MgfOutput(MSOutput):
    """ Class to represent a MGF MS output.
    """

    def __init__(self, ms_output_name: str, ms_output_type: str,ms_output_polarity: str, mgf_type: str, spectrum_list: List[Spectrum]):
        super().__init__(ms_output_name, ms_output_type, ms_output_polarity)
        self.mgf_type = mgf_type
        self.spectrum_list = spectrum_list
        # https://matchms.readthedocs.io/en/latest/_modules/matchms/Spectrum.html#Spectrum
        # Make sure that the spectrum_list is a list of matchms Spectrum objects
        if len(spectrum_list) > 0:
            assert isinstance(spectrum_list[0], Spectrum), "spectrum_list should be a list of matchms Spectrum objects"


    def get_ms_output_name(self) -> str:
        """
        Returns the name of the MS output.
        """
        return self.ms_output_name

    def get_ms_output_type(self) -> str:
        """
        Returns the type of the MS output.
        """
        return self.ms_output_type

    def get_ms_output_polarity(self) -> str:
        """
        Returns the polarity of the MS output.
        """
        return self.ms_output_polarity

    def get_mgf_type(self) -> str:
        """
        Returns the type of the MGF file.
        """
        return self.mgf_type

    def get_spectrum_list(self) -> list:
        """
        Returns the list of spectra.
        """
        return self.spectrum_list


class MNOutput(MSOutput):
    """ Class to represent a Molecular Networking output.
    """

    def __init__(self, ms_output_name: str, ms_output_type: str, ms_output_polarity: str, input_file: object, ms_network: SimilarityNetwork):
        super().__init__(ms_output_name, ms_output_type, ms_output_polarity)
        self.input_file = input_file
        self.ms_network = ms_network

        # https://matchms.readthedocs.io/en/latest/_modules/matchms/networking/SimilarityNetwork.html
        # Make sure that the ms_network is a matchms SimilarityNetwork object
        assert isinstance(ms_network, SimilarityNetwork), "ms_network should be a matchms SimilarityNetwork object"

    def get_ms_output_name(self) -> str:
        """
        Returns the name of the MS output.
        """
        return self.ms_output_name

    def get_ms_output_type(self) -> str:
        """
        Returns the type of the MS output.
        """
        return self.ms_output_type

    def get_ms_output_polarity(self) -> str:
        """
        Returns the polarity of the MS output.
        """
        return self.ms_output_polarity

    def get_input_file(self) -> object:
        """
        Returns the input file.
        """
        return self.input_file

    def get_ms_network(self) -> object:
        """
        Returns the MS network.
        """
        return self.ms_network