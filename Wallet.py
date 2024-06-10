from algosdk.future.transaction import AssetTransferTxn, PaymentTxn
from algosdk.util import microalgos_to_algos
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from Misc import find_amount_w_decimal, timestamp_to_string


class aWallet(AlgodClient, IndexerClient):
    def __init__(self, algod_url: str, indexer_url: str, fee: int,
    explorer_account_url: str, explorer_asset_url: str, explorer_tx_url: str):
        self.algod_client = AlgodClient("", algod_url)
        self.indexer_client = IndexerClient("", indexer_url)
        self.params = self.algod_client.suggested_params()
        self.params.flat_fee = True
        self.params.fee = fee
        self.explorer_account_url = explorer_account_url
        self.explorer_asset_url = explorer_asset_url
        self.explorer_tx_url = explorer_tx_url
        
    def get_network_fee(self) -> str:
        """return the network fee"""
        return str(microalgos_to_algos(self.algod_client.suggested_params().fee))

    def show_account_in_explorer(self, wallet_address: str) -> str:
        """generate a link to view account in explorer"""
        msg = f"{self.explorer_account_url}{wallet_address}"
        return msg

    def show_transaction_in_explorer(self, txid: str) -> str:
        """generate a link to view transaction in explorer"""
        msg = f"{self.explorer_tx_url}{txid}"
        return msg

    def show_asset_in_explorer(self, asset_id: int) -> str:
        """generate a link to view asset in explorer"""
        msg = f"{self.explorer_asset_url}{asset_id}"
        return msg

    def send_algo(self, sender_addr: str, receiver: str, amount: int, note: str) -> dict:
        """generate algo payment object, for multiple or single transfers"""
        return dict(PaymentTxn(sender_addr, self.params, receiver, amount, note=note).dictify())

    def send_asset(self, sender_addr: str, receiver: str, amount: int, asset_id: int, note: str) -> dict:
        """generate asset transfer object"""
        return dict(AssetTransferTxn(sender_addr, self.params, receiver, amount, asset_id, note=note).dictify())

    def algo_balance(self, wallet_addr: str) -> dict:
        """returns algo balance"""
        balance = 0
        asset_count = 0
        spend_balance = 0
        info = self.algod_client.account_info(wallet_addr)
        if "address" in info:
            balance = float(microalgos_to_algos(info["amount"]))
            asset_count = info["total-assets-opted-in"]
            # deduct = asset_count * 0.12
            spend_balance = balance - info["min-balance"]
        return {
            "balance": balance,
            "asset_count": asset_count,
            "spend_balance": spend_balance}
    
    def account_tokens(self, wallet_addr: str) -> list:
        """tokens an account can send and receive """
        account_tokens = []
        query = self.algod_client.account_info(wallet_addr)
        assets = query["assets"]
        for account_token in assets:
            token = {}
            token["token"] = ""
            token["unit"] = ""
            token["decimal"] = 0
            token['amount'] = int(account_token['amount'])
            token["id"] = account_token["asset-id"]
            token["is_frozen"] = account_token["is-frozen"]
            req = self.algod_client.asset_info(account_token["asset-id"])
            if "params" in req:
                info = req["params"]
                if "name" in info:
                    token["token"] = info["name"]
                if "unit-name" in info:
                    token["token"] = info["unit-name"]
                    if 'decimals' in info != 0:
                        token['decimal'] = info['decimals']
                        token['amount'] = find_amount_w_decimal(account_token['amount'], info['decimals'])
            account_tokens.append(token)
        account_tokens = filter(lambda i: i["decimal"] != 0, account_tokens) # do_it(account_tokens)
            # format list and drop zero decimals
        return list(account_tokens)
    
    def account_nfts(self, wallet_addr: str) -> list:
        """return account nfts"""
        account_tokens = []
        query = self.algod_client.account_info(wallet_addr)
        assets = query["assets"]
        for account_token in assets:
            token = {}
            token["nft"] = ""
            token["unit"] = ""
            token["decimal"] = 0
            token["amount"] = int(account_token['amount'])
            token["id"] = account_token["asset-id"]
            token["is_frozen"] = account_token["is-frozen"]
            req = self.algod_client.asset_info(account_token["asset-id"])
            if "params" in req:
                info = req["params"]
                if "name" in info:
                    token["nft"] = info["name"]
                if "unit-name" in info:
                    token["unit"] = info["unit-name"]
                if 'decimals' in info != 0:
                    token['decimal'] = info['decimals']
            account_tokens.append(token)
        account_tokens = filter(lambda i: i["decimal"] == 0, account_tokens)# format list and drop 0 + x decimals
        return list(account_tokens)
    
    def algo_transactions(self, wallet_addr: str, limit: int = None) -> dict:
        """algo transactions carried out by an account"""
        transactions_dict = {}
        sent = []
        received = []
        response = self.indexer_client.search_transactions_by_address(address=wallet_addr, limit=limit, txn_type="pay")
        if "transactions" in response:
            transactions = response["transactions"]
            for transaction in transactions:
                transact = {}
                transact["sender"] = transaction["sender"]
                transact["receiver"] = transaction["payment-transaction"]["receiver"]
                transact["amount"] = str(microalgos_to_algos(transaction["payment-transaction"]["amount"]))
                transact["fee"] = str(microalgos_to_algos(transaction["fee"]))
                transact["timestamp"] = timestamp_to_string(transaction["round-time"])
                transact["tx_type"] = transaction["tx-type"]
                transact["txid"] = transaction["id"]
                transact["link"] = f"{self.explorer_tx_url}{transaction['id']}"
                if transact['sender'] == wallet_addr:
                    sent.append(transact)
                elif transact['sender'] != wallet_addr:
                    received.append(transact)
            transactions_dict['sent'] = sent
            transactions_dict['received'] =  received
        return transactions_dict

    def asset_transactions(self, wallet_addr: str, limit: int = None) -> dict:
        """all asset transfer transactions carried out by an account"""
        transactions_dict = {}
        sent = []
        received = []
        response = self.indexer_client.search_transactions_by_address(address=wallet_addr, limit=limit, txn_type="axfer")
        if "transactions" in response:
            transactions = response["transactions"]
            for transaction in transactions:
                transact = {}
                transact["asset"] = ""
                transact["unit"] = ""
                transact["decimal"] = 0
                transact["amount"] = int(transaction["asset-transfer-transaction"]["amount"])
                info = self.algod_client.asset_info(transaction["asset-transfer-transaction"]["asset-id"])
                if "params" in info:
                    if "name" in info["params"]:
                        transact["asset"] = info["params"]["name"]
                    if "unit-name" in info["params"]:
                        transact["unit"] = info["params"]["unit-name"]
                    if "decimals" in info["params"] != 0:
                        transact['decimal'] = info["params"]['decimals']
                        transact['amount'] = find_amount_w_decimal(transaction["asset-transfer-transaction"]["amount"], info["params"]["decimals"])
                transact["sender"] = transaction["sender"]
                transact["receiver"] = transaction["asset-transfer-transaction"]["receiver"]
                transact["fee"] = str(microalgos_to_algos(transaction["fee"]))
                transact["timestamp"] = timestamp_to_string(transaction["round-time"])
                transact["tx_type"] = transaction["tx-type"]
                transact["txid"] = transaction["id"]
                transact["link"] = f"{self.explorer_tx_url}{transaction['id']}"

                if transact['sender'] == wallet_addr:
                    sent.append(transact)
                elif transact['sender'] != wallet_addr:
                    received.append(transact)
            transactions_dict['sent'] = sent
            transactions_dict['received'] =  received
        return transactions_dict

    def asset_transaction(self, wallet_addr: str, asset_id: int) -> dict:
        """all asset transfer transactions for an asset id by an account"""
        transactions_dict = {}
        sent = []
        received = []
        response = self.indexer_client.search_asset_transactions(address=wallet_addr, asset_id=asset_id, txn_type="axfer")
        if "transactions" in response:
            transactions = response["transactions"]
            for transaction in transactions:
                transact = {}
                transact["asset"] = ""
                transact["unit"] = ""
                transact["decimal"] = 0
                transact["amount"] = int(transaction["asset-transfer-transaction"]["amount"])
                info = self.algod_client.asset_info(transaction["asset-transfer-transaction"]["asset-id"])
                if "params" in info:
                    if "name" in info["params"]:
                        transact["asset"] = info["params"]["name"]
                    if "unit-name" in info["params"]:
                        transact["unit"] = info["params"]["unit-name"]
                    if "decimals" in info["params"] != 0:
                        transact['decimal'] = info["params"]['decimals']
                        transact['amount'] = find_amount_w_decimal(transaction["asset-transfer-transaction"]["amount"], info["params"]["decimals"])
                transact["sender"] = transaction["sender"]
                transact["receiver"] = transaction["asset-transfer-transaction"]["receiver"]
                transact["fee"] = str(microalgos_to_algos(transaction["fee"]))
                transact["timestamp"] = timestamp_to_string(transaction["round-time"])
                transact["tx_type"] = transaction["tx-type"]
                transact["txid"] = transaction["id"]
                transact["link"] = f"{self.explorer_tx_url}{transaction['id']}"

                if transact['sender'] == wallet_addr:
                    sent.append(transact)
                elif transact['sender'] != wallet_addr:
                    received.append(transact)
            transactions_dict['sent'] = sent
            transactions_dict['received'] =  received
        return transactions_dict








        

        

"""change to use only key"""

"""
Q5PXZU7PQWFPIRYSBDRSUM34PTZKL5INZAPFHFL23C6DWQ4A2IGX5WTPGE
My address: 67EDQPXMWCQJYH7UN72ABWWT4NPCBAWAU4VGQMUHCHKBMNPNG2NTTL7XWM
My private kay: dvW4GBNtWu1giommd17tlesIMmXYlUSr+ch2wqmmB+/3yDg+7LCgnB/0b/QA2tPjXiCCwKcqaDKHEdQWNe02mw==
My passphrase: put toilet middle spell regular deputy fantasy maze visit keep wall rich balcony erode segment noise hammer trade good cherry fatal trust join abstract obey
"""

account1 = "67EDQPXMWCQJYH7UN72ABWWT4NPCBAWAU4VGQMUHCHKBMNPNG2NTTL7XWM"
private_key = "dvW4GBNtWu1giommd17tlesIMmXYlUSr+ch2wqmmB+/3yDg+7LCgnB/0b/QA2tPjXiCCwKcqaDKHEdQWNe02mw=="


af = aWallet("https://testnet-api.algonode.cloud", "https://testnet-idx.algonode.cloud", 1000, "", "", "")
# print(af.send_algo(account1, account1, 1000, "hello"))


print(af.asset_transactions("67EDQPXMWCQJYH7UN72ABWWT4NPCBAWAU4VGQMUHCHKBMNPNG2NTTL7XWM", 10))
# import json

# f = open("indexerassetxn.json", "w")
# esp = af.indexer_client.search_asset_transactions(address="67EDQPXMWCQJYH7UN72ABWWT4NPCBAWAU4VGQMUHCHKBMNPNG2NTTL7XWM", asset_id=153974828, txn_type="axfer")
# json.dump(esp, f, indent=4)