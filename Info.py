import base64

import requests
from algosdk.util import microalgos_to_algos
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from Misc import (find_amount_w_decimal, find_amount_w_decimal_id,
                  timestamp_to_string)


class aInfo(AlgodClient, IndexerClient):
    def __init__(self, indexer_url: str, algod_url: str):
        self.indexer_client = IndexerClient("", indexer_url)
        self.algod_client = AlgodClient("", algod_url)
    
    def get_account_info(self, wallet_addr: str) -> dict:
        """return information on an account"""
        account_info = {}
        algod_req = self.algod_client.account_info(wallet_addr)
        indexer_req = self.indexer_client.account_info(wallet_addr)
        if "account" in indexer_req and "address" in indexer_req["account"] and "address" in algod_req:
            account_info["account"] = algod_req["address"]
            account_info["balance"] = str(microalgos_to_algos(algod_req["amount"]))
            account_info["min_balance"] = str(microalgos_to_algos(algod_req["min_balance"]))
            account_info["pending_rewards"] = algod_req["pending-rewards"]
            account_info["status"] = algod_req["status"]
            account_info["asset_count"] = algod_req["total-assets-opted-in"]
            account_info["app_count"] = algod_req["total-apps-opted-in"]
            account_info["created_asset_count"] = algod_req["total-created-assets"]
            account_info["created_app_count"] = algod_req["total-created-apps"]
            # indexer begins here
            account_info["date_created"] = timestamp_to_string(self.indexer_client.block_info(algod_req["account"]["created-at-round"])["timestamp"])
            account_info["block_created"] = algod_req["account"]["created-at-round"]
            account_info["is_deleted"] = algod_req["account"]["deleted"]
            account_info["type"] = algod_req["account"]["sig-type"]
            # box bytes and stuff
        return account_info
        
    def get_asset_info(self, asset_id: int) -> dict:
        """return information on an asset"""
        asset_info = {}
        price_info = requests.get(f"https://free-api.vestige.fi/asset/{asset_id}/price").json()
        supply_info = requests.get(f"https://free-api.vestige.fi/asset/{asset_id}").json()
        describe = requests.get(f"https://indexer.algoexplorerapi.io/v2/assets/{asset_id}?include-all=true").json()
        req = self.indexer_client.asset_info(asset_id)
        if "asset" in req:
            asset_info["name"] = ""
            asset_info["unit"] = ""
            if "name" in req["asset"]["params"]:
                asset_info["name"] = req["asset"]["params"]["name"]
            if "unit-name" in req["asset"]["params"]:
                asset_info["unit"] = req["asset"]["params"]["unit-name"]
            asset_info["id"] = req["asset"]["index"]
            asset_info["date_created"] = timestamp_to_string(self.indexer_client.block_info(req["asset"]["created-at-round"])["timestamp"])
            asset_info["clawback"] = req["asset"]["params"]["clawback"]
            asset_info["reserve"] = req["asset"]["params"]["reserve"]
            asset_info["freeze"] = req["asset"]["params"]["freeze"]
            asset_info["manager"] = req["asset"]["params"]["manager"]
            asset_info["creator"] = req["asset"]["params"]["creator"]
            asset_info["supply"] = find_amount_w_decimal(req["asset"]["params"]["total"], req["asset"]["params"]["decimals"])
            asset_info["default_frozen"] = req["asset"]["params"]["default-frozen"]
            asset_info["is_deleted"] = req["asset"]["deleted"]
            asset_info["price"] = 0
            asset_info["description"] = ""
            asset_info["circulating_supply"] = 0
            asset_info["burned_supply"] = 0
            asset_info["market_cap"] = 0
            if isinstance(price_info, dict) and "USD" in price_info:
                asset_info["price"] = price_info["USD"]
            if isinstance(supply_info, dict) and "circulating_supply" in supply_info:
                asset_info["circulating_supply"] = find_amount_w_decimal(int(supply_info["circulating_supply"]), supply_info["decimals"])
                asset_info["market_cap"] = asset_info["circulating_supply"] * asset_info["price"]
            if isinstance(supply_info, dict) and "burned_supply" in supply_info:
                asset_info["burned_supply"] = find_amount_w_decimal(int(supply_info["burned_supply"]), supply_info["decimals"])
            if isinstance(describe, dict) and "asset" in describe and "verification" in describe["asset"] and "description" in describe["asset"]["verification"]:
                asset_info["description"] = describe["asset"]["verification"]["description"]
        return asset_info

    def pay_txn_info(self, txid: str) -> dict:
        """detailed info on a payment transaction"""
        txn_info = {}
        req = self.indexer_client.transaction(txid)
        if "transaction" in req:
            txn_info["sender"] = req["transaction"]["sender"]
            if "payment-transaction" in req["transaction"]:
                txn_info["receiver"] = req["transaction"]["payment-transaction"]["receiver"]
                txn_info["amount"] =str(microalgos_to_algos(req["transaction"]["payment-transaction"]["amount"]))
                txn_info["asset_id"] = 0
                txn_info["name"] = "ALGO"
            if "asset-transfer-transaction" in req["transaction"]:
                txn_info["receiver"] = req["transaction"]["asset-transfer-transaction"]["receiver"]
                txn_info["amount"] = find_amount_w_decimal_id(self.indexer_client, req["transaction"]["asset-transfer-transaction"]["amount"], req["transaction"]["asset-transfer-transaction"]["asset-id"])
                txn_info["asset_id"] = req["transaction"]["asset-transfer-transaction"]["asset-id"]
                txn_info["name"] = self.get_asset_info(req["transaction"]["asset-transfer-transaction"]["asset-id"])["name"]
            txn_info["timestamp"] = timestamp_to_string(req["transaction"]["round-time"])
            txn_info["txid"] = req["transaction"]["id"]
            txn_info["tx_type"] = req["transaction"]["tx-type"]
            txn_info["fee"] = str(microalgos_to_algos(req["transaction"]["fee"]))
            txn_info["note"] = ""
            if "note" in req["transaction"]:
                txn_info["note"] = base64.b64decode(req['transaction']['note']).decode()
        return txn_info
