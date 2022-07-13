import json
from decimal import Decimal
from textwrap import indent
from typing import Union

from algosdk import account, mnemonic
from algosdk.future import transaction
from algosdk.future.transaction import (AssetTransferTxn, PaymentTxn,
                                        SignedTransaction, Transaction)
from algosdk.util import algos_to_microalgos, microalgos_to_algos
from algosdk.v2client.algod import AlgodClient

from EngClient import MintEngineClient
from Misc import find_amount_W_decimal, timestamp_to_string


class Wallet(AlgodClient, MintEngineClient):
    def __init__(self, mint_indexer_url: str, algod_token: str, algod_url: str, txns_fee: int,
    explorer_account_url: str, explorer_tx_url: str, explorer_asset_url: str):
        self.headers = {"X-API-Key": algod_token,}
        self.token = algod_token
        self.algod_client = AlgodClient(algod_token, algod_url, self.headers)
        self.mint_client = MintEngineClient(mint_indexer_url)
        self.params = self.algod_client.suggested_params()
        self.params.flat_fee = True
        self.params.fee = txns_fee 
        self.explorer_account_url = explorer_account_url
        self.explorer_tx_url = explorer_tx_url
        self.explorer_asset_url = explorer_asset_url

    def generate_algorand_account(self, name: str) -> dict:
        """generate a new algorand account"""
        private_key, address = account.generate_account()
        wallet_passphrase = mnemonic.from_private_key(private_key)
        account_dict = {}
        account_dict['name'] = name
        account_dict['address'] = address
        account_dict['phrase'] = wallet_passphrase
        account_dict['key'] = private_key
        return account_dict

    def restore_account(self, name: str, phrase: str) -> dict: # ✅
        """restore an account from mmemonic"""
        address = mnemonic.to_public_key(phrase)
        private_key = mnemonic.to_private_key(phrase)
        account_dict = {}
        account_dict['name'] = name
        account_dict['address'] = address
        account_dict['phrase'] = phrase
        account_dict['key'] = private_key
        return account_dict

    def address_from_mnemonic(self, phrase: str) -> str:
        """returns wallet address from phrase"""
        wallet_address = mnemonic.to_public_key(phrase)
        return wallet_address

    def key_from_mnemonic(self, phrase: str) -> str:
        """returns private key from phrase"""
        private_key = mnemonic.to_private_key(phrase)
        return private_key

    def mnemonic_from_key(self, key: str) -> str:
        """returns phrase from private key"""
        phrase = mnemonic.from_private_key(key)
        return phrase
    
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

    # def send_algo(self, sender_addr: str, receiver_addr: str, amount: int, sender_key: str, note: str) -> dict:
    #     """send algo"""
    #     txn = PaymentTxn(sender_addr, self.params, receiver_addr, amount, note=note)
    #     stxn = txn.sign(sender_key)
    #     txid = self.algod_client.send_transaction(stxn)
    #     transactioninfo = {}
    #     transactioninfo['txid'] = txid
    #     transactioninfo['link'] = f"{self.explorer_tx_url}{txid}"
    #     return transactioninfo
    
    def change_network(self, algod_url: str, mint_indexer_url: str, explorer_account_url: str,
    explorer_tx_url: str, explorer_asset_url: str) -> bool:
        """change the entirety of the network"""
        self.algod_client = AlgodClient(self.token, algod_url, self.headers)
        self.mint_client = MintEngineClient(mint_indexer_url)
        self.explorer_account_url = explorer_account_url
        self.explorer_tx_url = explorer_tx_url
        self.explorer_asset_url = explorer_asset_url
        return True

    def to_testnet(self) -> bool:
        """changes the client to testnet"""
        self.algod_client = AlgodClient(self.token, "https://testnet-algorand.api.purestake.io/ps2", self.headers)
        self.mint_client = MintEngineClient("https://algoindexer.testnet.algoexplorerapi.io/v2")
        self.explorer_account_url = "https://testnet.algoexplorer.io/address/"
        self.explorer_tx_url = "https://testnet.algoexplorer.io/tx/"
        self.explorer_asset_url = "https://testnet.algoexplorer.io/asset/"
        return True
    
    def to_mainnet(self) -> bool:
        """changes the client to mainnet"""
        self.algod_client = AlgodClient(self.token, "https://mainnet-algorand.api.purestake.io/ps2", self.headers)
        self.mint_client = MintEngineClient("https://algoindexer.algoexplorerapi.io/v2")
        self.explorer_account_url = "https://algoexplorer.io/address/"
        self.explorer_tx_url = "https://algoexplorer.io/tx/"
        self.explorer_asset_url = "https://algoexplorer.io/asset/"
        return True

    def change_algod_key(self, key: str) -> bool:
        """change the algod key"""
        self.headers["X-API-Key"] = key
        return True

    def modify_chain_fee(self, new_fee: int) -> bool:
        """modify the network fee for a faster transaction time"""
        assert new_fee > 1000
        self.params.fee = new_fee
        return True

    def gen_signedalgo_object(self, sender_addr: str, receiver_addr: str, amount: int, sender_key: str, note: str) -> SignedTransaction:
        """return algo payment object, use for scheduled transactions"""
        txn = PaymentTxn(sender_addr, self.params, receiver_addr, algos_to_microalgos(amount), note=note)
        stxn = txn.sign(sender_key)
        return stxn

    # def send_asset(self, sender_addr: str, sender_key: str, receiver_addr: str, asset_id: int, amount: int, note: str) -> dict:
    #     """send a specific asset"""
    #     txn = AssetTransferTxn(sender=sender_addr, sp=self.params, receiver=receiver_addr, amt=amount, index=asset_id, note=note)
    #     stxn = txn.sign(sender_key)
    #     txid = self.algod_client.send_transaction(stxn)
    #     transactioninfo = {}
    #     transactioninfo['txid'] = txid
    #     transactioninfo['link'] = f"{self.explorer_tx_url}{txid}"
    #     return transactioninfo
    
    def gen_signedasset_object(self, sender_addr: str, sender_key: str, receiver_addr: str, asset_id: int, amount: int, note: str) -> SignedTransaction:
        """return asset payment object, use for scheduled transactions"""
        txn = AssetTransferTxn(sender=sender_addr, sp=self.params, receiver=receiver_addr, amt=amount, index=asset_id, note=note)
        stxn = txn.sign(sender_key)
        return stxn

    def send_signed_object(self, stxn: SignedTransaction) -> dict:
        """send a signed transaction, for scheduled transactions"""
        txid = self.algod_client.send_transaction(stxn)
        transactioninfo = {}
        transactioninfo['txid'] = txid
        transactioninfo['link'] = f"{self.explorer_tx_url}{txid}"
        return transactioninfo
    
    def gen_algo_object(self, sender: str, receiver: str, amount: int, note: str) -> PaymentTxn:
        """generate algo payment object, for multiple or single transfers"""
        return PaymentTxn(sender, self.params, receiver, algos_to_microalgos(amount), note=note)

    def gen_asset_object(self, sender: str, receiver: str, amount: int, asset_id: int, note: str) -> AssetTransferTxn:
        """generate asset transfer object, for multiple or single tranfers"""
        return AssetTransferTxn(sender, self.params, receiver, amount, asset_id, note=note)

    def sign_and_sendtxns(self, txns: Union[Transaction, list[Transaction]], sender_key: str) -> dict:
        """sign and send a single transaction or a list, use for multiple transfers"""
        transactioninfo = {}

        if isinstance(txns, Transaction):
            stxn = txns.sign(sender_key)
            txid = self.algod_client.send_transaction(stxn)
            transactioninfo['txid'] = txid
            transactioninfo['link'] = f"{self.explorer_tx_url}{txid}"
            return transactioninfo

        if isinstance(txns, list):
            stxn = None
            stxn_list = []
            gid = transaction.calculate_group_id(txns)
            for txn in txns:
                txn.group = gid
                stxn = txn.sign(sender_key)
                stxn_list.append(stxn)
            txid = self.algod_client.send_transactions(stxn_list)
            transactioninfo['txid'] = txid
            transactioninfo['link'] = f"{self.explorer_tx_url}{txid}"
            return transactioninfo

    def send_future_algo(self, time_in_milli_seconds: int, sender_addr: str, receiver: str, amount: int, sender_key: str, note: str) -> dict:
        """send timed algo transactions by the networks standards, but this is crap"""
        transactioninfo = {}
        params = self.algod_client.suggested_params()
        status = self.algod_client.status()
        current_round = status['last-round']

        avg_blocktime = 4.5
        avg_blocks_produced = time_in_milli_seconds/avg_blocktime
        first_valid_round = int(current_round + avg_blocks_produced)
        last_valid_round = int(first_valid_round + 1000)

        params.flat_fee = True
        params.fee = 1000
        params.first = first_valid_round
        params.last = last_valid_round

        while 1 > 0:
            status = self.algod_client.status()
            current_round = int(status['last-round'])
            if current_round > first_valid_round:
                txn = PaymentTxn(sender_addr, params, receiver, amount, note=note)
                signed_txn = txn.sign(sender_key)
                txid = self.algod_client.send_transaction(signed_txn) # send the transaction
                transactioninfo['txid'] = txid
                transactioninfo['link'] = f"{self.explorer_tx_url}{txid}"
                break
        return transactioninfo   

    def algo_balance(self, wallet_addr: str) -> float:
        """returns algo balance"""
        info = self.mint_client.account_info(wallet_addr)
        balance = float(microalgos_to_algos(info["account"]["amount"]))
        return balance

    def spendable_algo_balance(self, wallet_addr: str) -> float:
        """return algo balance - minimum holding"""
        info = self.mint_client.account_info(wallet_addr)
        balance = float(microalgos_to_algos(info['account']['amount']))
        assets = info['account']['assets']
        number = len(assets)
        m_bal = 0.12 * number
        return balance - m_bal

    def wallet_holdings(self, wallet_addr: str) -> dict:
        """return all balances of assets and algo of a given address"""
        asset_list = []
        response = self.mint_client.account_info(wallet_addr)
        address = response['account']['address']
        # algo_amount = str(microalgos_to_algos(response['amount']))
        
        asset_holdings = {}
        asset_holdings['address'] = address
        # asset_holdings['algo_amount'] = algo_amount

        if 'assets' in response['account']:
            assets = response['account']['assets']
            for asset in assets:
                amount = asset['amount']
                is_frozen = asset['is-frozen']
                asset_id = asset['asset-id']

                asset_data = self.mint_client.asset_info(asset_id)
                if "asset" in asset_data:
                    if 'name' in asset_data['asset']['params']:
                        asset_name = asset_data['asset']['params']['name']
                    if 'unit-name' in asset_data['asset']['params']:
                        asset_unit = asset_data['asset']['params']['unit-name']
                    if 'decimals' in asset_data['asset']['params']:
                        decimal = asset_data['asset']['params']['decimals']
                        if decimal == 0:
                            asset_amount = amount
                        else:
                            asset_amount = find_amount_W_decimal(amount, decimal)
                    
                    asset_dict = {}
                    asset_dict['name'] = asset_name
                    asset_dict['unit'] = asset_unit
                    asset_dict['id'] = asset_id
                    asset_dict['amount'] = asset_amount
                    # asset_dict['pure_amount] = amount
                    asset_dict['decimal'] = decimal
                    asset_dict['frozen'] = is_frozen

                    asset_list.append(asset_dict)
        asset_holdings['assets'] = asset_list
        return asset_holdings

    def created_assets(self, wallet_addr: str) -> dict:
        """returns all assets created by a given address"""
        assets_created = {}
        assets = []
        response = self.mint_client.account_info(wallet_addr)
        created_assets = response['account']['created-assets']
        if created_assets != []:
            for item in created_assets:
                asset_id = item['index']
                params = item['params']
                decimal = params['decimals']
                asset = {}
                if 'name' in params: 
                    asset['name'] = params['name']
                if 'unit-name' in params:
                    asset["unit"] = params['unit-name']
                asset["id"] = asset_id
                if 'decimals' in params:
                    asset["decimal"] = params['decimals']
                if 'default-frozen' in params:
                    asset["default_frozen"] = params['default-frozen']
                if 'total' in params:
                    # asset["pure_total"] = params['total']
                    asset["total"] = find_amount_W_decimal(params['total'], decimal)
                if 'url' in params:
                    asset["url"] = params['url']
                if 'clawback' in params:
                    asset["clawback"] = params['clawback']
                if 'creator' in params:
                    asset["creator"] = params['creator']
                if 'freeze' in params:
                    asset["freeze"] = params['freeze']
                if 'manager' in params:
                    asset["manager"] = params['manager']
                if 'reserve' in params:
                    asset["reserve"] = params['reserve']
                assets.append(asset)
            assets_created['asset-created'] = assets
            return assets_created

    def nft_holdings(self, wallet_addr: str) -> dict:
        """returns all the 0 decimal assets in an address"""
        nft_list = []
        response = self.mint_client.account_info(wallet_addr)
        nft_holdings = {}
        nft_holdings['address'] = wallet_addr
        if 'assets' in response['account']:
            assets = response['account']['assets']
            for asset in assets:
                amount = asset['amount']
                is_frozen = asset['is-frozen']
                asset_id = asset['asset-id']
            
                asset_data = self.mint_client.asset_info(asset_id)
                if "asset" in asset_data:
                    if 'name' in asset_data['asset']['params']:
                        asset_name = asset_data['asset']['params']['name']
                    if 'unit-name' in asset_data['asset']['params']:
                        asset_unit = asset_data['asset']['params']['unit-name']
                    if 'decimals' in asset_data['asset']['params']:
                        decimal = asset_data['asset']['params']['decimals']
                        if decimal == 0:
                            asset_dict = {}
                            asset_dict['name'] = asset_name
                            asset_dict['unit'] = asset_unit
                            asset_dict['id'] = asset_id
                            asset_dict['amount'] = amount
                            # asset_dict['pure_amount] = amount
                            # asset_dict['decimal'] = decimal
                            asset_dict['frozen'] = is_frozen
                            nft_list.append(asset_dict)
        nft_holdings['nfts'] = nft_list
        return nft_holdings

    def recent_algo_transactions(self, wallet_address: str) -> dict:
        """returns last 100 or 1000 algo transactions carried out by an address"""
        transactions_dict = {}
        sent = []
        received = []
        response = self.mint_client.account_algo_transactions(wallet_address, 50) # add limit to how many dev can render
        pay_transactions = response['transactions']
        if pay_transactions == []:
            pass
        else:
            for transaction in pay_transactions:
                transact = {}
                transact['sender'] = transaction['sender']
                transact['receiver'] = transaction['payment-transaction']['receiver']
                # transact['pure_amount'] = transaction['payment-transaction']['amount']
                transact['amount'] = str(microalgos_to_algos(transaction['payment-transaction']['amount']))
                transact['fee'] = transaction['fee']
                transact['txid'] = transaction['id']
                transact['tx_time'] = timestamp_to_string(transaction['round-time'])
                transact['tx_type'] = transaction['tx-type']
                if transact['sender'] == wallet_address:
                    sent.append(transact)
                elif transact['sender'] != wallet_address:
                    received.append(transact)
            transactions_dict['sent'] = sent
            transactions_dict['received'] =  received
            return transactions_dict

    def recent_assets_transfer_transactions(self, wallet_address: str) -> dict:
        """returns the last 100 or 1000 asset transfers carried out by an address"""
        transactions_dict = {}
        sent = []
        received = []
        response = self.mint_client.account_assets_transfer_transactions(wallet_address, 50) # add limit
        axfer_transactions = response['transactions']
        if axfer_transactions == []:
            pass
        else:
            for transaction in axfer_transactions:
                asset_id = transaction['asset-transfer-transaction']['asset-id']
                asset_info = self.mint_client.asset_info(asset_id)
                if "asset" in asset_info:
                    params = asset_info['asset']['params']
                    asset_name = params['name']
                    asset_decimal = params['decimals']

                    transact = {}
                    transact['sender'] = transaction['sender']
                    transact['receiver'] = transaction['asset-transfer-transaction']['receiver']
                    transact['name'] = asset_name
                    transact['asset_id'] = asset_id
                    # transact['pure_amount'] = transaction['asset-transfer-transaction']['amount']
                    transact['amount'] = find_amount_W_decimal(transaction['asset-transfer-transaction']['amount'], asset_decimal)
                    transact['fee'] = transaction['fee']
                    transact['txid'] = transaction['id']
                    transact['tx_time'] = timestamp_to_string(transaction['round-time'])
                    transact['tx_type'] = transaction['tx-type']

                    if transact['sender'] == wallet_address:
                        sent.append(transact)
                    elif transact['sender'] != wallet_address:
                        received.append(transact)
                transactions_dict['sent'] = sent
                transactions_dict['received'] =  received
        return transactions_dict

    # print(recent_assets_transfer_transactions("USF4S3MEMHNTOV3WAFSIC7PZNYTYCMNHYCDDXTI2HFBE3VLTX2WLZMI3FY"))
    def recent_asset_transfer_transactions(self, wallet_address: str, asset_id: int) -> dict:
        """returns the last 100 or 1000 specified asset id transfers carried out by an address"""
        transactions_dict = {}
        sent = []
        received = []
        response = self.mint_client.account_asset_transfer_transactions(wallet_address, asset_id, 50)
        axfer_transactions = response['transactions']
        if axfer_transactions != []:
            for transaction in axfer_transactions:
                asset_id = transaction['asset-transfer-transaction']['asset-id']
                asset_info = self.mint_client.asset_info(asset_id)
                if "asset" in asset_info:
                    asset_name = asset_info['asset']['params']['name']
                    asset_decimal = asset_info['asset']['params']['decimals']

                    transact = {}
                    transact['sender'] = transaction['sender']
                    transact['receiver'] = transaction['asset-transfer-transaction']['receiver']
                    transact['name'] = asset_name
                    transact['asset_id'] = asset_id
                    # transact['pure_amount'] = transaction['asset-transfer-transaction']['amount']
                    transact['amount'] = find_amount_W_decimal(transaction['asset-transfer-transaction']['amount'], asset_decimal)
                    transact['fee'] = transaction['fee']
                    transact['txid'] = transaction['id']
                    transact['tx_time'] = timestamp_to_string(transaction['round-time'])
                    transact['tx_type'] = transaction['tx-type']

                    if transact['sender'] == wallet_address:
                        sent.append(transact)
                    elif transact['sender'] != wallet_address:
                        received.append(transact)
                transactions_dict['sent'] = sent
                transactions_dict['received'] =  received
        return transactions_dict

# wal = Wallet("https://algoindexer.testnet.algoexplorerapi.io/v2",
# "dU2RRWVPW5aWbcCDyzfET7M3FIpEqpkJ2BZmjTxw",
# "https://testnet-algorand.api.purestake.io/ps2",
# 1000, 
# "https://testnet.algoexplorer.io/address/",
# "https://testnet.algoexplorer.io/tx/",
# "https://testnet.algoexplorer.io/asset/")

v = MintEngineClient("https://algoindexer.algoexplorerapi.io/v2")
print(json.dumps(v.account_info("VQIMXAPONHJV3W2HIQACCZWNUC5JIVWIFHRAV35ZH524M6NIZJXXHTLPJE"), indent=2))

# print(wal.recent_asset_transfer_transactions("VQIMXAPONHJV3W2HIQACCZWNUC5JIVWIFHRAV35ZH524M6NIZJXXHTLPJE", 17063481))
# print(wal.wallet_holdings("VQIMXAPONHJV3W2HIQACCZWNUC5JIVWIFHRAV35ZH524M6NIZJXXHTLPJE"))

# account_1 = "VQIMXAPONHJV3W2HIQACCZWNUC5JIVWIFHRAV35ZH524M6NIZJXXHTLPJE"
# account_2 = "HZN5PECG77YA4R5D4HNI3SXQU67IYZ5QULYVIC6ME52OJLJTM2IOZAUZYY"
# account1_private_key = "W3I9M28ZU3BNy8mZKlS4q2F4prsqHH5JDKoRiRe0y2CsEMuB7mnTXdtHRAAhZs2gupRWyCniCu+5P3XGeajKbw=="
# account2_private_key = "VoYXZjLsLc5Wdyf/m1SAPBWSRLzx7jK0DFFrsCpRo8o+W9eQRv/wDkej4dqNyvCnvoxnsKLxVAvMJ3TkrTNmkA=="

# print(mnemonic.from_private_key(account1_private_key))

# wal.to_testnet()

# # txnz = [PaymentTxn(account_1, params, account_2, 130),
# # PaymentTxn(account_1, params, account_2, 120),
# # PaymentTxn(account_1, params, account_2, 110)]
# x = wal.gen_algo_object(account_1, account_2, 3, "")
# y = wal.gen_algo_object(account_1, account_2, 1, "")
# z = wal.gen_algo_object(account_1, account_2, 2, "")
# txnz = [x,y,z]

# print(wal.sign_and_sendtxns(txnz, account1_private_key))
# (txns: Union[Transaction, list[Transaction]], sender_key: str) -> dict:
#     transactioninfo = {}

#     if isinstance(txns, Transaction):
#         stxn = txns.sign(sender_key)
#         txid = algod_client.send_transaction(stxn)
#         transactioninfo['txid'] = txid
#         transactioninfo['link'] = f"{''}{txid}"
#         return transactioninfo

#     if isinstance(txns, list):
#         stxn = None
#         stxn_list = []
#         gid = transaction.calculate_group_id(txns)
#         for txn in txns:
#             txn.group = gid
#             stxn = txn.sign(sender_key)
#             stxn_list.append(stxn)
#         txid = algod_client.send_transactions(stxn_list)
#         transactioninfo['txid'] = txid
#         transactioninfo['link'] = f"{''}{txid}"
#         return transactioninfo

# print(sign_and_sendtxns(txnz, account1_private_key))
