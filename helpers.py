import io
import os
import subprocess
from pathlib import Path

from algosdk import account, mnemonic
from algosdk.future.transaction import PaymentTxn
from algosdk.v2client import algod, indexer


## SANDBOX
def _call_sandbox_command(*args):
    """Call and return sandbox command composed from provided arguments."""
    return subprocess.Popen(
        [_sandbox_executable(), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _sandbox_directory():
    """Return full path to Algorand's sandbox executable.

    The location of sandbox directory is retrieved either from the SANDBOX_DIR
    environment variable or if it's not set then the location of sandbox directory
    is implied to be the sibling of this Django project in the directory tree.
    """
    return os.environ.get("SANDBOX_DIR") or str(
        Path(__file__).resolve().parent.parent / "sandbox"
    )


def _sandbox_executable():
    """Return full path to Algorand's sandbox executable."""
    return _sandbox_directory() + "/sandbox"


def _cli_passphrase_for_account(address):
    """Return passphrase for provided address."""
    process = _call_sandbox_command("goal", "account", "export", "-a", address)
    passphrase = ""
    output = [line for line in io.TextIOWrapper(process.stdout)]
    for line in output:
        parts = line.split('"')
        if len(parts) > 1:
            passphrase = parts[1]
    if passphrase == "":
        raise ValueError(
            "Can't retrieve passphrase from the address: %s\nOutput: %s"
            % (address, output)
        )
    return passphrase


## CLIENTS
def _algod_client():
    """Instantiate and return Algod client object."""
    algod_address = "http://localhost:4001"
    # algod_address = "http://127.0.0.1:45821"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    # algod_token = "5cc28c1e0334a1af1b93340ffe3b7cc9b9f723e283ada55b32ae197f807480e6"
    return algod.AlgodClient(algod_token, algod_address)


def _indexer_client():
    """Instantiate and return Indexer client object."""
    indexer_address = "http://localhost:8980"
    indexer_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    return indexer.IndexerClient(indexer_token, indexer_address)


## TRANSACTIONS
def _add_transaction(sender, receiver, passphrase, amount, note):
    """Create and sign transaction from provided arguments.

    Returned non-empty tuple carries field where error was raised and description.
    If the first item is None then the error is non-field/integration error.
    Returned two-tuple of empty strings marks successful transaction.
    """
    client = _algod_client()
    params = client.suggested_params()
    unsigned_txn = PaymentTxn(sender, params, receiver, amount, None, note.encode())
    signed_txn = unsigned_txn.sign(mnemonic.to_private_key(passphrase))
    transaction_id = client.send_transaction(signed_txn)
    _wait_for_confirmation(client, transaction_id, 4)
    return transaction_id


def _wait_for_confirmation(client, transaction_id, timeout):
    """
    Wait until the transaction is confirmed or rejected, or until 'timeout'
    number of rounds have passed.
    Args:
        transaction_id (str): the transaction to wait for
        timeout (int): maximum number of rounds to wait
    Returns:
        dict: pending transaction information, or throws an error if the transaction
            is not confirmed or rejected in the next timeout rounds
    """
    start_round = client.status()["last-round"] + 1
    current_round = start_round

    while current_round < start_round + timeout:
        try:
            pending_txn = client.pending_transaction_info(transaction_id)
        except Exception:
            return
        if pending_txn.get("confirmed-round", 0) > 0:
            return pending_txn
        elif pending_txn["pool-error"]:
            raise Exception("pool error: {}".format(pending_txn["pool-error"]))
        client.status_after_block(current_round)
        current_round += 1
    raise Exception(
        "pending tx not found in timeout rounds, timeout value = : {}".format(timeout)
    )


def process_transactions(transactions):
    """Send provided grouped `transactions` to network and wait for confirmation."""
    client = _algod_client()
    transaction_id = client.send_transactions(transactions)
    _wait_for_confirmation(client, transaction_id, 4)
    return transaction_id


## CREATING
def add_standalone_account():
    """Create standalone account and return two-tuple of its private key and address."""
    private_key, address = account.generate_account()
    return private_key, address


def fund_account(address, initial_funds=1000000000):
    """Fund provided `address` with `initial_funds` amount of microAlgos."""
    initial_funds_address = _initial_funds_address()
    if initial_funds_address is None:
        raise Exception("Initial funds weren't transferred!")
    _add_transaction(
        initial_funds_address,
        address,
        _cli_passphrase_for_account(initial_funds_address),
        initial_funds,
        "Initial funds",
    )


## RETRIEVING
def _initial_funds_address():
    """Get the address of initially created account having enough funds.

    Such an account is used to transfer initial funds for the accounts
    created in this tutorial.
    """
    return next(
        (
            account.get("address")
            for account in _indexer_client().accounts().get("accounts", [{}, {}])[1:-1]
            if account.get("created-at-round") == 0
            and account.get("status") == "Offline"
        ),
        None,
    )


def account_balance(address):
    """Return funds balance of the account having provided address."""
    account_info = _algod_client().account_info(address)
    return account_info.get("amount")


def suggested_params():
    """Return the suggested params from the algod client."""
    return _algod_client().suggested_params()
