"""
Template configuration for Syntasa functions.

This module shows how to handle configuration for your function using
environment variables (.env) or YAML configuration files (config.yaml).
"""

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class FunctionConfig:
    """
    Configuration for your Syntasa function.

    Configuration can be loaded from:
    1. Environment variables (.env file)
    2. YAML configuration file (config.yaml)
    3. Direct instantiation

    Example configuration is provided in:
    - .env.example (copy to .env)
    - config.example.yaml (copy to config.yaml)
    """

    # Example configuration fields - customize for your function
    project_id: str
    dataset_id: str
    table_name: str
    batch_size: int = 100
    timeout_seconds: Optional[int] = None

    @classmethod
    def from_env(cls) -> "FunctionConfig":
        """
        Load configuration from environment variables.

        Reads from .env file or environment variables:
        - GCP_PROJECT_ID
        - DATASET_ID
        - TABLE_ID
        - BATCH_SIZE (default: 100)
        - TIMEOUT_SECONDS (optional)

        Returns:
            FunctionConfig instance populated from environment.

        Example:
            >>> # Create a .env file with your configuration
            >>> config = FunctionConfig.from_env()
        """
        return cls(
            project_id=os.environ.get("GCP_PROJECT_ID", ""),
            dataset_id=os.environ.get("DATASET_ID", ""),
            table_name=os.environ.get("TABLE_ID", ""),
            batch_size=int(os.environ.get("BATCH_SIZE", "100")),
            timeout_seconds=(
                int(os.environ["TIMEOUT_SECONDS"])
                if "TIMEOUT_SECONDS" in os.environ
                else None
            ),
        )

    @classmethod
    def from_yaml(cls, config_path: str = "config.yaml") -> "FunctionConfig":
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to YAML config file (default: config.yaml)

        Returns:
            FunctionConfig instance populated from YAML.

        Example:
            >>> # Create config.yaml with your configuration
            >>> config = FunctionConfig.from_yaml("config.yaml")
        """
        import yaml

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        gcp = data.get("gcp", {})
        # processing = data.get("processing", {})

        return cls(
            project_id=gcp.get("project_id", ""),
            dataset_id=gcp.get("dataset_id", ""),
            table_name=gcp.get("table_name", ""),
        )
