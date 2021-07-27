from algosdk import template

from helpers import (
    account_balance,
    add_standalone_account,
    fund_account,
    process_transactions,
    suggested_params,
)


def _create_grouped_transactions(split_template, amount):
    """Create grouped transactions for the provided `split_template` and `amount`."""
    params = suggested_params()
    return split_template.get_split_funds_transaction(
        split_template.get_program(),
        amount,
        1,
        params.first,
        params.last,
        params.gh,
    )


def _create_split_template(
    owner,
    receiver_1,
    receiver_2,
    ratio_1=1,
    ratio_2=3,
    expiry_round=5000000,
    min_pay=3000,
    max_fee=2000,
):
    """Initialize split template from the provided arguments."""
    return template.Split(
        owner, receiver_1, receiver_2, ratio_1, ratio_2, expiry_round, min_pay, max_fee
    )


def setup_split_contract(amount=1000000, **kwargs):
    """Create split contract and send provided amount."""
    owner = kwargs.pop("owner", add_standalone_account()[1])
    receiver_1 = kwargs.pop("receiver_1", add_standalone_account()[1])
    receiver_2 = kwargs.pop("receiver_2", add_standalone_account()[1])

    split_template = _create_split_template(owner, receiver_1, receiver_2, **kwargs)
    escrow_address = split_template.get_address()
    fund_account(escrow_address)

    transactions = _create_grouped_transactions(split_template, amount)
    transaction_id = process_transactions(transactions)
    return owner, receiver_1, receiver_2, transaction_id


if __name__ == "__main__":
    _, local_owner = add_standalone_account()
    _, local_receiver_2 = add_standalone_account()
    amount = 5000000

    owner, receiver_1, receiver_2, transaction_id = setup_split_contract(
        amount=amount,
        owner=local_owner,
        receiver_2=local_receiver_2,
        ratio_1=3,
        ratio_2=7,
    )
    assert owner == local_owner
    assert receiver_2 == local_receiver_2

    print("amount: %s" % (amount,))
    print("owner: %s" % (account_balance(owner),))
    print("receiver_1: %s" % (account_balance(receiver_1),))
    print("receiver_2: %s" % (account_balance(receiver_2),))
    print("transaction_id: %s" % (transaction_id,))
