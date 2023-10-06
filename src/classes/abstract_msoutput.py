from abc import ABC, abstractmethod


class AbstractMSOutput(ABC):

    def __init__(self, ms_output_name: str, ms_output_type: str, ms_output_polarity: str):
        self.ms_output_name = ms_output_name
        self.ms_output_type = ms_output_type

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


class MgfMSOutput(AbstractMSOutput):
    def __init__(self, ms_output_name: str, ms_output_type: str, ms_output_polarity: str, mgf_type: str, spectrum_list: list):
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
