from typing import Union
from algosdk.future import transaction
from algosdk.future.transaction import AssetCloseOutTxn, AssetConfigTxn, AssetDestroyTxn, AssetFreezeTxn, AssetOptInTxn, AssetTransferTxn, AssetUpdateTxn, PaymentTxn
from Misc import meta_hash_text
from algosdk.v2client.algod import AlgodClient

class Eng(AlgodClient):
    def __init__(self, algod_token: str, algod_url: str, txns_fee: int,
    explorer_tx_url: str):
        self.headers = {"X-API-Key": algod_token,}
        self.algod_client = AlgodClient(algod_token, algod_url, self.headers)
        self.params = self.algod_client.suggested_params()
        self.params.flat_fee = True
        self.params.fee = txns_fee
        self.explorer_tx_url = explorer_tx_url
    
    def change_network(self, algod_url: str, explorer_tx_url: str) -> bool:
        """change the entirety of the network"""
        self.algod_client = AlgodClient(self.algod_token, algod_url, self.headers)
        self.explorer_tx_url = explorer_tx_url
        return True
    
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
    
    def change_algod_key(self, key: str) -> bool:
        """change the algod key"""
        self.headers["X-API-Key"] = key
        return True

    def modify_chain_fee(self, new_fee: int) -> bool:
        """modify the network fee for faster transaction time"""
        assert new_fee > 1000
        self.params.fee = new_fee
        return True
    
    def opt_in(self, sender_addr: str, sender_key: str, asset_id: int, note: str) -> dict:
        """enable transacting with an asset"""
        account_info = self.algod_client.account_info(sender_addr)
        holding = None
        asset_index = 0

        for my_account_info in account_info['assets']:
            scrutinized_asset = account_info['assets'][asset_index]
            asset_index = asset_index + 1    
            if (scrutinized_asset['asset-id'] == asset_id):
                holding = True
                pass
        if not holding:
            txn = AssetOptInTxn(sender=sender_addr, sp=self.params, index=asset_id, note=note)
            stxn = txn.sign(sender_key)
            txid = self.algod_client.send_transaction(stxn)
            transactioninfo = {}
            transactioninfo['txid'] = txid
            transactioninfo['link'] = f"{self.explorer_tx_url}{txid}"
            return transactioninfo

    def opt_out(self, sender_addr: str, sender_key: str, asset_id: int, receiver_addr: int, note: str) -> dict:
        """disable transacting with an asset"""
        account_info = self.algod_client.account_info(sender_addr)
        holding = None
        asset_index = 0

        for my_account_info in account_info['assets']:
            scrutinized_asset = account_info['assets'][asset_index]
            asset_index = asset_index + 1    
            if (scrutinized_asset['asset-id'] == asset_id):
                holding = True
        if holding:
            txn = AssetCloseOutTxn(sender=sender_addr, sp=self.params, receiver=receiver_addr, index=asset_id, note=note)
            stxn = txn.sign(sender_key)
            txid = self.algod_client.send_transaction(stxn)
            transactioninfo = {}
            transactioninfo['txid'] = txid
            transactioninfo['link'] = f"{self.explorer_tx_url}{txid}"
            return transactioninfo

    def freeze_asset(self, sender_addr: str, target_addr: str, asset_id: int, sender_key: str,
        fee_type: str, eng_id: Union[int, None], fee_addr: str, fee_amount: int, note: str) -> dict:
        """freeze an asset for a target_addr"""
        txn2 = None
        txn1 = AssetFreezeTxn(sender=sender_addr, sp=self.params, index=asset_id, target=target_addr, new_freeze_state=True, note=note)

        if fee_type == "algo":
            txn2 = PaymentTxn(sender_addr, self.params, fee_addr, fee_amount, note="asset interaction fee")
        if fee_type == "eng":
            txn2 = AssetTransferTxn(sender_addr, self.params, fee_addr, fee_amount, eng_id, note="asset interaction fee")

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

    def unfreeze_asset(self, sender_addr: str, target_addr: str, asset_id: int, sender_key: str,
        fee_type: str, eng_id: Union[int, None], fee_addr: str, fee_amount: int, note: str) -> dict:
        """unfreeze an asset for a target_address"""
        txn2 = None
        txn1 = AssetFreezeTxn(sender=sender_addr, sp=self.params, index=asset_id, target=target_addr, new_freeze_state=False, note=note)
        
        if fee_type == "algo":
            txn2 = PaymentTxn(sender_addr, self.params, fee_addr, fee_amount, note="asset interaction fee")
        if fee_type == "eng":
            txn2 = AssetTransferTxn(sender_addr, self.params, fee_addr, fee_amount, eng_id, note="asset interaction fee")

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

    def clawback_asset(self, sender_addr: str, receiver_addr: str, target_addr: str, asset_id: int, amount: int, sender_key: str,
        fee_type: str, eng_id: Union[int, None], fee_addr: str, fee_amount: int, note: str) -> dict:
        """retrieve an asset from an account and send it to a receiving address"""
        txn2 = None
        txn1 = AssetTransferTxn(sender=sender_addr, sp=self.params, receiver=receiver_addr, amt=amount, index=asset_id, revocation_target=target_addr, note=note)

        if fee_type == "algo":
            txn2 = PaymentTxn(sender_addr, self.params, fee_addr, fee_amount, note="asset interaction fee")
        if fee_type == "eng":
            txn2 = AssetTransferTxn(sender_addr, self.params, fee_addr, fee_amount, eng_id, note="asset interaction fee")

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

    def modify_asset(self, sender_addr: str, asset_id: int, manager_addr: str, reserve_addr: str, freeze_addr: str, clawback_addr: str, sender_key: str,
        fee_type: str, eng_id: Union[int, None], fee_addr: str, fee_amount: int, note: str) -> dict:
        """change an asset parameters, only a manager can call this"""
        txn2 = None
        txn1 = AssetUpdateTxn(sender=sender_addr, sp=self.params, index=asset_id,
        manager=manager_addr,
        reserve=reserve_addr, 
        freeze=freeze_addr,
        clawback=clawback_addr,
        note=note,
        strict_empty_address_check=True)

        if fee_type == "algo":
            txn2 = PaymentTxn(sender_addr, self.params, fee_addr, fee_amount, note="asset interaction fee")
        if fee_type == "eng":
            txn2 = AssetTransferTxn(sender_addr, self.params, fee_addr, fee_amount, eng_id, note="asset interaction fee")

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


    def destroy_asset(self, sender_addr: str, asset_id: int, sender_key: str,
        fee_type: str, eng_id: Union[int, None], fee_addr: str, fee_amount: int, note: str) -> dict:
        """destroy an asset"""
        txn2 = None
        txn1 = AssetDestroyTxn(sender=sender_addr, sp=self.params, index=asset_id, note=note)

        if fee_type == "algo":
            txn2 = PaymentTxn(sender_addr, self.params, fee_addr, fee_amount, note="asset interaction fee")
        if fee_type == "eng":
            txn2 = AssetTransferTxn(sender_addr, self.params, fee_addr, fee_amount, eng_id, note="asset interaction fee")

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

    def custom_asset(self, name: str, unit: str, total_supply: int, decimal: int, df_frozen: bool, url: str, mt_hash: bytes,
        sender_addr: str, manager_addr: str, reserve_addr: str, freeze_addr: str, clawback_addr: str,sender_key: str,
        fee_type: str, eng_id: Union[int, None], fee_addr: str, fee_amount: int, note: str) -> dict:
        """create custom asset"""
        txn2 = None

        txn1 = AssetConfigTxn(
        sender=sender_addr,
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
        metadata_hash=mt_hash, # req 32 b''
        note=note)  # max 1000

        if fee_type == "algo":
            txn2 = PaymentTxn(sender_addr, self.params, fee_addr, fee_amount, note="asset creation fee")
        if fee_type == "eng":
            txn2 = AssetTransferTxn(sender_addr, self.params, fee_addr, fee_amount, eng_id, note="asset creation fee")

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

    def create_asset(self, name: str, unit: str, total_supply: int, decimal: int, url: str,
        sender_addr: str, sender_key: str,
        fee_type: str, eng_id: Union[int, None], fee_addr: str, fee_amount: int, note: str) -> dict:
        """create asset"""
        txn2 = None

        txn1 = AssetConfigTxn(strict_empty_address_check=False,
        sender=sender_addr,
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
        decimals=decimal, # max 19
        metadata_hash= meta_hash_text(name), # req 32 b''
        note=note)  # max 1000

        if fee_type == "algo":
            txn2 = PaymentTxn(sender_addr, self.params, fee_addr, fee_amount, note="asset creation fee")
        if fee_type == "eng":
            txn2 = AssetTransferTxn(sender_addr, self.params, fee_addr, fee_amount, eng_id, note="asset creation fee")

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

    def create_unique_nft(self, name: str, unit: str, url: str, sender_addr: str, sender_key: str,
        fee_type: str, eng_id: Union[int, None], fee_addr: str, fee_amount: int, note: str) -> dict:
        """create unique nft"""
        txn2 = None

        txn1 = AssetConfigTxn(strict_empty_address_check=False,
        sender=sender_addr,
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
        decimals=0, # max 19
        metadata_hash=meta_hash_text(name), # req 32 b''
        note=note)  # max 1000

        if fee_type == "algo":
            txn2 = PaymentTxn(sender_addr, self.params, fee_addr, fee_amount, note="asset creation fee")
        if fee_type == "eng":
            txn2 = AssetTransferTxn(sender_addr, self.params, fee_addr, fee_amount, eng_id, note="asset creation fee")

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

    def web3_tickets(self, name: str, url: str, total_supply: int, sender_addr: str, sender_key: str,
        fee_type: str, eng_id: Union[int, None], fee_addr: str, fee_amount: int, note: str) -> dict:
        """create web3 ticket"""
        txn2 = None

        txn1 = AssetConfigTxn(
        sender=sender_addr,
        sp=self.params,
        total=total_supply, # max 18 quintillion
        default_frozen=False, # bool
        unit_name="WEB3TCKT", # max 8
        asset_name=name, # max 32
        manager=sender_addr,
        reserve=sender_addr,
        freeze=sender_addr,
        clawback=sender_addr,
        url=url, # max 32
        decimals=0, # max 19
        metadata_hash=meta_hash_text(name), # req 32 b''
        note=note)  # max 1000

        if fee_type == "algo":
            txn2 = PaymentTxn(sender_addr, self.params, fee_addr, fee_amount, note="asset creation fee")
        if fee_type == "eng":
            txn2 = AssetTransferTxn(sender_addr, self.params, fee_addr, fee_amount, eng_id, note="asset creation fee")

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

    def create_nft_collection(self, name: str, unit: str, total: int, url: str,
        sender_addr: str, sender_key: str,
        fee_type: str, eng_id: Union[int, None], fee_addr: str, fee_amount: int, note: str) -> dict:
        """create common nft"""
        txn2 = None

        txn1 = AssetConfigTxn(strict_empty_address_check=False,
        sender=sender_addr,
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
        decimals=0, # max 19
        metadata_hash=meta_hash_text(name), # req 32 b''
        note=note)  # max 1000

        if fee_type == "algo":
            txn2 = PaymentTxn(sender_addr, self.params, fee_addr, fee_amount, note="asset creation fee")
        if fee_type == "eng":
            txn2 = AssetTransferTxn(sender_addr, self.params, fee_addr, fee_amount, eng_id, note="asset creation fee")

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

    def security_asset(self, sender_addr: str, sender_key: str, name: str, unit: str,
        total_supply: int, url: str, decimal: int,
        fee_type: str, eng_id: Union[int, None], fee_addr: str, fee_amount: int, note: str) -> dict:
        """create a security asset"""
        txn2 = None

        txn1 = AssetConfigTxn(
        sender=sender_addr,
        sp=self.params,
        total=total_supply, # max 18 quintillion
        default_frozen=False, # bool
        unit_name=unit, # max 8
        asset_name=name, # max 32
        manager=sender_addr,
        reserve=sender_addr,
        freeze=sender_addr,
        clawback=sender_addr,
        url=url, # max 32 pointing to a the mtdata file
        decimals=decimal, # max 19
        metadata_hash= meta_hash_text(name), # req 32 b''
        note=note)  # max 1000

        if fee_type == "algo":
            txn2 = PaymentTxn(sender_addr, self.params, fee_addr, fee_amount, note="asset creation fee")
        if fee_type == "eng":
            txn2 = AssetTransferTxn(sender_addr, self.params, fee_addr, fee_amount, eng_id, note="asset creation fee")

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

    def create_fractional_nft(self, sender_addr: str, sender_key: str, name: str, unit: str,
        total_supply: int, url: str, decimal: int,
        fee_type: str, eng_id: int, fee_addr: str, fee_amount: int, note: str) -> dict:
        """create fractional nft""" 
        txn2 = None

        txn1 = AssetConfigTxn(strict_empty_address_check=False,
        sender=sender_addr,
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
        decimals=decimal, # max 19
        metadata_hash= meta_hash_text(name), # req 32 b''
        note=note)  # max 1000

        if fee_type == "algo":
            txn2 = PaymentTxn(sender_addr, self.params, fee_addr, fee_amount, note="asset creation fee")
        if fee_type == "eng":
            txn2 = AssetTransferTxn(sender_addr, self.params, fee_addr, fee_amount, eng_id, note="asset creation fee")

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