from typing import Union

from algosdk import account
from algosdk.future import transaction
from algosdk.future.transaction import (AssetConfigTxn, AssetTransferTxn,
                                        PaymentTxn)
from algosdk.v2client.algod import AlgodClient


class aAsset(AlgodClient):
    def __init__(self, algod_url: str, txns_fee: int, explorer_tx_url: str):
        self.algod_client = AlgodClient("", algod_url)
        self.params = self.algod_client.suggested_params()
        self.params.flat_fee = True
        self.params.fee = txns_fee
        self.explorer_tx_url = explorer_tx_url

    def to_mainnet(self) -> bool:
        """change client to mainnet"""
        self.algod_client = AlgodClient(self.algod_token, "https://mainnet-algorand.api.purestake.io/ps2", self.headers)
        self.explorer_tx_url = "https://algoexplorer.io/tx/"
        return True

    def to_testnet(self) -> bool:
        """change client to testnet"""
        self.algod_client = AlgodClient(self.algod_token, "https://testnet-algorand.api.purestake.io/ps2", self.headers)
        self.explorer_tx_url = "https://testnet.algoexplorer.io/tx/"
        return False
    
    def custom_asset(self, sender_key: str, name: str, unit: str, total_supply: int, decimal: int, df_frozen: bool, url: str, mt_hash: bytes,
        manager_addr: str, reserve_addr: str, freeze_addr: str, clawback_addr: str,
        eng_id: Union[int, None], fee_addr: str, fee_amount: int) -> dict:
        """create custom asset"""

        txn1 = AssetConfigTxn(
        sender=account.address_from_private_key(sender_key),
        sp=self.params,
        total=total_supply, # 18 quintillion
        default_frozen=df_frozen, # bool
        unit_name=unit, # max 8
        asset_name=name, # max 32
        manager=manager_addr,
        reserve=reserve_addr,
        freeze=freeze_addr,
        clawback=clawback_addr,
        url=url, # max 32
        decimals=decimal, # max 19
        metadata_hash=mt_hash,) # req 32 b''
        txn2 = PaymentTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, note="asset creation fee")

        if isinstance(eng_id, int):
            txn2 = AssetTransferTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, eng_id, note="asset creation fee")

        gid = transaction.calculate_group_id([txn1, txn2])
        txn1.group = gid
        txn2.group = gid

        stxn1 = txn1.sign(sender_key)    
        stxn2 = txn2.sign(sender_key)
        signed_group = [stxn1, stxn2]

        txid = self.algod_client.send_transactions(signed_group)
        transactioninfo = {}
        transactioninfo['txid'] = txid
        transactioninfo['link'] = f"{self.explorer_tx_url}{txid}"
        return transactioninfo

    def create_token(self, sender_key: str, name: str, unit: str, total_supply: int, decimal: int, url: str,
        eng_id: Union[int, None], fee_addr: str, fee_amount: int) -> dict:
        """create token"""

        txn1 = AssetConfigTxn(strict_empty_address_check=False,
        sender=account.address_from_private_key(sender_key),
        sp=self.params,
        total=total_supply, # max 18 quintillion
        default_frozen=False, # bool
        unit_name=unit, # max 8
        asset_name=name, # max 32
        manager="",
        reserve="",
        freeze="",
        clawback="",
        url=url, # max 32
        decimals=decimal)
        txn2 = PaymentTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, note="asset creation fee")

        if isinstance(eng_id, int):
            txn2 = AssetTransferTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, eng_id, note="asset creation fee")

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

    # print(create_asset("bowo", "boow", 100000, 2, "obi.wan", "OR3HAH76YZU6CVVZY4E6XKHMKOD3AOQR7ZDVQWYROY6Y3ASXEEAZXVPDVE",
    # "Uqgacy/2+xV4466dH9sXpMW+YuLdBwzlQAh1J66SISJ0dnAf/sZp4Va5xwnrqOxTh7A6Ef5HWFsRdj2NglchAQ==",
    # "algo", None, "HZN5PECG77YA4R5D4HNI3SXQU67IYZ5QULYVIC6ME52OJLJTM2IOZAUZYY", 1000000, "noted"))

    def create_pure_nft(self, sender_key: str, name: str, unit: str, url: str,
        eng_id: Union[int, None], fee_addr: str, fee_amount: int) -> dict:
        """create pure nft"""

        txn1 = AssetConfigTxn(strict_empty_address_check=False,
        sender=account.address_from_private_key(sender_key),
        sp=self.params,
        total=1, # max 18 quintillion
        default_frozen=False, # bool
        unit_name=unit, # max 8
        asset_name=name, # max 32
        manager="",
        reserve="",
        freeze="",
        clawback="",
        url=url, # max 32 url to information about nft or asset
        ) # max 19
        txn2 = PaymentTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, note="asset creation fee")

        if isinstance(eng_id, int):
            txn2 = AssetTransferTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, eng_id, note="asset creation fee")

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

    def web3_tickets(self, sender_key: str, name: str, url: str, total_supply: int,
        eng_id: Union[int, None], fee_addr: str, fee_amount: int) -> dict:
        """create web3 ticket"""
        txn1 = AssetConfigTxn(
        sender=account.address_from_private_key(sender_key),
        sp=self.params,
        total=total_supply, # max 18 quintillion
        default_frozen=False, # bool
        unit_name="WEB3TCKT", # max 8
        asset_name=name, # max 32
        manager=account.address_from_private_key(sender_key),
        freeze=account.address_from_private_key(sender_key),
        clawback=account.address_from_private_key(sender_key),
        url=url, # max 32
        decimals=0)
        txn2 = PaymentTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, note="asset creation fee")

        if isinstance(eng_id, int):
            txn2 = AssetTransferTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, eng_id, note="asset creation fee")

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

    def create_nft_collection(self, sender_key: str, name: str, unit: str, total: int, url: str,
        eng_id: Union[int, None], fee_addr: str, fee_amount: int) -> dict:
        """create nft collection"""
        txn1 = AssetConfigTxn(strict_empty_address_check=False,
        sender=account.address_from_private_key(sender_key),
        sp=self.params,
        total=total, # max 18 quintillion
        default_frozen=False, # bool
        unit_name=unit, # max 8
        asset_name=name, # max 32
        manager="",
        reserve="",
        freeze="",
        clawback="",
        url=url, # max 32
        decimals=0)
        txn2 = PaymentTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, note="asset creation fee")

        if isinstance(eng_id, int):
            txn2 = AssetTransferTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, eng_id, note="asset creation fee")

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

    def security_asset(self, sender_key: str, name: str, unit: str, total_supply: int, url: str, decimal: int,
        eng_id: Union[int, None], fee_addr: str, fee_amount: int) -> dict:
        """create a security asset"""
        txn1 = AssetConfigTxn(
        sender=account.address_from_private_key(sender_key),
        sp=self.params,
        total=total_supply, # max 18 quintillion
        default_frozen=False, # bool
        unit_name=unit, # max 8
        asset_name=name, # max 32
        manager=account.address_from_private_key(sender_key),
        freeze=account.address_from_private_key(sender_key),
        clawback=account.address_from_private_key(sender_key),
        reserve=account.address_from_private_key(sender_key),
        url=url, # max 32 pointing to a the mtdata file
        decimals=decimal)
        txn2 = PaymentTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, note="asset creation fee")

        if isinstance(eng_id, int):
            txn2 = AssetTransferTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, eng_id, note="asset creation fee")

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

    def create_fractional_nft(self, sender_key: str, name: str, unit: str, total_supply: int, 
        url: str, decimal: int, eng_id: Union[int, None], fee_addr: str, fee_amount: int) -> dict:
        """create fractional nft""" 
        txn1 = AssetConfigTxn(strict_empty_address_check=False,
        sender=account.address_from_private_key(sender_key),
        sp=self.params,
        total=total_supply, # max 18 quintillion
        default_frozen=False, # bool
        unit_name=unit, # max 8
        asset_name=name, # max 32
        manager="",
        reserve="",
        freeze="",
        clawback="",
        url=url, # max 32 pointing to a the mtdata file
        decimals=decimal)
        txn2 = PaymentTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, note="asset creation fee")

        if isinstance(eng_id, int):
            txn2 = AssetTransferTxn(account.address_from_private_key(sender_key), self.params, fee_addr, fee_amount, eng_id, note="asset creation fee")

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

af = aAsset("https://node.testnet.algoexplorerapi.io", 1000, "") #  "https://algoindexer.testnet.algoexplorerapi.io/", 1000, "", "", "")