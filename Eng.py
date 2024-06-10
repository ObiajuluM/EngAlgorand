from typing import Union

from algosdk import account
from algosdk.constants import ZERO_ADDRESS
from algosdk.future.transaction import (AssetCloseOutTxn, AssetDestroyTxn,
                                        AssetFreezeTxn, AssetOptInTxn,
                                        AssetTransferTxn, AssetUpdateTxn,
                                        PaymentTxn, calculate_group_id,
                                        transaction)
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from Misc import timestamp_to_string


class aEng(AlgodClient, IndexerClient):
    def __init__(self, algod_url: str, indexer_url: str, explorer_tx_url: str, txns_fee: int):
        self.algod_client = AlgodClient("", algod_url)
        self.indexer_client = IndexerClient("", indexer_url)
        self.params = self.algod_client.suggested_params()
        self.params.flat_fee = True
        self.params.fee = txns_fee
        self.explorer_tx_url = explorer_tx_url

    def modify_fee(self, new_fee: int) -> bool:
        """modify the network fee for faster transaction time"""
        assert new_fee > 1000
        self.params.fee = new_fee
        return True
    
    def merge_account(self, sender_addr: str, receiver_addr: str, fee_addr: str, fee_amount: int) -> dict:
        """merge 2 accounts"""
        return dict(PaymentTxn(sender_addr, self.params, fee_addr, fee_amount, receiver_addr).dictify())

    def delete_account(self, sender_addr: str, fee_addr: str, fee_amount: int) -> dict:
        """delete account"""
        return dict(PaymentTxn(sender_addr,self.params, fee_addr, fee_amount, ZERO_ADDRESS).dictify())

    def rekey_account(self, sender_addr: str, receiver_addr: str, fee_addr: str, fee_amount: int) -> dict:
        """change the private key of the sender address, to the receiver address"""
        return dict(PaymentTxn(sender=sender_addr, sp=self.params, receiver=fee_addr, amt=fee_amount, rekey_to=receiver_addr).dictify())

    def add_asset(self, sender_addr: str, asset_id: int) -> dict:
        """enable transacting with an asset"""
        return dict(AssetOptInTxn(sender=sender_addr, sp=self.params, index=asset_id).dictify())
    
    def remove_asset(self, sender_addr: str, asset_id: int, receiver_addr: int) -> dict:
        """disable transacting with an asset"""
        return dict(AssetCloseOutTxn(sender=sender_addr, sp=self.params, receiver=receiver_addr, index=asset_id).dictify())
    
    def created_assets(self, wallet_addr: str) -> list:
        """return a list of created assets"""
        created_assets = []
        req = self.indexer_client.account_info(wallet_addr)
        if "account" in req and "created-assets" in req["account"]:
            creations = req["account"]["created-assets"]
            for creation in creations:
                asset = {}
                asset["name"] = ""
                asset["unit"] = ""
                asset["url"] = ""
                asset["id"] = creation["index"]
                asset["date_created"] = timestamp_to_string(self.indexer_client.block_info(creation["created-at-round"])["timestamp"])
                if "name" in creation["params"]:
                    asset["name"] = creation["params"]["name"]
                if "unit-name" in creation["params"]:
                    asset["unit"] = creation["params"]["unit-name"]
                if "url" in creation["params"]:
                    asset["url"] = creation["params"]["url"]
                created_assets.append(asset)
        return created_assets
    
    def freeze_asset(self, sender_addr: str, target_addr: str, asset_id: int,
        eng_id: Union[int, None], fee_addr: str, fee_amount: int) -> dict:
        """freeze an asset for a target_addr"""

        txn1 = AssetFreezeTxn(sender=sender_addr, sp=self.params, index=asset_id, target=target_addr, new_freeze_state=True)
        txn2 = PaymentTxn(sender_addr, self.params, fee_addr, fee_amount, note="asset interaction fee")

        if isinstance(eng_id, int):
            txn2 = AssetTransferTxn(sender_addr, self.params, fee_addr, fee_amount, eng_id, note="asset interaction fee")

        gid = calculate_group_id([txn1, txn2])
        txn1.group = gid
        txn2.group = gid
        return gid

        # stxn1 = txn1.sign(sender_key)    
        # stxn2 = txn2.sign(sender_key)

        # signed_group =  [stxn1, stxn2]
        # txid = self.algod_client.send_transactions(signed_group)

        # transactioninfo = {}
        # transactioninfo['txid'] = txid
        # transactioninfo['link'] = f"{self.explorer_tx_url}{txid}"
        # return transactioninfo   

    def unfreeze_asset(self, sender_key: str, target_addr: str, asset_id: int,
        eng_id: Union[int, None], fee_addr: str, fee_amount: int) -> dict:
        """unfreeze an asset for a target_address"""
    
        txn1 = AssetFreezeTxn(sender=account.address_from_private_key(sender_key), sp=self.params, index=asset_id, target=target_addr, new_freeze_state=False)
        txn2 = PaymentTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, note="asset interaction fee")

        if isinstance(eng_id, int):
            txn2 = AssetTransferTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, eng_id, note="asset interaction fee")

        gid = transaction.calculate_group_id([txn1, txn2])
        txn1.group = gid
        txn2.group = gid

        return gid

        # stxn1 = txn1.sign(sender_key)    
        # stxn2 = txn2.sign(sender_key)

        # signed_group =  [stxn1, stxn2]
        # txid = self.algod_client.send_transactions(signed_group)

        # transactioninfo = {}
        # transactioninfo['txid'] = txid
        # transactioninfo['link'] = f"{self.explorer_tx_url}{txid}"
        # return transactioninfo    
    
    def clawback_asset(self, sender_key: str, receiver_addr: str, target_addr: str, asset_id: int, amount: int,
        eng_id: Union[int, None], fee_addr: str, fee_amount: int) -> dict:
        """retrieve an asset from an account and send it to a receiving address"""

        txn1 = AssetTransferTxn(sender=account.address_from_private_key(sender_key), sp=self.params, receiver=receiver_addr, amt=amount, index=asset_id, revocation_target=target_addr)
        txn2 = PaymentTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, note="asset interaction fee")

        if isinstance(eng_id, int):
            txn2 = AssetTransferTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, eng_id, note="asset interaction fee")

        gid = transaction.calculate_group_id([txn1, txn2])
        txn1.group = gid
        txn2.group = gid

        stxn1 = txn1.sign(sender_key)    
        stxn2 = txn2.sign(sender_key)

        signed_group =  [stxn1, stxn2]
        txid = self.algod_client.send_transactions(signed_group)

        transactioninfo = {}
        transactioninfo['txid'] = txid
        transactioninfo['link'] = f"{self.explorer_tx_url}{txid}"
        return transactioninfo
    
    def destroy_asset(self, sender_key: str, asset_id: int, 
        eng_id: Union[int, None], fee_addr: str, fee_amount: int) -> dict:
        """destroy an asset"""
        
        txn1 = AssetDestroyTxn(sender=account.address_from_private_key(sender_key), sp=self.params, index=asset_id)
        txn2 = PaymentTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, note="asset interaction fee")
        
        if isinstance(eng_id, int):
            txn2 = AssetTransferTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, eng_id, note="asset interaction fee")

        gid = transaction.calculate_group_id([txn1, txn2])
        txn1.group = gid
        txn2.group = gid

        stxn1 = txn1.sign(sender_key)    
        stxn2 = txn2.sign(sender_key)

        signed_group =  [stxn1, stxn2]
        txid = self.algod_client.send_transactions(signed_group)

        transactioninfo = {}
        transactioninfo['txid'] = txid
        transactioninfo['link'] = f"{self.explorer_tx_url}{txid}"
        return transactioninfo
    
    def update_asset(self, sender_key: str, asset_id: int, manager_addr: str, freeze_addr: str, 
        reserve_addr: str, clawback_addr: str, eng_id: Union[int, None], fee_addr: str, fee_amount: int) -> dict:
        """modify the 4 primary addresses"""
        txn1 = AssetUpdateTxn(sender=account.address_from_private_key(sender_key),
        sp=self.params, index=asset_id, manager=manager_addr, clawback=clawback_addr, freeze=freeze_addr, reserve=reserve_addr)
        txn2 = PaymentTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, note="asset interaction fee")

        if isinstance(eng_id, int):
            txn2 = AssetTransferTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, eng_id, note="asset interaction fee")

        gid = transaction.calculate_group_id([txn1, txn2])
        txn1.group = gid
        txn2.group = gid

        stxn1 = txn1.sign(sender_key)    
        stxn2 = txn2.sign(sender_key)

        signed_group =  [stxn1, stxn2]
        txid = self.algod_client.send_transactions(signed_group)

        transactioninfo = {}
        transactioninfo['txid'] = txid
        transactioninfo['link'] = f"{self.explorer_tx_url}{txid}"
        return transactioninfo


# add = "ZG6LER7OSSY33MJ22IQRHA2FKV2LLSZGOKF5VGBOE46NVF6FG7JDXVPHQA"
# keyq = "eFXckqb03J7f0mGrkyYZrBI7Gp6BFQqFOVwoavKpSUXJvLJH7pSxvbE60iETg0VVdLXLJnKL2pguJzzal8U30g=="


# eng = aEng("https://node.testnet.algoexplorerapi.io", "https://algoindexer.testnet.algoexplorerapi.io/", "", 1000)
# print(eng.freeze_asset(
#     add,
#     add,
#     1333,
#     None,
#     add,
#     1233,
# ))

# gid = b'\x8b\xea]|\xf1\xbd\x877\x1e\xce\xb53G\xa8\x81+\xf9\x9c\x85\xb8\x15)&*\xa2\x95\xf6q\xd6\xc8\xd4\x12'
# txn1.group = gid
# txn2.group = gid

# print(eng.rekey_account(keyq, "67EDQPXMWCQJYH7UN72ABWWT4NPCBAWAU4VGQMUHCHKBMNPNG2NTTL7XWM", "Q5PXZU7PQWFPIRYSBDRSUM34PTZKL5INZAPFHFL23C6DWQ4A2IGX5WTPGE", 1000))


# print(eng.add_asset("eFXckqb03J7f0mGrkyYZrBI7Gp6BFQqFOVwoavKpSUXJvLJH7pSxvbE60iETg0VVdLXLJnKL2pguJzzal8U30g==", 153974828))

# try:
#     print(eng.destroy_asset(
#         "dvW4GBNtWu1giommd17tlesIMmXYlUSr+ch2wqmmB+/3yDg+7LCgnB/0b/QA2tPjXiCCwKcqaDKHEdQWNe02mw==",
#         153974828,
#         None,
#         "T7F2LBEJRYH6MJZ26TZBP2JCX7XHTB5V54R2SE4XKVXCJYL37KBG6DXXBU",
#         1000
#     ))
# except Exception as e:
#     print(e)
