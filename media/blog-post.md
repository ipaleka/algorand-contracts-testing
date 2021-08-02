![py-algorand-sdk-pyteal-pytest](https://github.com/ipaleka/algorand-contracts-testing/blob/main/media/py-algorand-sdk-pyteal-pytest.png?raw=true)

# Introduction

In this tutorial we're going to create two smart contracts using two different approaches. The first smart contract will be created using predefined template that ships with the [Python Algorand SDK](https://github.com/algorand/py-algorand-sdk), while the other will be created using [PyTeal](https://github.com/algorand/pyteal) package.

All the source code for this tutorial is available in a [public GitHub repository](https://github.com/ipaleka/algorand-contracts-testing).


# Requirements

This project uses a [Python](https://www.python.org/) wrapper around [Algorand SDK](https://developer.algorand.org/docs/reference/sdks/), so you should have Python 3 installed on your system. Also, this project uses `python3-venv` package for creating virtual environments and you have to install it if it's not already installed in your system. For a Debian/Ubuntu based systems, you can do that by issuing the following command:

```bash
$ sudo apt-get install python3-venv
```

If you're going to clone the Algorand Sandbox (as opposed to just download its installation archive), you'll also need [Git distributed version control system](https://git-scm.com/).


# Setup and run Algorand Sandbox

Let's create the root directory named `algorand` where this project and Sandbox will reside.

```bash
cd ~
mkdir algorand
cd algorand
```

This project depends on [Algorand Sandbox](https://github.com/algorand/sandbox) running in your computer. Use its README for the instructions on how to prepare its installation on your system. You may clone the Algorand Sandbox repository with the following command:

```bash
git clone https://github.com/algorand/sandbox.git
```

The Sandbox Docker containers will be started automatically by running the tests from this project. As starting them for the first time takes time, it's advisable to start the Sandbox before the tests by issuing the following command:

```bash
./sandbox/sandbox up
```


---
**Note**

This project's code implies that the Sandbox executable is in the `sandbox` directory which is a sibling to this project's directory:

```bash
$ tree -L 1
.
├── algorand-contracts-testing
└── sandbox
```

If that's not the case, then you should set `SANDBOX_DIR` environment variable holding sandbox directory before running this project's tests:

```bash
export SANDBOX_DIR="/home/ipaleka/dev/algorand/sandbox
```

---

# Create and activate Python virtual environment

Every Python-based project should run inside its own virtual environment. Create and activate one for this project with:

```bash
python3 -m venv algcontestvenv
source algcontestvenv/bin/activate
```

After successful activation, the environment name will be presented at your prompt and that indicates that all the Python package installations issued will reside only in that environment.

```bash
(algcontestvenv) $
```

We're ready now to install our project's main dependencies: the [Python Algorand SDK](https://github.com/algorand/py-algorand-sdk),  [PyTeal](https://github.com/algorand/pyteal) and [pytest](https://docs.pytest.org/).


```bash
(algcontestvenv) $ pip install py-algorand-sdk pyteal pytest
```
