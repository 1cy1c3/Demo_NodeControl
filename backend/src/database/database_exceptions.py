class UserRegistrationError(Exception):
    """Custom exception for user registration errors"""
    pass


class UserProjectCreationError(Exception):
    """Custom exception for user project creation errors"""
    pass


class WalletKeySaveError(Exception):
    """Custom exception for wallet key save errors"""
    pass


class InstanceIPUpdateError(Exception):
    """Custom exception for instance IP update errors"""
    pass


class PasswordGenerationError(Exception):
    """Custom exception for password generation and save errors"""
    pass


class PasswordSaveError(Exception):
    """Custom exception for password saving errors"""
    pass


class DatabaseFetchError(Exception):
    """Custom exception for database fetch errors"""
    pass


class DecryptionError(Exception):
    """Custom exception for decryption errors"""
    pass


class VPSDataFetchError(Exception):
    """Custom exception for VPS data fetch errors"""
    pass


class EmailVerificationError(Exception):
    """Custom exception for email verification errors"""
    pass


class PasswordResetInitiationError(Exception):
    """Custom exception for password reset initiation errors"""
    pass


class PasswordResetCompletionError(Exception):
    """Custom exception for password reset completion errors"""
    pass


class UserLoginError(Exception):
    """Custom exception for user login errors"""
    pass


class ProjectCreationError(Exception):
    """Custom exception for project creation errors"""
    pass
