import base58
import logging
import eth_account

from solders.keypair import Keypair
from src.database.database import save_wallet_keys
from tenacity import retry, stop_after_attempt, wait_exponential


logger = logging.getLogger(__name__)


class WalletCreationError(Exception):
    """Custom exception for wallet creation errors"""
    pass


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def generate_wallet_keys(wallet_type: str, user_project_id: int) -> dict or None:
    """
    Add as necessary.
    :param wallet_type: Type of Wallet to be created
    :param user_project_id: User Project ID from database
    """
    try:
        if wallet_type.lower() not in ['ethereum', 'solana']:
            raise ValueError(f"Unsupported wallet type: {wallet_type}")

        if wallet_type == 'ethereum':
            account = eth_account.Account.create()
            private_key = account._private_key.hex()
            public_key = account.address
        elif wallet_type == 'solana':
            keypair = Keypair()
            private_key = base58.b58encode(keypair.secret()).decode('ascii')
            public_key = str(keypair.pubkey())
        else:
            raise ValueError(f"Unexpected wallet type: {wallet_type}")

        if not save_wallet_keys(user_project_id=user_project_id, pub_key=public_key, priv_key=private_key):
            raise WalletCreationError("Failed to save wallet keys to database")

        return {'public_key': public_key}

    except ValueError as ve:
        logger.error(f"Invalid input for wallet creation: {ve}")
        raise
    except Exception as e:
        logger.error(f"Error generating wallet keys: {e}")
        raise


if __name__ == "__main__":
    # Example usage
    ethereum_wallet = generate_wallet_keys('ethereum')
    print("Ethereum Wallet:")
    print(f"Private Key: {ethereum_wallet['private_key']}")
    print(f"Public Key: {ethereum_wallet['public_key']}")

    solana_wallet = generate_wallet_keys('solana')
    print("\nSolana Wallet:")
    print(f"Private Key: {solana_wallet['private_key']}")
    print(f"Public Key: {solana_wallet['public_key']}")
