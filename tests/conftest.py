"""Configuration module for pytest."""

import os
import pytest
from pathlib import Path
from xprocess import ProcessStarter


@pytest.fixture(autouse=True, scope="session")
def sandbox(xprocess):
    class Starter(ProcessStarter):
        pattern = "^.* started!.*$"

        # retrieve sandbox dir from environment variable
        # or use default one (sibling of this project's root)
        sandbox_dir = (
            os.environ.get("SANDBOX_DIR")
            or str(Path(__file__).resolve().parent.parent.parent / "sandbox")
        )

        # command to start process
        args = [sandbox_dir + "/sandbox", "up"]

    # ensure process is running
    xprocess.ensure("sandbox", Starter)

    yield

    # clean up whole process tree afterwards
    xprocess.getinfo("sandbox").terminate()
