from abc import ABC, abstractmethod


class AbstractMSOutput(ABC):
    """ Abstract class to represent a MS output.
    """

    def __init__(self, ms_output_name: str, ms_output_type: str, ms_output_polarity: str):
        self.ms_output_name = ms_output_name
        self.ms_output_type = ms_output_type
        self.ms_output_polarity = ms_output_polarity

    @property
    def talk(self):
        return f"This is a MS output of type {self.ms_output_type} named {self.ms_output_name}."

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


class MgfOutput(AbstractMSOutput):
    """ Class to represent a MGF MS output.
    """

    def __init__(self, ms_output_name: str, ms_output_type: str,ms_output_polarity: str, mgf_type: str, spectrum_list: list):
        super().__init__(ms_output_name, ms_output_type, ms_output_polarity)
        self.mgf_type = mgf_type
        self.spectrum_list = spectrum_list

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


class MNOutput(AbstractMSOutput):
    """ Class to represent a Molecular Networking output.
    """

    def __init__(self, ms_output_name: str, ms_output_type: str, ms_output_polarity: str, input_file: object, ms_network: object):
        super().__init__(ms_output_name, ms_output_type, ms_output_polarity)
        self.input_file = input_file
        self.ms_network = ms_network

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