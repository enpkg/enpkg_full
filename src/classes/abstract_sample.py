from abc import ABC, abstractmethod


class AbstractSample(ABC):

    @abstractmethod
    def get_sample_name(self) -> str:
        """
        Returns the name of the sample.
        """
        pass

    @abstractmethod
    def get_sample_id(self) -> int:
        """
        Returns the id of the sample.
        """
        pass

