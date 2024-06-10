import base64
import hashlib
from datetime import datetime

import requests
from algosdk.encoding import is_valid_address
from algosdk.v2client.indexer import IndexerClient


def get_token_price(asset_id: int):
    price = 0
    price_info = requests.get(f"https://free-api.vestige.fi/asset/{asset_id}/price").json()
    if isinstance(price_info, dict) and "USD" in price_info:
        price = price_info["USD"]
    return price

def ___valid_address(addr: str) -> bool:
    """check if an address is valid"""
    return is_valid_address(addr)

def find_amount_w_decimal(amount: int, decimals: int) -> float:
    """returns asset or algo amount with decimal"""
    value = 0
    if decimals != 0:
        # result = '{:.19f}'.format(Decimal(amount) / 10**decimals)
        result = '{:.19f}'.format(amount * 10**-decimals)
        value = round(float(result), decimals)
    else:
        value = amount
    return value

def find_amount_w_decimal_id(client: IndexerClient, amount: int, asset_id: int) -> float:
    """specify the asset id, it will automatically search the asset and return the amount with asset decimals
    a promax version of the above code """
    value = 0
    asset_info = client.asset_info(asset_id=asset_id)
    decimal = asset_info['asset']['params']['decimals']
    if decimal != 0:
        result = '{:.19f}'.format(amount * 10**-decimal)
        value = round(float(result), decimal)
    else:
        value = amount
    return value

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

def date_of_asset_creation(client: IndexerClient, asset_id: int) -> str:
    """returns the date the asset was created"""
    round_number = client.asset_info(asset_id)["asset"]["created-at-round"]
    time_stamp = client.block_info(round_number)["timestamp"]
    return timestamp_to_string(time_stamp)

def all_assets_ownedby_creator(client: IndexerClient, asset_id: int) -> bool:
    """check if all the assets are in the creators wallet, check to destroy asset"""
    asset = client.asset_info(asset_id)
    creator = asset['asset']['params']['creator']
    total_supply = asset['asset']['params']['total']

    acc_info = client.account_info(creator)
    assets = acc_info['account']['assets']
    if assets != []:
        for item in assets:
            asset_index = item['asset-id']
            balance = item['amount']
            if asset_index == asset_id:
                return balance == total_supply
            else:
                return False

def holding_in_address(client: IndexerClient, asset_id: int, wallet_addr: str) -> bool:
    """check if an address is opted in to an asset"""
    response = client.account_info(wallet_addr)
    assets = response['account']['assets']
    for asset in assets:
        return asset_id in asset.values()

def frozen_for_address(client: IndexerClient, asset_id: int, wallet_addr: str) -> bool:
    """check if an asset is frozen for an address"""
    response = client.account_info(wallet_addr)
    assets = response['account']['assets']
    for asset in assets:
        if asset_id in asset.values():
            return asset['is-frozen']

def is_manager_address(client: IndexerClient, asset_id: int, wallet_addr: str) -> bool:
    """check if a specified address is the manager address"""
    response = client.asset_info(asset_id)
    if 'asset' in response:
        manager = response['asset']['params']['manager']
        return wallet_addr == manager
    else:
        return False

def is_creator_address(client: IndexerClient, asset_id: int, wallet_addr: str) -> bool:
    """check if a specified address is the creator address"""
    response = client.asset_info(asset_id)
    if 'asset' in response:
        creator = response['asset']['params']['creator']
        return wallet_addr == creator
    else:
        return False   

def is_freeze_address(client: IndexerClient, asset_id: int, wallet_addr: str) -> bool:
    """check if a specified address is the freeze address"""
    response = client.asset_info(asset_id)
    if 'asset' in response:
        freeze = response['asset']['params']['freeze']
        return wallet_addr == freeze
    else:
        return False

def is_clawback_address(client: IndexerClient, asset_id: int, wallet_addr: str) -> bool:
    """check if a specified address is the clawback address"""
    response = client.asset_info(asset_id)
    if 'asset' in response:
        clawback = response['asset']['params']['clawback']
        return wallet_addr == clawback
    else:
        return False

def is_reserve_address(client: IndexerClient, asset_id: int, wallet_addr: str) -> bool:
    """check if a specified address is the reserve address"""
    response = client.asset_info(asset_id)
    if 'asset' in response:
        reserve = response['asset']['params']['reserve']
        return wallet_addr == reserve
    else:
        return False    

def can_clawback(client: IndexerClient, asset_id: int) -> bool:
    """check if an asset can be clawedback"""
    response = client.asset_info(asset_id)
    if 'asset' in response:
        clawback = response['asset']['params']['clawback']
        return clawback != ""
    else:
        return False

def can_manage(client: IndexerClient, asset_id: int) -> bool:
    """check if an asset can be managed"""
    response = client.asset_info(asset_id)
    if 'asset' in response:
        manager = response['asset']['params']['manager']
        return manager != ""
    else:
        return False

def can_freeze(client: IndexerClient, asset_id: int) -> bool:
    """check if an asset can be frozen"""
    response = client.asset_info(asset_id)
    if 'asset' in response:
        freeze = response['asset']['params']['freeze']
        return freeze != ""
    else:
        return False

def can_reserve(client: IndexerClient, asset_id: int) -> bool:
    """check if an asset can be reserved"""
    response = client.asset_info(asset_id)
    if 'asset' in response:
        reserve = response['asset']['params']['reserve']
        return reserve != ""
    else:
        return False

def is_default_frozen(client: IndexerClient, asset_id: int) -> bool:
    """check if an asset is frozen by default"""
    response = client.asset_info(asset_id)
    if 'asset' in response:
        df_frozen = response['asset']['params']['default-frozen']
        return df_frozen
    else:
        return False

def is_nft(client: IndexerClient, asset_id: int) -> bool:
    """check if an asset is an zero decimal, hence an nft"""
    response = client.asset_info(asset_id)
    if 'asset' in response:
        decimal = response['asset']['params']['decimals']
        return decimal <= 0
    else:
        return False

def r_block_time(client: IndexerClient, block: int) -> str:
    """return the time a block was verified"""
    time_stamp = client.block_info(block)["timestamp"]
    date_time = timestamp_to_string(time_stamp)
    return date_time

def r_nft_holding_address(client: IndexerClient, asset_id: int) -> dict:
    """return the address holding a unique nft"""
    holder = {}
    info = client.asset_balances(asset_id=asset_id, min_balance=0, max_balance=2)
    balances = info["balances"]
    if balances != []:
        for balance in balances:
            holder["address"] = balance["address"]
            holder["amount"] = balance["amount"]
    return holder

def transaction_successful(client: IndexerClient, txid: str) -> str:
    """check if a transaction was successful"""
    response = client.transaction(txid)
    if 'confirmed-round' in response['transaction']:
        return 'success'

def r_transaction_time(client: IndexerClient, txid: str) -> str:
    """return the time a transaction was verified"""
    response = client.transaction(txid)
    return timestamp_to_string(response["transaction"]["round-time"])

def r_note_from_txid(client: IndexerClient, txid: str) -> str:
    """return a note from txid"""
    response = client.transaction(txid)
    if 'note' in response['transaction']:
        return base64.b64decode(response['transaction']['note']).decode()

def r_block_of_txid(client: IndexerClient, txid: str) -> str:
    """return the block a txn was confirmed in"""
    response = client.transaction(txid)
    if 'confirmed-round' in response['transaction']:
        return response['transaction']['confirmed-round']

def r_created_id(client: IndexerClient, txid: str) -> int:
    """returns a created asset id from a transaction id"""
    info = client.transaction(txid)
    asset_id = info['transaction']['created-asset-index']
    return asset_id