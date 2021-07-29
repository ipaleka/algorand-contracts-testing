"""Testing module for smart contract domain logic."""

import base64

import pytest
from algosdk import constants
from algosdk.encoding import encode_address, is_valid_address
from algosdk.error import TemplateInputError

from contract import create_split_transaction, setup_split_contract
from helpers import (
    account_balance,
    add_standalone_account,
    call_sandbox_command,
    transaction_info,
)


def setup_module(module):
    """Ensure Algorand Sandbox is up prior to running tests from this module."""
    call_sandbox_command("up")


class TestSplitContract:
    """Base class for testing the split smart contract with pre-existing accounts."""

    def setup_method(self):
        """Create owner and receivers accounts before each test."""
        _, self.owner = add_standalone_account()
        _, self.receiver_1 = add_standalone_account()
        _, self.receiver_2 = add_standalone_account()

    def _create_split_contract(self, **kwargs):
        """Create contract from pre-existing accounts and provided named arguments."""
        return setup_split_contract(
            owner=self.owner,
            receiver_1=self.receiver_1,
            receiver_2=self.receiver_2,
            **kwargs,
        )

    def test_contract_creates_new_accounts(self):
        contract = setup_split_contract()
        assert contract.owner != self.owner
        assert contract.receiver_1 != self.receiver_1
        assert contract.receiver_2 != self.receiver_2

    def test_contract_uses_existing_accounts_when_they_are_provided(self):
        contract = self._create_split_contract()
        assert contract.owner == self.owner
        assert contract.receiver_1 == self.receiver_1
        assert contract.receiver_2 == self.receiver_2

    def test_min_pay(self):
        min_pay = 250000
        contract = self._create_split_contract(min_pay=min_pay, rat_1=1, rat_2=3)
        amount = 2000000
        create_split_transaction(contract, amount)
        assert account_balance(contract.receiver_1) > min_pay

    def test_min_pay_failed_transaction(self):
        min_pay = 300000
        contract = self._create_split_contract(min_pay=min_pay, rat_1=1, rat_2=3)
        amount = 1000000

        with pytest.raises(TemplateInputError) as exception:
            create_split_transaction(contract, amount)
        assert (
            str(exception.value)
            == f"the amount paid to receiver_1 must be greater than {min_pay}"
        )

    def test_max_fee_failed_transaction(self):
        max_fee = 500
        contract = self._create_split_contract(max_fee=max_fee, rat_1=1, rat_2=3)
        amount = 1000000

        with pytest.raises(TemplateInputError) as exception:
            create_split_transaction(contract, amount)
        assert (
            str(exception.value)
            == f"the transaction fee should not be greater than {max_fee}"
        )

    @pytest.mark.parametrize(
        "amount,rat_1,rat_2",
        [
            (1000000, 1, 2),
            (1000033, 1, 3),
            (1000000, 2, 5),
        ],
    )
    def test_invalid_ratios_for_amount(self, amount, rat_1, rat_2):
        contract = self._create_split_contract(rat_1=rat_1, rat_2=rat_2)
        with pytest.raises(TemplateInputError) as exception:
            create_split_transaction(contract, amount)
        assert (
            str(exception.value)
            == f"the specified amount cannot be split into two parts with the ratio {rat_1}/{rat_2}"
        )

    @pytest.mark.parametrize(
        "amount,rat_1,rat_2",
        [
            (1000000, 1, 3),
            (999999, 1, 2),
            (1400000, 2, 5),
            (1000000, 1, 9),
            (900000, 4, 5),
            (1200000, 5, 1),
        ],
    )
    def test_balances_of_involved_accounts(self, amount, rat_1, rat_2):
        contract = self._create_split_contract(rat_1=rat_1, rat_2=rat_2)
        assert account_balance(contract.owner) == 0
        assert account_balance(contract.receiver_1) == 0
        assert account_balance(contract.receiver_2) == 0

        escrow = contract.get_address()
        escrow_balance = account_balance(escrow)

        create_split_transaction(contract, amount)
        assert account_balance(escrow) == escrow_balance - amount - contract.max_fee
        assert account_balance(contract.owner) == 0
        assert account_balance(contract.receiver_1) == rat_1 * amount / (rat_1 + rat_2)
        assert account_balance(contract.receiver_2) == rat_2 * amount / (rat_1 + rat_2)

    def test_contract_transaction(self):
        contract = setup_split_contract()
        transaction_id = create_split_transaction(contract, 1000000)
        transaction = transaction_info(transaction_id)
        assert transaction.get("transaction").get("tx-type") == constants.payment_txn
        assert transaction.get("transaction").get("sender") == contract.get_address()
        assert (
            transaction.get("transaction").get("payment-transaction").get("receiver")
            == contract.receiver_1
        )
        assert is_valid_address(
            encode_address(
                base64.b64decode(transaction.get("transaction").get("group"))
            )
        )
