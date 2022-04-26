import base64
import hashlib
from datetime import datetime
from decimal import Decimal
from time import time
from urllib import response

from algosdk import encoding
from algosdk.util import algos_to_microalgos, microalgos_to_algos
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

from EngClient import MintEngineClient

URLS_= {
"ALGOD_TESTNET_URL": "https://testnet-algorand.api.purestake.io/ps2",
"ALGOD_MAINNET_URL": "https://mainnet-algorand.api.purestake.io/ps2",

"INDEXER_TESTNET_URL": "https://testnet-algorand.api.purestake.io/idx2",
"INDEXER_MAINNET_URL": "https://mainnet-algorand.api.purestake.io/idx2",

"MINT_INDEXER_MAINNET_URL": "https://algoindexer.algoexplorerapi.io/v2",
"MINT_INDEXER_TESTNET_URL": "https://algoindexer.testnet.algoexplorerapi.io/v2",

"TESTNET_TXNS": "https://testnet.algoexplorer.io/tx/",
"MAINNET_TXNS": "https://algoexplorer.io/tx/",

"TESTNET_ASSET": "https://algoexplorer.io/asset/",
"MAINNET_ASSET": "https://testnet.algoexplorer.io/asset/",

"MAINNET_ACCOUNT": "https://algoexplorer.io/address/",
"TESTNET_ACCOUNT": "https://testnet.algoexplorer.io/address/",
}

PAY_ADDRESS = {
    "MULTIPLE_TXNS": "",
    "SCHEDULE_TXNS": "",

    "FREEZE_TXNS": "",
    "CLAWBACK_TXNS": "",
    "MODIFY_TXNS": "",
    "DESTROY_TXNS": "",
    "CREATION_TXNS": ""
}

def r_schedule_fee(time_in_seconds: int) -> int:
    """return the amount of fee to pay for scheduling a transaction\n
    pass in time in seconds"""
    min_fee = 0.000004
    max_time = 2592000
    min_time = 60

    assert time_in_seconds >= min_time
    assert time_in_seconds <= max_time

    fee = min_fee * time_in_seconds
    return int(fee * 1000000)

def find_amount_W_decimal(amount: int, decimals: int) -> float:
    """returns asset or algo amount with decimal"""
    # result = '{:.19f}'.format(Decimal(amount) / 10**decimals)
    result = '{:.19f}'.format(amount * 10**-decimals)
    return round(float(result), decimals)

def timestamp_to_string(timestamp: int) -> str:
    """converts a timestamp to a string"""
    dt_obj = datetime.fromtimestamp(timestamp)
    date_time = dt_obj.strftime("%d-%m-%Y, %H:%M:%S")
    return date_time

def meta_hash_file_data(filename: str) -> bytes:
    """Takes any byte data and returns the SHA512/256 hash in base64. in summary: hashes a file"""
    filebytes = open(filename, 'rb').read()
    h = hashlib.sha256()
    h.update(filebytes)
    return h.digest()

def meta_hash_text(string: str) -> bytes:
    """ Takes any byte data and returns the SHA512/256 hash in base64. in summary: hashes a text """
    s = hashlib.sha256()
    string_binary = f'{string}'.encode('utf-8')
    s.update(string_binary)
    return s.digest()

def verify_address(wallet_addr: str) -> bool:
    """check if a wallet address is valid according to algorand method"""
    return encoding.is_valid_address(wallet_addr)

def verify_unit_name(unit_name: str) -> bool:
    """check if the unit-name length is shorter or equal to 8"""
    return len(unit_name) <= 8

def verify_assetname(asset_name: str) -> bool:
    """check if the asset name is shorter than or equal to 32"""
    return len(asset_name) <= 32

def verify_total_supply(total_supply: int) -> bool:
    """check if the total supply is less than or eqaul to 18 quintillion"""
    return total_supply <= 18446744073709552000

def verify_url(url: str) -> bool:
    """check if the asset name is shorter than or equal to 32"""
    return len(url) <= 96

def verify_decimal(decimal: int) -> bool:
    """check if the decimal is lesser than or equal to 19"""
    return decimal <= 19

def verify_note(note: str) -> bool:
    """check if the note is less than or equal to 1000"""
    return len(note) <= 1000

class Misc(MintEngineClient, IndexerClient):
    def __init__(self, mint_indexer_url: str, indexer_url: str, algod_token: str):
        self.headers = {"X-API-Key": algod_token,}
        self.mint_client = MintEngineClient(mint_indexer_url)
        self.indexer_client = IndexerClient("", indexer_url, self.headers)
    
    def change_network(self, mint_indexer_url: str, indexer_url: str) -> bool:
        """change the entirety of the network"""
        self.mint_client = MintEngineClient(mint_indexer_url)
        self.indexer_client = IndexerClient("", indexer_url, self.headers)
        return True
    
    def to_testnet(self) -> bool:
        """change client to testnet"""
        self.mint_client = MintEngineClient("https://algoindexer.testnet.algoexplorerapi.io/v2")
        self.indexer_client = IndexerClient("", "https://testnet-algorand.api.purestake.io/idx2", self.headers)
        return True
    
    def to_mainnet(self) -> bool:
        """change client to mainnet"""
        self.mint_client = MintEngineClient("https://algoindexer.algoexplorerapi.io/v2")
        self.indexer_client = IndexerClient("", "https://mainnet-algorand.api.purestake.io/idx2", self.headers)
        return True

    def change_algod_key(self, key: str) -> bool:
        """change the algod key"""
        self.headers["X-API-Key"] = key
        return True

    def find_amount_W_decimal_id(self, amount: int, asset_id: int) -> float:
        """specify the asset id, it will automatically search the asset and return the amount with asset decimals
        a promax version of the above code """
        asset_info = self.mint_client.asset_info(asset_id=asset_id)
        decimal = asset_info['asset']['params']['decimals']
        result = '{:.19f}'.format(amount * 10**-decimal)
        return round(float(result), decimal)

    def date_of_asset_creation(self, asset_id: int) -> str:
        """returns the date the asset was created"""
        round_number = self.mint_client.asset_info(asset_id)["asset"]["created-at-round"]
        time_stamp = self.mint_client.block_info(round_number)["timestamp"]
        return timestamp_to_string(time_stamp)

    def return_minimum_balance(self, wallet_addr: str) -> float:
        """returns the minimum number of algos an account should be holding"""
        """multiplies the number of assets holding passed by 0.12(minimum per asset)"""
        response = self.mint_client.account_info(wallet_addr)
        assets = response['account']['assets']
        number = len(assets)
        m_bal = 0.12 * number
        return m_bal
    
    def all_assets_ownedby_creator(self, asset_id: int) -> bool:
        """check if all the assets are in the creators wallet"""
        asset = self.mint_client.asset_info(asset_id)
        creator = asset['asset']['params']['creator']
        total_supply = asset['asset']['params']['total']

        acc_info = self.mint_client.account_info(creator)
        assets = acc_info['account']['assets']
        if assets != []:
            for item in assets:
                asset_index = item['asset-id']
                balance = item['amount']
                if asset_index == asset_id:
                    return balance == total_supply
                else:
                    return False

    def holding_in_address(self, asset_id: int, wallet_addr: str) -> bool:
        """check if an address is opted in to an asset"""
        response = self.mint_client.account_info(wallet_addr)
        assets = response['account']['assets']
        for asset in assets:
            return asset_id in asset.values()

    def frozen_for_address(self, asset_id: int, wallet_addr: str) -> bool:
        """check if an asset is frozen for an address"""
        response = self.mint_client.account_info(wallet_addr)
        assets = response['account']['assets']
        for asset in assets:
            if asset_id in asset.values():
                return asset['is-frozen']

    def is_manager_address(self, asset_id: int, wallet_addr: str) -> bool:
        """check if a specified address is the manager address"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            manager = response['asset']['params']['manager']
            return wallet_addr == manager
        else:
            return False

    def is_creator_address(self, asset_id: int, wallet_addr: str) -> bool:
        """check if a specified address is the creator address"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            creator = response['asset']['params']['creator']
            return wallet_addr == creator
        else:
            return False   

    def is_freeze_address(self, asset_id: int, wallet_addr: str) -> bool:
        """check if a specified address is the freeze address"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            freeze = response['asset']['params']['freeze']
            return wallet_addr == freeze
        else:
            return False

    def is_clawback_address(self, asset_id: int, wallet_addr: str) -> bool:
        """check if a specified address is the clawback address"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            clawback = response['asset']['params']['clawback']
            return wallet_addr == clawback
        else:
            return False

    def is_reserve_address(self, asset_id: int, wallet_addr: str) -> bool:
        """check if a specified address is the reserve address"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            reserve = response['asset']['params']['reserve']
            return wallet_addr == reserve
        else:
            return False    

    def can_clawback(self, asset_id: int) -> bool:
        """check if an asset can be clawedback"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            clawback = response['asset']['params']['clawback']
            return clawback != ""
        else:
            return False

    def can_manage(self, asset_id: int) -> bool:
        """check if an asset can be managed"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            manager = response['asset']['params']['manager']
            return manager != ""
        else:
            return False

    def can_freeze(self, asset_id: int) -> bool:
        """check if an asset can be frozen"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            freeze = response['asset']['params']['freeze']
            return freeze != ""
        else:
            return False

    def can_reserve(self, asset_id: int) -> bool:
        """check if an asset can be reserved"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            reserve = response['asset']['params']['reserve']
            return reserve != ""
        else:
            return False
    
    def is_default_frozen(self, asset_id: int) -> bool:
        """check if an asset is frozen by default"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            df_frozen = response['asset']['params']['default-frozen']
            return df_frozen
        else:
            return False

    def is_nft(self, asset_id: int) -> bool:
        """check if an asset is an zero decimal, hence an nft"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            decimal = response['asset']['params']['decimals']
            return decimal <= 0
        else:
            return False

    def r_nft_holding_address(self, asset_id: int) -> dict:
        """return the address holding a unique nft (1)
        a pro version of the `nft_is_payable_to_address` function"""
        holder = {}
        info = self.indexer_client.asset_balances(asset_id=asset_id, min_balance=0, max_balance=2)
        balances = info["balances"]
        if balances != []:
            for balance in balances:
                holder["address"] = balance["address"]
                holder["amount"] = balance["amount"]
        return holder

    def transaction_successful(self, txid: str) -> str:
        """check if a transaction was successful"""
        response = self.indexer_client.transaction(txid)
        if 'confirmed-round' in response['transaction']:
            return 'success'

    def r_transaction_time(self, txid: str) -> str:
        """return the time a transaction was verified"""
        response = self.indexer_client.transaction(txid)
        return timestamp_to_string(response["transaction"]["round-time"])

    def r_note_from_txid(self, txid: str) -> str:
        """return a note from txid"""
        response = self.indexer_client.transaction(txid)
        if 'note' in response['transaction']:
            return base64.b64decode(response['transaction']['note']).decode()
    
    def r_block_time(self, block: int) -> str:
        """return the time a block was verified"""
        time_stamp = self.mint_client.block_info(block)["timestamp"]
        date_time = timestamp_to_string(time_stamp)
        return date_time
    
    def r_block_of_txid(self, txid: str) -> str:
        """return the block a txn was confirmed in"""
        response = self.indexer_client.transaction(txid)
        if 'confirmed-round' in response['transaction']:
            return response['transaction']['confirmed-round']

    def r_created_id(self, txid: str) -> int:
        """returns a created asset id from a transaction id"""
        info = self.indexer_client.transaction(txid)
        asset_id = info['transaction']['created-asset-index']
        return asset_id

    def r_asset_name(self, asset_id: int) -> str:
        """return asset name of a specified asset id"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:    
            if 'name' in response['asset']['params']:
                return response['asset']['params']['name']

    def r_unit_name(self, asset_id: int) -> str:
        """return unit name of a specified asset id"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            if 'unit-name' in response['asset']['params']:
                return response['asset']['params']['unit-name']

    def r_asset_url(self, asset_id: int) -> str:
        """return url of a specified asset id"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            if 'url' in response['asset']['params']:
                return response['asset']['params']['url']

    def r_asset_total(self, asset_id: int) -> str:
        """return total supply of a specified asset id"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            if 'total' in response['asset']['params']:
                return response['asset']['params']['total']

    def r_asset_decimal(self, asset_id: int) -> str:
        """return decimals of a specified asset id"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            if 'decimals' in response['asset']['params']:
                return response['asset']['params']['decimals']

    def r_asset_df_frozen(self, asset_id: int) -> str:
        """return default frozen asset of a specified asset id"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            if 'default-frozen' in response['asset']['params']:
                return response['asset']['params']['default-frozen']

    def r_asset_manager(self, asset_id: int) -> str:
        """returns manager address of a specified asset id"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            if 'manager' in response['asset']['params']:
                return response['asset']['params']['manager']

    def r_asset_clawback(self, asset_id: int) -> str:
        """returns clawback address of a specified asset id"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            if 'clawback' in response['asset']['params']:
                return response['asset']['params']['clawback']

    def r_asset_creator(self, asset_id: int) -> str:
        """returns creator address of a specified asset id"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            if 'creator' in response['asset']['params']:
                return response['asset']['params']['creator']

    def r_asset_freeze(self, asset_id: int) -> str:
        """returns freeze address of a specified asset id"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            if 'freeze' in response['asset']['params']:
                return response['asset']['params']['freeze']

    def r_asset_reserve(self, asset_id: int) -> str:
        """returns reserve address of a specified asset id"""
        response = self.mint_client.asset_info(asset_id)
        if 'asset' in response:
            if 'reserve' in response['asset']['params']:
                return response['asset']['params']['reserve']

indexer_address = "https://testnet-algorand.api.purestake.io/idx2"
algod_token = "HcMuKoVwiiaghFBOIdTFOcK1280ECCA2x4oMLN5h"
indexer_querier = "https://algoindexer.testnet.algoexplorerapi.io/v2"
