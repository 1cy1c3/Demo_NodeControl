import unittest
from unittest.mock import patch, MagicMock
from src.crypto.create_wallet import generate_wallet_keys, WalletCreationError


class TestCreateWallet(unittest.TestCase):

    @patch('src.crypto.create_wallet.eth_account.Account.create')
    @patch('src.crypto.create_wallet.save_wallet_keys')
    def test_generate_ethereum_wallet(self, mock_save_wallet_keys, mock_create_account):
        # Setup
        mock_account = MagicMock()
        mock_account._private_key.hex.return_value = 'mock_private_key'
        mock_account.address = 'mock_public_key'
        mock_create_account.return_value = mock_account
        mock_save_wallet_keys.return_value = True

        # Execute
        result = generate_wallet_keys('ethereum', 123)

        # Assert
        self.assertEqual(result, {'public_key': 'mock_public_key'})
        mock_create_account.assert_called_once()
        mock_save_wallet_keys.assert_called_once_with(
            user_project_id=123,
            pub_key='mock_public_key',
            priv_key='mock_private_key'
        )

    @patch('src.crypto.create_wallet.Keypair')
    @patch('src.crypto.create_wallet.base58.b58encode')
    @patch('src.crypto.create_wallet.save_wallet_keys')
    def test_generate_solana_wallet(self, mock_save_wallet_keys, mock_b58encode, mock_keypair):
        # Setup
        mock_keypair_instance = MagicMock()
        mock_keypair_instance.pubkey.return_value = 'mock_public_key'
        mock_keypair_instance.secret.return_value = b'mock_secret'
        mock_keypair.return_value = mock_keypair_instance
        mock_b58encode.return_value = b'mock_encoded_private_key'
        mock_save_wallet_keys.return_value = True

        # Execute
        result = generate_wallet_keys('solana', 123)

        # Assert
        self.assertEqual(result, {'public_key': 'mock_public_key'})
        mock_keypair.assert_called_once()
        mock_b58encode.assert_called_once_with(b'mock_secret')
        mock_save_wallet_keys.assert_called_once_with(
            user_project_id=123,
            pub_key='mock_public_key',
            priv_key='mock_encoded_private_key'
        )

    def test_generate_wallet_unsupported_type(self):
        with self.assertRaises(ValueError):
            generate_wallet_keys('unsupported_type', 123)

    @patch('src.crypto.create_wallet.eth_account.Account.create')
    @patch('src.crypto.create_wallet.save_wallet_keys')
    def test_generate_wallet_save_failure(self, mock_save_wallet_keys, mock_create_account):
        # Setup
        mock_account = MagicMock()
        mock_account._private_key.hex.return_value = 'mock_private_key'
        mock_account.address = 'mock_public_key'
        mock_create_account.return_value = mock_account
        mock_save_wallet_keys.return_value = False

        # Execute and Assert
        with self.assertRaises(WalletCreationError):
            generate_wallet_keys('ethereum', 123)

    @patch('src.crypto.create_wallet.eth_account.Account.create')
    def test_generate_wallet_unexpected_error(self, mock_create_account):
        # Setup
        mock_create_account.side_effect = Exception("Unexpected error")

        # Execute and Assert
        with self.assertRaises(Exception):
            generate_wallet_keys('ethereum', 123)


if __name__ == '__main__':
    unittest.main()
