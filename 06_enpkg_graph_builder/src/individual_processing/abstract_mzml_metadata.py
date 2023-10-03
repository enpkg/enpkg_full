


class AbstractMzXMLMetadata:

    def get_massive_id(self) -> str:
        """
        Returns the MassIVE ID of the sample.
        """        
        raise NotImplementedError(
            "This method should be implemented by a child class."
        )
    
    def get_sample_id(self) -> str:
        """
        Returns the sample ID of the sample.
        """
        raise NotImplementedError(
            "This method should be implemented by a child class."
        )

    
        