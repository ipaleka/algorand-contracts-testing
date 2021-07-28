"""Configuration module for pytest."""

import pytest
from xprocess import ProcessStarter

from helpers import sandbox_directory


@pytest.fixture(autouse=True, scope="session")
def sandbox(xprocess):
    class Starter(ProcessStarter):
        pattern = "^.* started!.*$"

        # command to start process
        args = [sandbox_directory() + "/sandbox", "up"]

    # ensure process is running
    xprocess.ensure("sandbox", Starter)

    yield

    # clean up whole process tree afterwards
    xprocess.getinfo("sandbox").terminate()
