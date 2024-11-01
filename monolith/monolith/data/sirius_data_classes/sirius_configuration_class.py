"""Configuration for Sirius."""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class SiriusEnricherConfig:
    """Dataclass for the Sirius Enricher configuration."""

    path_to_sirius: str
    output_directory: str
    sirius_command_arg: str
    recompute: bool
    zip_output: bool
    sirius_user_env: str
    sirius_password_env: str

    @classmethod
    def from_dict(cls, config: dict) -> "SiriusEnricherConfig":
        """Create a SiriusEnricherConfig from a dictionary."""
        return cls(
            path_to_sirius=config["paths"]["path_to_sirius"],
            output_directory=config["paths"]["output_directory"],
            sirius_command_arg=config["options"]["sirius_command_arg"],
            recompute=config["options"]["recompute"],
            zip_output=config["options"]["zip_output"],
            sirius_user_env=config["options"]["sirius_user_env"],
            sirius_password_env=config["options"]["sirius_password_env"],
        )

    @property
    def user(self) -> str:
        """Returns the user for the Sirius API."""
        user: Optional[str] = os.environ.get(self.sirius_user_env)
        if user is None:
            raise RuntimeError(f"Environment variable {self.sirius_user_env} not set.")

        return user

    @property
    def password(self) -> str:
        """Returns the password for the Sirius API."""
        password: Optional[str] = os.environ.get(self.sirius_password_env)
        if password is None:
            raise RuntimeError(
                f"Environment variable {self.sirius_password_env} not set."
            )

        return password
