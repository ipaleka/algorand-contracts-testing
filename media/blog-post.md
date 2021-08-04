![py-algorand-sdk-pyteal-pytest](https://github.com/ipaleka/algorand-contracts-testing/blob/main/media/py-algorand-sdk-pyteal-pytest.png?raw=true)

# Introduction

In this tutorial, we're going to create two smart contracts using two different approaches. The first smart contract will be created using a predefined template that ships with the [Python Algorand SDK](https://github.com/algorand/py-algorand-sdk), while the other will be created using [PyTeal](https://github.com/algorand/pyteal) package.

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

The Sandbox Docker containers will be started automatically by running the tests from this project. As starting them for the first time takes time, it's advisable to start the Sandbox before running the tests by issuing `./sandbox/sandbox up`:

![Starting Sandbox](https://github.com/ipaleka/algorand-contracts-testing/blob/main/media/starting-sandbox.png?raw=true)

The Sandbox will be up and running after minute or two:

![Up and running Sandbox](https://github.com/ipaleka/algorand-contracts-testing/blob/main/media/sandbox-up-and-running.png?raw=true)

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
export SANDBOX_DIR="/home/ipaleka/dev/algorand/sandbox"
```

---

# Create and activate Python virtual environment

Every Python-based project should run inside its own virtual environment. Create and activate one for this project with:

```bash
python3 -m venv contractsvenv
source contractsvenv/bin/activate
```

After successful activation, the environment name will be presented at your prompt and that indicates that all the Python package installations issued will reside only in that environment.

```bash
(contractsvenv) $
```

We're ready now to install our project's main dependencies: the [Python Algorand SDK](https://github.com/algorand/py-algorand-sdk),  [PyTeal](https://github.com/algorand/pyteal) and [pytest](https://docs.pytest.org/).


```bash
(contractsvenv) $ pip install py-algorand-sdk pyteal pytest
```


# Creating a smart contract from a template

Our first smart contract will be a split payment contract where a transaction amount is split between two receivers at provided ratio. For that purpose we created a function that accepts contract's data as arguments:


```python
from algosdk import template

def _create_split_contract(
    owner,
    receiver_1,
    receiver_2,
    rat_1=1,
    rat_2=3,
    expiry_round=5000000,
    min_pay=3000,
    max_fee=2000,
):
    """Create and return split template instance from the provided arguments."""
    return template.Split(
        owner, receiver_1, receiver_2, rat_1, rat_2, expiry_round, min_pay, max_fee
    )
```

We use template's instance method `get_split_funds_transaction` in order to create a grouped transactions based on provided amount:

```python
def _create_grouped_transactions(split_contract, amount):
    """Create grouped transactions for the provided `split_contract` and `amount`."""
    params = suggested_params()
    return split_contract.get_split_funds_transaction(
        split_contract.get_program(),
        amount,
        1,
        params.first,
        params.last,
        params.gh,
    )
```

That grouped transactions instance is then sent to `process_transactions` helper function that is responsible for sending our smart contract to the Algorand blockchain.

```python
def _algod_client():
    """Instantiate and return Algod client object."""
    algod_address = "http://localhost:4001"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    return algod.AlgodClient(algod_token, algod_address)

def process_transactions(transactions):
    """Send provided grouped `transactions` to network and wait for confirmation."""
    client = _algod_client()
    transaction_id = client.send_transactions(transactions)
    _wait_for_confirmation(client, transaction_id, 4)
    return transaction_id
```

---
**Note**

Some helper functions aren't shown here in the tutorial for the sake of simplicity. Please take a look at the [project's repository](https://github.com/ipaleka/algorand-contracts-testing) for their implementation.

---

# Creating a smart contract with PyTeal

Our second smart contract is a simple bank for account contract where only a pre-defined receiver is able to withdraw funds from the smart contract:

```python
def bank_for_account(receiver):
    """Only allow receiver to withdraw funds from this contract account.

    Args:
        receiver (str): Base 32 Algorand address of the receiver.
    """
    is_payment = Txn.type_enum() == TxnType.Payment
    is_single_tx = Global.group_size() == Int(1)
    is_correct_receiver = Txn.receiver() == Addr(receiver)
    no_close_out_addr = Txn.close_remainder_to() == Global.zero_address()
    no_rekey_addr = Txn.rekey_to() == Global.zero_address()
    acceptable_fee = Txn.fee() <= Int(BANK_ACCOUNT_FEE)

    return And(
        is_payment,
        is_single_tx,
        is_correct_receiver,
        no_close_out_addr,
        no_rekey_addr,
        acceptable_fee,
    )
```

The above PyTeal code is then compiled into TEAL byte-code using PyTeal's `compileTeal` function and a signed logic signature is created from the compiled source:

```python
def setup_bank_contract(**kwargs):
    """Initialize and return bank contract for provided receiver."""
    receiver = kwargs.pop("receiver", add_standalone_account()[1])

    teal_source = compileTeal(
        bank_for_account(receiver),
        mode=Mode.Signature,
        version=3,
    )
    logic_sig, escrow_address = signed_logic_signature(teal_source)
    fund_account(escrow_address)
    return logic_sig, escrow_address, receiver

def create_bank_transaction(logic_sig, escrow_address, receiver, amount, fee=1000):
    """Create bank transaction with provided amount."""
    params = suggested_params()
    params.fee = fee
    params.flat_fee = True
    payment_transaction = create_payment_transaction(
        escrow_address, params, receiver, amount
    )
    transaction_id = process_logic_sig_transaction(logic_sig, payment_transaction)
    return transaction_id
```

As you may notice, we provide some funds to the escrow account after its creation by calling the `fund_account` function.

Among other used functions, the following helper functions are used for connecting to the blockchain and processing the smart contract:

```python
import base64

from algosdk import account
from algosdk.future.transaction import LogicSig, LogicSigTransaction, PaymentTxn


def create_payment_transaction(escrow_address, params, receiver, amount):
    """Create and return payment transaction from provided arguments."""
    return PaymentTxn(escrow_address, params, receiver, amount)


def process_logic_sig_transaction(logic_sig, payment_transaction):
    """Create logic signature transaction and send it to the network."""
    client = _algod_client()
    logic_sig_transaction = LogicSigTransaction(payment_transaction, logic_sig)
    transaction_id = client.send_transaction(logic_sig_transaction)
    _wait_for_confirmation(client, transaction_id, 4)
    return transaction_id

def _compile_source(source):
    """Compile and return teal binary code."""
    compile_response = _algod_client().compile(source)
    return base64.b64decode(compile_response["result"])

def signed_logic_signature(teal_source):
    """Create and sign logic signature for provided `teal_source`."""
    compiled_binary = _compile_source(teal_source)
    logic_sig = LogicSig(compiled_binary)
    private_key, escrow_address = account.generate_account()
    logic_sig.sign(private_key)
    return logic_sig, escrow_address
```

That's all we need to prepare our smart contracts for testing.


# Structure of a testing module

In order for our `test_contracts.py` testing module to be discovered by pytest test runner, we named it with `test_` prefix. For a large-scale project, you may create `tests` directory and place your testing modules in it.

Pytest allows running a special function before the very first test from the current module is run. In our testing module, we use it to run the Sandbox daemon:

```python
from helpers import call_sandbox_command

def setup_module(module):
    """Ensure Algorand Sandbox is up prior to running tests from this module."""
    call_sandbox_command("up")
```

A test suite for each of the two smart contracts is created and the `setup_method` is run before each test in the suite. We use that setup method to create the needed accounts:

```python
from contracts import setup_bank_contract, setup_split_contract
from helpers import add_standalone_account

class TestBankContract:
    """Class for testing the bank for account smart contract."""

    def setup_method(self):
        """Create receiver account before each test."""
        _, self.receiver = add_standalone_account()

    def _create_bank_contract(self, **kwargs):
        """Helper method for creating bank contract from pre-existing receiver

        and provided named arguments.
        """
        return setup_bank_contract(receiver=self.receiver, **kwargs)


class TestSplitContract:
    """Class for testing the split smart contract."""

    def setup_method(self):
        """Create owner and receivers accounts before each test."""
        _, self.owner = add_standalone_account()
        _, self.receiver_1 = add_standalone_account()
        _, self.receiver_2 = add_standalone_account()

    def _create_split_contract(self, **kwargs):
        """Helper method for creating split contract from pre-existing accounts

        and provided named arguments.
        """
        return setup_split_contract(
            owner=self.owner,
            receiver_1=self.receiver_1,
            receiver_2=self.receiver_2,
            **kwargs,
        )
```

Instead of repeating the code, we've created a helper method in each suite. That way we adhere to the [DRY principle](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself).


---
**Note**

We use only the `setup_method` that is executed **before** each test. In order to execute some code **after** each test, use the `teardown_method`. The same goes for the module level with `teardown_module` function.

---


# Writing our tests


```python

```