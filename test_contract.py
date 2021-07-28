"""Testing module for smart contract domain logic."""

import pytest

from contract import setup_split_contract
from helpers import add_standalone_account


class TestSplitContractExistingAccount:
    """Base class for testing the split smart contract with pre-existing accounts."""

    def setup_method(self):
        """Create owner and receivers accounts before each test."""
        _, self.owner = add_standalone_account()
        _, self.receiver_1 = add_standalone_account()
        _, self.receiver_2 = add_standalone_account()

    # def teardown_method(self):
    #     """"""

    def test_created_contract_uses_existing_accounts_when_they_are_provided(self):
        split_contract = setup_split_contract(
            owner=self.owner, receiver_1=self.receiver_1, receiver_2=self.receiver_2
        )
        assert split_contract.owner == self.owner
        assert split_contract.receiver_1 == self.receiver_1
        assert split_contract.receiver_2 == self.receiver_2

    # @pytest.mark.parametrize(
    #     "dest,count",
    #     [
    #         ("newblog", 1),
    #     ],
    # )
    # def test_main_blog_page_links_to_other_blog_page(self, dest, count):
    #     pass
