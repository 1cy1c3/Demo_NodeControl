import eth_account
import base58

from solders.keypair import Keypair
from src.database.database import save_wallet_keys
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def generate_wallet_keys(wallet_type: str, user_project_id: int) -> dict or None:
    """
    Add as necessary.
    :param wallet_type: Type of Wallet to be created
    :param user_project_id: User Project ID from database
    """
    if wallet_type.lower() == 'ethereum':
        # Generate Ethereum wallet
        account = eth_account.Account.create()
        private_key = account._private_key.hex()
        public_key = account.address

        saved = save_wallet_keys(user_project_id=user_project_id, pub_key=public_key, priv_key=private_key)
        if saved:
            return {
                'public_key': public_key
            }
        else:
            raise "Failed to save wallet"

    elif wallet_type.lower() == 'solana':
        # Generate Solana wallet
        keypair = Keypair()  # Create a new keypair
        private_key = base58.b58encode(keypair.secret()).decode('ascii')
        public_key = str(keypair.pubkey())
        saved = save_wallet_keys(user_project_id=user_project_id, pub_key=public_key, priv_key=private_key)
        if saved:
            return {
                'public_key': public_key
            }
        else:
            raise "Failed to save wallet"

    else:
        return None


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
