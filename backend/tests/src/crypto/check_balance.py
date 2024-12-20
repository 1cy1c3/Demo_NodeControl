import os
from web3 import Web3
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
import asyncio
from dotenv import load_dotenv


# Get the INFURA_KEY from the .env file
load_dotenv()
INFURA_KEY = os.getenv('INFURA_KEY')


async def check_solana_balance(public_key_str):
    try:
        public_key = Pubkey.from_string(public_key_str)
        async with AsyncClient("https://api.mainnet-beta.solana.com") as client:
            if not await client.is_connected():
                return "Failed to connect to Solana network"

            balance_response = await client.get_balance(public_key)
            if balance_response.value is not None:
                balance_sol = balance_response.value / 1e9
                return balance_sol
            else:
                return "Failed to retrieve balance"
    except Exception as e:
        return f"An error occurred: {str(e)}"


async def check_ethereum_balance(address):
    infura_url = f"https://mainnet.infura.io/v3/{INFURA_KEY}"
    w3 = Web3(Web3.HTTPProvider(infura_url))

    try:
        if not w3.is_connected():
            return "Failed to connect to Ethereum network"

        if not w3.is_address(address):
            return "Invalid Ethereum address"

        checksum_address = w3.to_checksum_address(address)
        balance_wei = w3.eth.get_balance(checksum_address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        return float(balance_eth)
    except Exception as e:
        return f"An error occurred: {str(e)}"


async def main():
    eth_address = ""
    sol_address = ""

    eth_balance = await check_ethereum_balance(eth_address)
    print(f"The balance of the Ethereum wallet {eth_address} is: {eth_balance} ETH")

    sol_balance = await check_solana_balance(sol_address)
    print(f"The balance of the Solana wallet {sol_address} is: {sol_balance} SOL")


if __name__ == "__main__":
    asyncio.run(main())
