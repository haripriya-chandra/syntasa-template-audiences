import pytest
import os
from unittest.mock import patch
from typing import Generator


@pytest.fixture(autouse=True)
def mock_env_vars() -> Generator[None, None, None]:
    """
    Automatically patch os.environ for every test.
    """
    with patch.dict(os.environ, {}, clear=True):
        os.environ["SECRET_PROVIDER"] = "environment"
        yield
