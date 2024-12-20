import unittest
from unittest.mock import patch, AsyncMock
import asyncio
from web3 import Web3
from solders.pubkey import Pubkey
from src.crypto.check_balance import (
    check_solana_balance,
    check_ethereum_balance,
    SolanaBalanceCheckError,
    EthereumBalanceCheckError
)


class TestCheckBalance(unittest.TestCase):

    @patch('src.crypto.check_balance.AsyncClient')
    async def test_check_solana_balance_success(self, mock_async_client):
        mock_client = AsyncMock()
        mock_client.is_connected.return_value = True
        mock_client.get_balance.return_value.value = 1000000000  # 1 SOL
        mock_async_client.return_value.__aenter__.return_value = mock_client

        balance = await check_solana_balance("7xLk17EQQ5KLDLDe44wCmupJKJjTGd8hs3eSVVhCx932")

        self.assertEqual(balance, 1.0)
        mock_client.get_balance.assert_called_once()

    @patch('src.crypto.check_balance.AsyncClient')
    async def test_check_solana_balance_connection_error(self, mock_async_client):
        mock_client = AsyncMock()
        mock_client.is_connected.return_value = False
        mock_async_client.return_value.__aenter__.return_value = mock_client

        with self.assertRaises(SolanaBalanceCheckError):
            await check_solana_balance("7xLk17EQQ5KLDLDe44wCmupJKJjTGd8hs3eSVVhCx932")

    @patch('src.crypto.check_balance.AsyncClient')
    async def test_check_solana_balance_invalid_key(self, mock_async_client):
        with self.assertRaises(ValueError):
            await check_solana_balance("invalid_key")

    @patch('src.crypto.check_balance.Web3')
    def test_check_ethereum_balance_success(self, mock_web3):
        mock_w3 = mock_web3.return_value
        mock_w3.is_connected.return_value = True
        mock_w3.is_address.return_value = True
        mock_w3.eth.get_balance.return_value = 1000000000000000000  # 1 ETH
        mock_w3.from_wei.return_value = 1.0

        balance = check_ethereum_balance("0x742d35Cc6634C0532925a3b844Bc454e4438f44e")

        self.assertEqual(balance, 1.0)
        mock_w3.eth.get_balance.assert_called_once()

    @patch('src.crypto.check_balance.Web3')
    def test_check_ethereum_balance_connection_error(self, mock_web3):
        mock_w3 = mock_web3.return_value
        mock_w3.is_connected.return_value = False

        with self.assertRaises(EthereumBalanceCheckError):
            check_ethereum_balance("0x742d35Cc6634C0532925a3b844Bc454e4438f44e")

    @patch('src.crypto.check_balance.Web3')
    def test_check_ethereum_balance_invalid_address(self, mock_web3):
        mock_w3 = mock_web3.return_value
        mock_w3.is_connected.return_value = True
        mock_w3.is_address.return_value = False

        with self.assertRaises(ValueError):
            check_ethereum_balance("invalid_address")

    @patch('src.crypto.check_balance.Web3')
    def test_check_ethereum_balance_arbitrum(self, mock_web3):
        mock_w3 = mock_web3.return_value
        mock_w3.is_connected.return_value = True
        mock_w3.is_address.return_value = True
        mock_w3.eth.get_balance.return_value = 1000000000000000000  # 1 ETH
        mock_w3.from_wei.return_value = 1.0

        balance = check_ethereum_balance("0x742d35Cc6634C0532925a3b844Bc454e4438f44e", "arbitrum")

        self.assertEqual(balance, 1.0)
        mock_w3.eth.get_balance.assert_called_once()

    @patch('src.crypto.check_balance.Web3')
    def test_check_ethereum_balance_optimism(self, mock_web3):
        mock_w3 = mock_web3.return_value
        mock_w3.is_connected.return_value = True
        mock_w3.is_address.return_value = True
        mock_w3.eth.get_balance.return_value = 1000000000000000000  # 1 ETH
        mock_w3.from_wei.return_value = 1.0

        balance = check_ethereum_balance("0x742d35Cc6634C0532925a3b844Bc454e4438f44e", "optimism")

        self.assertEqual(balance, 1.0)
        mock_w3.eth.get_balance.assert_called_once()

    @patch('src.crypto.check_balance.Web3')
    def test_check_ethereum_balance_unsupported_network(self, mock_web3):
        with self.assertRaises(EthereumBalanceCheckError):
            check_ethereum_balance("0x742d35Cc6634C0532925a3b844Bc454e4438f44e", "unsupported_network")


def run_async_test(test_func):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_func(*args, **kwargs))

    return wrapper


class TestAsyncFunctions(unittest.TestCase):

    @run_async_test
    async def test_check_solana_balance(self):
        with patch('src.crypto.check_balance.AsyncClient') as mock_async_client:
            mock_client = AsyncMock()
            mock_client.is_connected.return_value = True
            mock_client.get_balance.return_value.value = 1000000000  # 1 SOL
            mock_async_client.return_value.__aenter__.return_value = mock_client

            balance = await check_solana_balance("7xLk17EQQ5KLDLDe44wCmupJKJjTGd8hs3eSVVhCx932")

            self.assertEqual(balance, 1.0)
            mock_client.get_balance.assert_called_once()


if __name__ == '__main__':
    unittest.main()
