import os
import bcrypt
import pyodbc
import string
import secrets
import logging
import smtplib

from dotenv import load_dotenv
from typing import List, Dict, Tuple, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from cryptography.fernet import Fernet, InvalidToken
from datetime import datetime

from src.database.database_exceptions import (
    UserRegistrationError, UserProjectCreationError, WalletKeySaveError, InstanceIPUpdateError,
    PasswordGenerationError, PasswordSaveError, DatabaseFetchError, EmailVerificationError, DecryptionError,
    VPSDataFetchError, UserLoginError, PasswordResetCompletionError, PasswordResetInitiationError
)

# Database connection string
load_dotenv()
DB_CONNECTION_STRING = os.getenv('MSSQL_CONNECTION_STRING')
MAIL_ADDRESS = os.getenv("MAIL_ADDRESS")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
BASE_URL = os.getenv('BASE_URL')
logger = logging.getLogger(__name__)


def register_user(username: str, email: str, password: str) -> Tuple[int, str, None] | Tuple[None, None, str]:
    """
    Register a new user in the database.

    :param username: Username for the new user
    :param email: Email address for the new user
    :param password: Password for the new user
    :return: Tuple of (user_id, None) if successful, or (None, error_message) if failed
    :raises UserRegistrationError: If there's an error during user registration
    """
    try:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        verification_token = secrets.token_urlsafe(32)

        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                cursor.execute("{CALL sp_RegisterUser(?,?,?,?,?)}",
                               (username, email, hashed_password.decode('utf-8'), salt.decode('utf-8'),
                                verification_token))
                user_id = cursor.fetchval()
                conn.commit()

                if user_id is not None:
                    logger.info(f"User registered successfully with ID: {user_id}")
                    return int(user_id), verification_token, None
                else:
                    raise UserRegistrationError("Failed to retrieve user ID after registration")

    except pyodbc.IntegrityError as e:
        if "50001" in str(e):
            logger.warning(f"Registration failed: Username '{username}' already exists")
            return None, None, "Username already exists"
        elif "50002" in str(e):
            logger.warning(f"Registration failed: Email '{email}' already exists")
            return None, None, "Email already exists"
        else:
            logger.error(f"Database integrity error during user registration: {e}")
            raise UserRegistrationError(f"Database integrity error: {str(e)}") from e
    except pyodbc.Error as e:
        logger.error(f"Database error during user registration: {e}")
        raise UserRegistrationError(f"Database error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error during user registration: {e}")
        raise UserRegistrationError(f"Unexpected error: {str(e)}") from e


def create_user_project(user_id: int, project_id: int, instance_id: str) -> Optional[int]:
    """
    Create a new user project in the database.

    :param user_id: ID of the user
    :param project_id: ID of the project
    :param instance_id: ID of the instance
    :return: ID of the created user project, or None if creation failed
    :raises UserProjectCreationError: If there's an error during user project creation
    """
    try:
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                # Insert into User_Projects, including the network information
                cursor.execute("""
                INSERT INTO User_Projects (
                    UserProject_UserIdKey, 
                    UserProject_ProjectIdKey, 
                    UserProject_InstanceId, 
                    UserProject_Version,
                    UserProject_Network
                )
                OUTPUT INSERTED.UserProject_IdKey
                SELECT 
                    ?, 
                    ?, 
                    ?, 
                    Project_Version,
                    Project_Network
                FROM Projectdata
                WHERE Project_IdKey = ?
                """, (user_id, project_id, instance_id, project_id))
                user_project_id = cursor.fetchval()

                if user_project_id is None:
                    raise UserProjectCreationError("Failed to create user project")

                # Create an entry in UserKeys
                cursor.execute("""
                INSERT INTO UserKeys (UserKey_UserProjectIdKey)
                VALUES (?)
                """, (user_project_id,))

                conn.commit()
                logger.info(f"User project created successfully with ID: {user_project_id}")
                return user_project_id

    except pyodbc.IntegrityError as e:
        logger.error(f"Database integrity error during user project creation: {e}")
        raise UserProjectCreationError(f"Database integrity error: {str(e)}") from e
    except pyodbc.Error as e:
        logger.error(f"Database error during user project creation: {e}")
        raise UserProjectCreationError(f"Database error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error during user project creation: {e}")
        raise UserProjectCreationError(f"Unexpected error: {str(e)}") from e


def _create_user_project(user_id: int, project_id: int, instance_id: int) -> Optional[int]:
    """
    Create a new user project in the database.

    :param user_id: ID of the user
    :param project_id: ID of the project
    :param instance_id: ID of the instance
    :return: ID of the created user project, or None if creation failed
    :raises UserProjectCreationError: If there's an error during user project creation
    """
    try:
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                # Insert into User_Projects, including the network information
                cursor.execute("""
                INSERT INTO User_Projects (
                    UserProject_UserIdKey, 
                    UserProject_ProjectIdKey, 
                    UserProject_InstanceId, 
                    UserProject_Version,
                    UserProject_Network
                )
                OUTPUT INSERTED.UserProject_IdKey
                SELECT 
                    ?, 
                    ?, 
                    ?, 
                    Project_Version,
                    Project_Network
                FROM Projectdata
                WHERE Project_IdKey = ?
                """, (user_id, project_id, instance_id, project_id))
                user_project_id = cursor.fetchval()

                if user_project_id is None:
                    raise UserProjectCreationError("Failed to create user project")

                # Create an entry in UserKeys
                cursor.execute("""
                INSERT INTO UserKeys (UserKey_UserProjectIdKey)
                VALUES (?)
                """, (user_project_id,))

                conn.commit()
                logger.info(f"User project created successfully with ID: {user_project_id}")
                return user_project_id

    except pyodbc.IntegrityError as e:
        logger.error(f"Database integrity error during user project creation: {e}")
        raise UserProjectCreationError(f"Database integrity error: {str(e)}") from e
    except pyodbc.Error as e:
        logger.error(f"Database error during user project creation: {e}")
        raise UserProjectCreationError(f"Database error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error during user project creation: {e}")
        raise UserProjectCreationError(f"Unexpected error: {str(e)}") from e


def save_wallet_keys(user_project_id: int, pub_key: str, priv_key: str) -> bool:
    """
    Save encrypted wallet keys for a user project.

    :param user_project_id: ID of the user project
    :param pub_key: Public key of the wallet
    :param priv_key: Private key of the wallet
    :return: True if keys were saved successfully, False otherwise
    :raises WalletKeySaveError: If there's an error during the key saving process
    """
    try:
        # Retrieve the stored Fernet key
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT UserKey_IV FROM UserKeys WHERE UserKey_UserProjectIdKey = ?", user_project_id)
                row = cursor.fetchone()
                if not row or row.UserKey_IV is None:
                    raise WalletKeySaveError("No Fernet key found for this user project")
                fernet_key = row.UserKey_IV

        # Create Fernet instance
        fernet = Fernet(fernet_key)

        # Encrypt the wallet keys
        encrypted_pub_key = fernet.encrypt(pub_key.encode())
        encrypted_priv_key = fernet.encrypt(priv_key.encode())

        # Update the UserKeys table with the encrypted wallet keys
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                UPDATE UserKeys 
                SET UserKey_EncryptedPubKey = ?, UserKey_EncryptedPrivKey = ?
                WHERE UserKey_UserProjectIdKey = ?
                """, (encrypted_pub_key, encrypted_priv_key, user_project_id))
                conn.commit()

        logger.info(f"Wallet keys saved successfully for user project ID: {user_project_id}")
        return True

    except pyodbc.Error as e:
        logger.error(f"Database error while saving wallet keys: {e}")
        raise WalletKeySaveError(f"Database error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error while saving wallet keys: {e}")
        raise WalletKeySaveError(f"Unexpected error: {str(e)}") from e


def update_instance_ip(instance_id: str, ip_address: str) -> bool:
    """
    Update the IP address for a given instance.

    :param instance_id: ID of the instance
    :param ip_address: New IP address to be set
    :return: True if the update was successful, False otherwise
    :raises InstanceIPUpdateError: If there's an error during the IP update process
    """
    try:
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                UPDATE UserKeys
                SET UserKey_IPAddress = ?
                FROM UserKeys UK
                INNER JOIN User_Projects UP ON UK.UserKey_UserProjectIdKey = UP.UserProject_IdKey
                WHERE UP.UserProject_InstanceId = ?
                """, (ip_address, instance_id))

                if cursor.rowcount == 0:
                    logger.warning(f"No matching record found for instance ID: {instance_id}")
                    return False

                conn.commit()
                logger.info(f"IP address updated successfully for instance ID: {instance_id}")
                return True

    except pyodbc.Error as e:
        logger.error(f"Database error while updating instance IP: {e}")
        raise InstanceIPUpdateError(f"Database error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error while updating instance IP: {e}")
        raise InstanceIPUpdateError(f"Unexpected error: {str(e)}") from e


def generate_and_save_password(user_project_id: int) -> Optional[str]:
    """
    Generate a random password, encrypt it, and save it for a user project.

    :param user_project_id: ID of the user project
    :return: The generated password if successful, None otherwise
    :raises PasswordGenerationError: If there's an error during password generation or saving
    """
    try:
        # Generate a random 32-character password
        password = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(32))

        # Generate a Fernet key
        fernet_key = Fernet.generate_key()
        fernet = Fernet(fernet_key)
        encrypted_password = fernet.encrypt(password.encode())

        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                UPDATE UserKeys
                SET UserKey_EncryptedPassword = ?, UserKey_IV = ?
                WHERE UserKey_UserProjectIdKey = ?
                """, (encrypted_password, fernet_key, user_project_id))
                conn.commit()

        logger.info(f"Password generated and saved successfully for user project ID: {user_project_id}")
        return password

    except pyodbc.Error as e:
        logger.error(f"Database error while generating and saving password: {e}")
        raise PasswordGenerationError(f"Database error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error while generating and saving password: {e}")
        raise PasswordGenerationError(f"Unexpected error: {str(e)}") from e


def generate_password_and_key() -> Tuple[str, bytes]:
    # Generate a random 32-character password
    try:
        # Generate a random 32-character password
        password = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(32))

        # Generate a Fernet key
        fernet_key = Fernet.generate_key()

        logger.info("Password and Fernet key generated successfully")
        return password, fernet_key
    except Exception as e:
        logger.error(f"Error generating password and key: {e}")
        raise PasswordGenerationError(f"Failed to generate password and key: {str(e)}") from e


def save_encrypted_password(user_project_id: int, password: str, fernet_key: bytes) -> bool:
    try:
        fernet = Fernet(fernet_key)
        encrypted_password = fernet.encrypt(password.encode())

        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                UPDATE UserKeys
                SET UserKey_EncryptedPassword = ?, UserKey_IV = ?
                WHERE UserKey_UserProjectIdKey = ?
                """, (encrypted_password, fernet_key, user_project_id))
                conn.commit()

        logger.info(f"Encrypted password saved successfully for user project ID: {user_project_id}")
        return True
    except pyodbc.Error as e:
        logger.error(f"Database error while saving encrypted password: {e}")
        raise PasswordSaveError(f"Failed to save encrypted password: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error while saving encrypted password: {e}")
        raise PasswordSaveError(f"Unexpected error while saving encrypted password: {str(e)}") from e


def fetch_pending_instances() -> List[Dict]:
    try:
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT UK.UserKey_UserProjectIdKey, UP.UserProject_InstanceId
                    FROM UserKeys UK
                    INNER JOIN User_Projects UP ON UK.UserKey_UserProjectIdKey = UP.UserProject_IdKey
                    WHERE UK.UserKey_IPAddress IS NULL
                    AND UK.UserKey_EncryptedPubKey IS NOT NULL
                    AND UK.UserKey_EncryptedPrivKey IS NOT NULL
                    AND UK.UserKey_EncryptedPubKey != ''
                    AND UK.UserKey_EncryptedPrivKey != ''
                """)
                results = [{"user_project_id": row.UserKey_UserProjectIdKey, "instance_id": row.UserProject_InstanceId}
                           for row in cursor.fetchall()]

        logger.info(f"Successfully fetched {len(results)} pending instances")
        return results
    except pyodbc.Error as e:
        logger.error(f"Database error while fetching pending instances: {e}")
        raise DatabaseFetchError(f"Failed to fetch pending instances: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error while fetching pending instances: {e}")
        raise DatabaseFetchError(f"Unexpected error while fetching pending instances: {str(e)}") from e


def decrypt_data(encrypted_data, fernet_key):
    try:
        # Ensure fernet_key is in the correct format
        if isinstance(fernet_key, str):
            fernet_key = fernet_key.encode('utf-8')

        fernet = Fernet(fernet_key)

        # If encrypted_data is a string, treat it as a UTF-8 encoded representation of bytes
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode('utf-8')

        # Decrypt the data
        decrypted_data = fernet.decrypt(encrypted_data)
        return decrypted_data.decode('utf-8')

    except InvalidToken as e:
        logger.error(f"Invalid token error during decryption: {e}")
        raise DecryptionError(f"Invalid token during decryption: {str(e)}") from e
    except Exception as e:
        logger.error(f"Decryption error: {type(e).__name__}: {str(e)}")
        logger.error(f"Encrypted data type: {type(encrypted_data)}")
        logger.error(f"Encrypted data length: {len(encrypted_data)}")
        logger.error(f"Encrypted data (first 50 bytes): {encrypted_data[:50]}")
        logger.error(f"Fernet key type: {type(fernet_key)}")
        logger.error(f"Fernet key length: {len(fernet_key)}")
        raise DecryptionError(f"Failed to decrypt data: {str(e)}") from e


def fetch_vps_data(user_project_id: int) -> Dict[str, any]:
    try:
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                query = """
                SELECT 
                    UK.UserKey_IPAddress,
                    CAST(UK.UserKey_EncryptedPubKey AS VARBINARY(MAX)) AS EncryptedPubKey,
                    CAST(UK.UserKey_EncryptedPrivKey AS VARBINARY(MAX)) AS EncryptedPrivKey,
                    CAST(UK.UserKey_EncryptedPassword AS VARBINARY(MAX)) AS EncryptedPassword,
                    UK.UserKey_IV,
                    PD.Project_Name
                FROM UserKeys UK
                JOIN User_Projects UP ON UK.UserKey_UserProjectIdKey = UP.UserProject_IdKey
                JOIN Projectdata PD ON UP.UserProject_ProjectIdKey = PD.Project_IdKey
                WHERE UK.UserKey_UserProjectIdKey = ?
                """
                cursor.execute(query, (str(user_project_id),))
                row = cursor.fetchone()

                if not row:
                    raise VPSDataFetchError(f"No data found for user_project_idkey: {user_project_id}")

                ip_address, encrypted_pub_key, encrypted_priv_key, encrypted_password, fernet_key, project_name = row

                pub_key = decrypt_data(encrypted_pub_key, fernet_key)
                priv_key = decrypt_data(encrypted_priv_key, fernet_key)
                password = decrypt_data(encrypted_password, fernet_key)

                if not all([pub_key, priv_key, password]):
                    raise VPSDataFetchError("One or more decryption operations failed")

                return {
                    'ip': ip_address,
                    'wallet': pub_key,
                    'priv_key': priv_key,
                    'password': password,
                    'project_name': project_name
                }

    except pyodbc.Error as e:
        logger.error(f"Database error in fetch_vps_data: {e}")
        raise VPSDataFetchError(f"Database error while fetching VPS data: {str(e)}") from e
    except DecryptionError as e:
        logger.error(f"Decryption error in fetch_vps_data: {e}")
        raise VPSDataFetchError(f"Decryption error while fetching VPS data: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error in fetch_vps_data: {e}")
        raise VPSDataFetchError(f"Unexpected error while fetching VPS data: {str(e)}") from e


def verify_email_process(token: str, email: str) -> bool:
    try:
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                cursor.execute("{CALL sp_VerifyEmail(?, ?, ?)}", (email, token, pyodbc.SQL_PARAM_OUTPUT))
                # Fetch the result
                row = cursor.fetchone()
                if row is None:
                    raise ValueError("No result returned from sp_VerifyEmail")

                result = row.Result  # Use column name to access the result
                print(result)
                if result == 0:
                    return True
                else:
                    return False

    except Exception as e:
        logger.error(f"Error during email verification: {e}")
        raise EmailVerificationError(f"Error during email verification: {e}") from e


def initiate_password_reset(email: str, reset_token: str, expiration_time: datetime) -> bool:
    try:
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                result = cursor.execute("{CALL sp_InitiatePasswordReset(?, ?, ?, ?)}",
                                        (email, reset_token, expiration_time, 0)).fetchone()[0]
                conn.commit()

                if result == 0:
                    logger.info(f"Password reset initiated successfully for email: {email}")
                    return True
                else:
                    logger.warning(f"Failed to initiate password reset for email: {email}")
                    return False

    except pyodbc.Error as e:
        logger.error(f"Database error during password reset initiation: {e}")
        raise PasswordResetInitiationError(f"Failed to initiate password reset: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error during password reset initiation: {e}")
        raise PasswordResetInitiationError(f"Unexpected error during password reset initiation: {str(e)}") from e


def complete_password_reset(reset_token: str, new_password: str) -> bool:
    try:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)

        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                result = cursor.execute("{CALL sp_CompletePasswordReset(?, ?, ?, ?)}",
                                        (reset_token, hashed_password.decode('utf-8'),
                                         salt.decode('utf-8'), 0)).fetchone()[0]
                conn.commit()

                if result == 0:
                    logger.info(f"Password reset completed successfully for token: {reset_token}")
                    return True
                else:
                    logger.warning(f"Failed to complete password reset for token: {reset_token}")
                    return False

    except pyodbc.Error as e:
        logger.error(f"Database error during password reset completion: {e}")
        raise PasswordResetCompletionError(f"Failed to complete password reset: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error during password reset completion: {e}")
        raise PasswordResetCompletionError(f"Unexpected error during password reset completion: {str(e)}") from e


def login_user(email: str, password: str, ip_address: str) -> Tuple[int | None, str | None, None | str]:
    try:
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                # Execute the stored procedure
                cursor.execute("{CALL sp_UserLogin (?, ?)}", (email, ip_address))

                # Fetch the result
                row = cursor.fetchone()
                if row is None:
                    raise ValueError("No result returned from sp_UserLogin")

                result = row.Result  # Use column name to access the result

                if result == 0:
                    # Fetch user details and check password
                    user = cursor.execute(
                        "SELECT User_IdKey, User_PasswordHash, User_Name FROM Userdata WHERE User_Mail = ?",
                        (email,)).fetchone()
                    if user and bcrypt.checkpw(password.encode('utf-8'), user.User_PasswordHash.encode('utf-8')):
                        # Reset failed login attempts
                        cursor.execute("{CALL sp_UpdateFailedLoginAttempts(?, ?)}", (user.User_IdKey, 0))
                        conn.commit()
                        logger.info(f"User logged in successfully: {email}")
                        return user.User_IdKey, user.User_Name, None
                    else:
                        # Increment failed login attempts
                        if user:
                            cursor.execute("{CALL sp_UpdateFailedLoginAttempts(?, ?)}", (user.User_IdKey, 1))
                            conn.commit()
                        logger.warning(f"Login failed: Invalid password for email: {email}")
                        return None, None, "Invalid password"
                elif result == -1:
                    logger.warning(f"Login failed: User not found for email: {email}")
                    return None, None, "User not found"
                elif result == -2:
                    logger.warning(f"Login failed: Email not verified for: {email}")
                    return None, None, "Email not verified"
                elif result == -3:
                    logger.warning(f"Login failed: Account is locked for email: {email}")
                    return None, None, "Account is locked"
                else:
                    logger.error(f"Unknown login result: {result} for email: {email}")
                    return None, None, "Unknown error occurred"

    except pyodbc.Error as e:
        logger.error(f"Database error during login: {str(e)}")
        raise UserLoginError(f"Database error occurred: {str(e)}") from e
    except Exception as e:
        logger.error(str(e))
        raise UserLoginError(f"User Login error occurred: {str(e)}") from e


def send_verification_email(email: str, verification_token: str):
    message = MIMEMultipart("alternative")
    message["Subject"] = "Verify your email"
    message["From"] = MAIL_ADDRESS
    message["To"] = email

    verification_link = f"{BASE_URL}/verify_email?token={verification_token}&email={email}"
    html = f"""
    <html>
      <body>
        <p>Please click the link below to verify your email:</p>
        <p><a href="{verification_link}">Verify Email</a></p>
      </body>
    </html>
    """
    part = MIMEText(html, "html")
    message.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(MAIL_ADDRESS, MAIL_PASSWORD)
        server.sendmail(MAIL_ADDRESS, email, message.as_string())


def fetch_user_projects(user_id: int) -> List[Dict]:
    """
    Fetch all user project data for a specific user ID and return it as JSON.

    :param user_id: ID of the user
    :return: JSON string containing user project data
    :raises DatabaseFetchError: If there's an error during the database fetch operation
    """
    try:
        with pyodbc.connect(DB_CONNECTION_STRING) as conn:
            with conn.cursor() as cursor:
                query = """
                SELECT 
                    UP.UserProject_IdKey,
                    UP.UserProject_ProjectIdKey,
                    UP.UserProject_InstanceId,
                    UP.UserProject_Version,
                    UP.UserProject_Network,
                    UP.UserProject_CreationDate,
                    UP.UserProject_LastModifiedDate,
                    P.Project_Name,
                    P.Project_Image,
                    UK.UserKey_IPAddress,
                    UK.UserKey_EncryptedPubKey,
                    UK.UserKey_EncryptedPrivKey
                FROM 
                    User_Projects UP
                JOIN 
                    Projectdata P ON UP.UserProject_ProjectIdKey = P.Project_IdKey
                LEFT JOIN
                    UserKeys UK ON UP.UserProject_IdKey = UK.UserKey_UserProjectIdKey
                WHERE 
                    UP.UserProject_UserIdKey = ?
                """
                cursor.execute(query, (user_id,))

                projects: List[Dict] = []
                for row in cursor.fetchall():
                    project = {
                        "id": row.UserProject_IdKey,
                        "project_id": row.UserProject_ProjectIdKey,
                        "instance_id": row.UserProject_InstanceId,
                        "version": row.UserProject_Version,
                        "network": row.UserProject_Network,
                        "creation_date": row.UserProject_CreationDate.isoformat()
                        if row.UserProject_CreationDate else None,

                        "last_modified_date": row.UserProject_LastModifiedDate.isoformat()
                        if row.UserProject_LastModifiedDate else None,

                        "project_name": row.Project_Name,
                        "ip_address": row.UserKey_IPAddress,
                        "public_key": row.UserKey_EncryptedPubKey,
                        "private_key": row.UserKey_EncryptedPrivKey,
                    }
                    projects.append(project)

        return projects

    except pyodbc.Error as e:
        logger.error(f"Database error while fetching user projects: {e}")
        raise DatabaseFetchError(f"Failed to fetch user projects: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error while fetching user projects: {e}")
        raise DatabaseFetchError(f"Unexpected error while fetching user projects: {str(e)}") from e


def main():
    # User registration
    while True:
        username = input("Enter username: ")
        email = input("Enter email: ")
        password = input("Enter password: ")

        user_id, error = register_user(username, email, password)
        if error:
            print(error)
            continue_registration = input("Do you want to try again? (y/n): ")
            if continue_registration.lower() != 'y':
                return
        else:
            print(f"User registered successfully with ID: {user_id}")
            break

    # Create user project
    project_id = int(input("Enter project ID: "))
    instance_id = input("Enter instance ID: ")

    user_project_id = create_user_project(user_id, project_id, instance_id)
    if user_project_id is not None:
        print(f"User project created successfully with ID: {user_project_id}")
    else:
        print("Failed to create user project.")
        return

    # Generate and save password
    if generate_and_save_password(user_project_id):
        print("Password generated and saved successfully.")
    else:
        print("Failed to generate and save password.")
        return

    # Generate and save wallet keys
    pub_key = input("Enter public key: ")
    priv_key = input("Enter private key: ")

    if save_wallet_keys(user_project_id, pub_key, priv_key):
        print("Wallet keys saved successfully.")
    else:
        print("Failed to save wallet keys.")
        return

    # Update instance IP
    ip_address = input("Enter IP address: ")
    if update_instance_ip(instance_id, ip_address):
        print("Instance IP updated successfully.")
    else:
        print("Failed to update instance IP.")

    print("Project setup completed successfully.")


if __name__ == "__main__":
    data = fetch_user_projects(1)
    print(data)
