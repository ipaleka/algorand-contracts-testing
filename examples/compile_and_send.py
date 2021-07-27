#!/usr/bin/env python3

import uuid, base64

from pyteal import *
from algosdk import algod, transaction, account, mnemonic

from helpers import (
    add_standalone_account,
    compile_smart_contract,
    create_and_fund_sender,
    process_transaction,
    suggested_params,
)
from periodic_payment import periodic_payment  #, tmpl_lease


sender_key, sender = create_and_fund_sender()
_teal_bytes = compile_smart_contract(periodic_payment)
logic_signature = transaction.LogicSig(_teal_bytes)
logic_signature.sign(sender_key)

params = suggested_params()
start_round = params.last - (params.last % 1000)
end_round = start_round + 1000
fee = 1000
amount = 2000

_, receiver = add_standalone_account()
# lease = base64.b64decode(tmpl_lease.byte_str)

print(params.last)
print(start_round)
print(end_round)
# print(lease)

# create a transaction
payment_transaction = transaction.PaymentTxn(
    sender,
    fee,
    start_round,
    end_round,
    params.gh,
    receiver,
    amount,
    flat_fee=True,
    # lease=lease,
)

# def __init__(self, sender, fee, first, last, gh, receiver, amt,
#                 close_remainder_to=None, note=None, gen=None, flat_fee=False,
#                 lease=None, rekey_to=None):


transaction_id = process_transaction(
    transaction.LogicSigTransaction(payment_transaction, logic_signature)
)
print("Transaction ID: " + transaction_id)
