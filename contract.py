"""Module containing domain logic for smart contract creation."""

import json

from algosdk import template

from helpers import (
    account_balance,
    add_standalone_account,
    fund_account,
    process_transactions,
    suggested_params,
    transaction_info,
)


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


def create_split_transaction(split_contract, amount=1000000):
    """Create transaction with provided amount for provided split contract."""
    transactions = _create_grouped_transactions(split_contract, amount)
    transaction_id = process_transactions(transactions)
    return transaction_id


def setup_split_contract(**kwargs):
    """Create split contract and send provided amount."""
    owner = kwargs.pop("owner", add_standalone_account()[1])
    receiver_1 = kwargs.pop("receiver_1", add_standalone_account()[1])
    receiver_2 = kwargs.pop("receiver_2", add_standalone_account()[1])

    split_contract = _create_split_contract(owner, receiver_1, receiver_2, **kwargs)
    escrow_address = split_contract.get_address()
    fund_account(escrow_address)
    return split_contract


if __name__ == "__main__":
    _, local_owner = add_standalone_account()
    _, local_receiver_2 = add_standalone_account()
    amount = 5000000

    split_contract = setup_split_contract(
        owner=local_owner,
        receiver_2=local_receiver_2,
        rat_1=3,
        rat_2=7,
    )
    assert split_contract.owner == local_owner
    assert split_contract.receiver_2 == local_receiver_2

    transaction_id = create_split_transaction(split_contract, amount=amount)

    print("amount: %s" % (amount,))
    print("owner: %s" % (account_balance(split_contract.owner),))
    print("receiver_1: %s" % (account_balance(split_contract.receiver_1),))
    print("receiver_2: %s" % (account_balance(split_contract.receiver_2),))
    print(json.dumps(transaction_info(transaction_id), indent=2))
