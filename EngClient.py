import json

import requests


class MintEngineClient():
    def __init__(self, indexer_url: str):
        self.indexer_url = indexer_url

    def account_info(self, account: str):
        """returns information about an account"""
        req = requests.get(f'{self.indexer_url}/accounts/{account}')
        return req.json()

    def asset_info(self, asset_id: int):
        """returns information about a specified asset id"""
        query = {"include-all": False}
        req = requests.get(f'{self.indexer_url}/assets/{asset_id}', params=query)
        return req.json()

    def account_algo_transactions(self, account: str, limit: int):
        """returns an accounts algo transactions"""
        params = {"tx-type": "pay", "limit": limit}
        req = requests.get(f'{self.indexer_url}/accounts/{account}/transactions', params)
        return req.json()

    def account_assets_transfer_transactions(self, account: str, limit: int):
        params = {"tx-type": "axfer", "limit": limit}
        req = requests.get(f'{self.indexer_url}/accounts/{account}/transactions', params)
        return req.json()

    def account_asset_transfer_transactions(self, account: str, asset_id: int, limit: int):
        params = {"asset-id": asset_id, "tx-type": "axfer", "limit": limit}
        req = requests.get(f'{self.indexer_url}/accounts/{account}/transactions', params)
        return req.json()

    def block_info(self, round_number: int):
        req = requests.get(f'{self.indexer_url}/blocks/{round_number}')
        return req.json()

x = MintEngineClient("https://algoindexer.testnet.algoexplorerapi.io/v2")

# g = [10458941, 16010077, 16001043, 16010043, 16010087, 17026402, 16010057, 16001041, 16010056, 16010085, 17063481, 16016011, 16010050, 16010049, 86121492]
# for i in g:
# print(json.dumps(x.asset_info(17063481), indent=2))
# print(json.dumps(x.account_info("VQIMXAPONHJV3W2HIQACCZWNUC5JIVWIFHRAV35ZH524M6NIZJXXHTLPJE"), indent=2))
