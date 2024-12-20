import os
import asyncio
import logging

from web3 import Web3
from dotenv import load_dotenv
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)
load_dotenv()

INFURA_KEY = os.getenv('INFURA_KEY')
SOLANA_RPC = os.getenv('SOLANA_RPC')
ETHEREUM_MAINNET_RPC = os.getenv('ETHEREUM_MAINNET_RPC')
ETHEREUM_ARBITRUM_RPC = os.getenv('ETHEREUM_ARBITRUM_RPC')
ETHEREUM_OPTIMISM_RPC = os.getenv('ETHEREUM_OPTIMISM_RPC')


class SolanaBalanceCheckError(Exception):
    """Custom exception for Solana balance check errors"""
    pass


class EthereumBalanceCheckError(Exception):
    """Custom exception for Ethereum balance check errors"""
    pass


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def check_solana_balance(public_key_str: str) -> float:
    """
    Check the balance of a Solana wallet.

    :param public_key_str: Solana public key as a string
    :return: Balance in SOL
    :raises ValueError: If the public key is invalid
    :raises SolanaBalanceCheckError: If there's an error checking the balance
    """
    try:
        public_key = Pubkey.from_string(public_key_str)
        async with AsyncClient(SOLANA_RPC) as client:
            if not await client.is_connected():
                raise SolanaBalanceCheckError("Failed to connect to Solana network")

            balance_response = await client.get_balance(public_key)
            if balance_response.value is None:
                raise SolanaBalanceCheckError("Failed to retrieve balance")

            balance_sol = balance_response.value / 1e9
            return balance_sol

    except ValueError as ve:
        logger.error(f"Invalid Solana public key: {ve}")
        raise
    except SolanaBalanceCheckError as sbce:
        logger.error(f"Error checking Solana balance: {sbce}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Solana balance check: {e}")
        raise SolanaBalanceCheckError("Unexpected error during Solana balance check") from e


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def check_ethereum_balance(address: str, network: str = "mainnet") -> float:
    """
    Check the balance of an Ethereum wallet.
    :param network: Ethereum network, default mainnet
    :param address: Ethereum address
    :return: Balance in ETH
    :raises ValueError: If the address is invalid
    :raises EthereumBalanceCheckError: If there's an error checking the balance
    """

    if network == 'mainnet':
        infura_url = ETHEREUM_MAINNET_RPC + INFURA_KEY
        w3 = Web3(Web3.HTTPProvider(infura_url))

    elif network == 'arbitrum':
        infura_url = ETHEREUM_ARBITRUM_RPC + INFURA_KEY
        w3 = Web3(Web3.HTTPProvider(infura_url))

    elif network == 'optimism':
        infura_url = ETHEREUM_OPTIMISM_RPC + INFURA_KEY
        w3 = Web3(Web3.HTTPProvider(infura_url))

    else:
        raise EthereumBalanceCheckError("Network is not supported")

    try:
        if not w3.is_connected():
            raise EthereumBalanceCheckError("Failed to connect to Ethereum network")

        if not w3.is_address(address):
            raise ValueError("Invalid Ethereum address")

        checksum_address = w3.to_checksum_address(address)
        balance_wei = w3.eth.get_balance(checksum_address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        return float(balance_eth)

    except ValueError as ve:
        logger.error(f"Invalid Ethereum address: {ve}")
        raise
    except EthereumBalanceCheckError as ebce:
        logger.error(f"Error checking Ethereum balance: {ebce}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Ethereum balance check: {e}")
        raise EthereumBalanceCheckError("Unexpected error during Ethereum balance check") from e


async def main():
    eth_address = ""
    sol_address = ""

    eth_balance = await check_ethereum_balance(eth_address)
    print(f"The balance of the Ethereum wallet {eth_address} is: {eth_balance} ETH")

    sol_balance = await check_solana_balance(sol_address)
    print(f"The balance of the Solana wallet {sol_address} is: {sol_balance} SOL")


if __name__ == "__main__":
    asyncio.run(main())
