import bcrypt
import pyodbc
import string
import secrets
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
from typing import List, Dict, Tuple
import logging
import traceback
from datetime import datetime

# Database connection string
load_dotenv()
DB_CONNECTION_STRING = os.getenv('MSSQL_CONNECTION_STRING')
logger = logging.getLogger(__name__)


def register_user(username: str, email: str, password: str) -> Tuple[int or None, str or None]:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    with pyodbc.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("{CALL sp_RegisterUser(?,?,?,?)}",
                               (username, email, hashed_password.decode('utf-8'), salt.decode('utf-8')))
                user_id = cursor.fetchval()
                conn.commit()
                return int(user_id), None
            except pyodbc.ProgrammingError as e:
                error_msg = str(e)
                if "50001" in error_msg:
                    return None, "Username already exists"
                elif "50002" in error_msg:
                    return None, "Email already exists"
                else:
                    return None, f"An unexpected error occurred: {error_msg}"
            except pyodbc.Error as e:
                return None, f"An error occurred during registration: {e}"


def create_user_project(user_id: int, project_id: int, instance_id: int) -> int or None:
    with pyodbc.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cursor:
            try:
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

                # Create an entry in UserKeys
                cursor.execute("""
                INSERT INTO UserKeys (UserKey_UserProjectIdKey)
                VALUES (?)
                """, (user_project_id,))

                conn.commit()
                return user_project_id
            except pyodbc.Error as e:
                print(f"An error occurred creating user project: {e}")
                conn.rollback()
                return None


def save_wallet_keys(user_project_id: int, pub_key: str, priv_key: str) -> bool:
    # Retrieve the stored Fernet key (previously called IV)
    with pyodbc.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT UserKey_IV FROM UserKeys WHERE UserKey_UserProjectIdKey = ?", user_project_id)
            row = cursor.fetchone()
            if not row or row.UserKey_IV is None:
                print("No Fernet key found for this user project")
                return False
            fernet_key = row.UserKey_IV

    # Create Fernet instance directly with the stored key
    fernet = Fernet(fernet_key)

    # Encrypt the wallet keys
    encrypted_pub_key = fernet.encrypt(pub_key.encode())
    encrypted_priv_key = fernet.encrypt(priv_key.encode())

    # Update the UserKeys table with the encrypted wallet keys
    with pyodbc.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                UPDATE UserKeys 
                SET UserKey_EncryptedPubKey = ?, UserKey_EncryptedPrivKey = ?
                WHERE UserKey_UserProjectIdKey = ?
                """, (encrypted_pub_key, encrypted_priv_key, user_project_id))
                conn.commit()
                return True
            except pyodbc.Error as e:
                print(f"An error occurred saving wallet keys: {e}")
                conn.rollback()
                return False


def update_instance_ip(instance_id: int, ip_address: str) -> bool:
    with pyodbc.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                UPDATE UserKeys
                SET UserKey_IPAddress = ?
                FROM UserKeys UK
                INNER JOIN User_Projects UP ON UK.UserKey_UserProjectIdKey = UP.UserProject_IdKey
                WHERE UP.UserProject_InstanceId = ?
                """, (ip_address, instance_id))

                if cursor.rowcount == 0:
                    print(f"No matching record found for instance ID: {instance_id}")
                    return False

                conn.commit()
                return True
            except pyodbc.Error as e:
                print(f"An error occurred updating instance IP: {e}")
                conn.rollback()
                return False


def generate_and_save_password(user_project_id: int) -> str or None:
    # Generate a random 32-character password
    password = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(32))

    # Generate a Fernet key
    fernet_key = Fernet.generate_key()
    fernet = Fernet(fernet_key)
    encrypted_password = fernet.encrypt(password.encode())

    with pyodbc.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                UPDATE UserKeys
                SET UserKey_EncryptedPassword = ?, UserKey_IV = ?
                WHERE UserKey_UserProjectIdKey = ?
                """, (encrypted_password, fernet_key, user_project_id))
                conn.commit()
                print(f"Generated password: {password}")  # In production, handle this securely
                return password
            except pyodbc.Error as e:
                print(f"An error occurred saving encrypted password: {e}")
                conn.rollback()
                return None


def generate_password_and_key() -> tuple:
    # Generate a random 32-character password
    try:
        password = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(32))

        # Generate a Fernet key
        fernet_key = Fernet.generate_key()
        return password, fernet_key
    except Exception as e:
        logger.error(f"Error generating password {e}")
        return None, None


def save_encrypted_password(user_project_id: int, password: str, fernet_key: bytes) -> bool:
    fernet = Fernet(fernet_key)
    encrypted_password = fernet.encrypt(password.encode())

    with pyodbc.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                UPDATE UserKeys
                SET UserKey_EncryptedPassword = ?, UserKey_IV = ?
                WHERE UserKey_UserProjectIdKey = ?
                """, (encrypted_password, fernet_key, user_project_id))
                conn.commit()
                print(f"Generated password: {password}")  # In production, handle this securely
                return True
            except pyodbc.Error as e:
                print(f"An error occurred saving encrypted password: {e}")
                conn.rollback()
                return False


def fetch_pending_instances() -> List[Dict]:
    """
    Fetch all entries from UserKeys where IP address is null and both encrypted public and private keys are set.
    """
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
            return [{"user_project_id": row.UserKey_UserProjectIdKey, "instance_id": row.UserProject_InstanceId}
                    for row in cursor.fetchall()]


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

    except Exception as e:
        print(f"Decryption error: {type(e).__name__}: {str(e)}")
        print(f"Encrypted data type: {type(encrypted_data)}")
        print(f"Encrypted data length: {len(encrypted_data)}")
        print(f"Encrypted data (first 50 bytes): {encrypted_data[:50]}")
        print(f"Fernet key type: {type(fernet_key)}")
        print(f"Fernet key length: {len(fernet_key)}")
        print(f"Fernet key: {fernet_key}")
        return None


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
                    raise ValueError(f"No data found for user_project_idkey: {user_project_id}")

                ip_address, encrypted_pub_key, encrypted_priv_key, encrypted_password, fernet_key, project_name = row

                pub_key = decrypt_data(encrypted_pub_key, fernet_key)
                priv_key = decrypt_data(encrypted_priv_key, fernet_key)
                password = decrypt_data(encrypted_password, fernet_key)

                if not all([pub_key, priv_key, password]):
                    raise ValueError("One or more decryption operations failed")

                return {
                    'ip': ip_address,
                    'wallet': pub_key,
                    'priv_key': priv_key,
                    'password': password,
                    'project_name': project_name
                }

    except Exception as e:
        print(f"Error in fetch_vps_data: {str(e)}")
        print(traceback.format_exc())
        raise


def verify_email(email: str) -> bool:
    with pyodbc.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cursor:
            try:
                result = cursor.execute("{CALL sp_VerifyEmail(?, ?)}", (email, 0)).fetchone()[0]
                conn.commit()
                return result == 0
            except pyodbc.Error as e:
                print(f"An error occurred during email verification: {e}")
                return False


def initiate_password_reset(email: str, reset_token: str, expiration_time: datetime) -> bool:
    with pyodbc.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cursor:
            try:
                result = cursor.execute("{CALL sp_InitiatePasswordReset(?, ?, ?, ?)}",
                                        (email, reset_token, expiration_time, 0)).fetchone()[0]
                conn.commit()
                return result == 0
            except pyodbc.Error as e:
                print(f"An error occurred initiating password reset: {e}")
                return False


def complete_password_reset(reset_token: str, new_password: str) -> bool:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)

    with pyodbc.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cursor:
            try:
                result = cursor.execute("{CALL sp_CompletePasswordReset(?, ?, ?, ?)}",
                                        (reset_token, hashed_password.decode('utf-8'),
                                         salt.decode('utf-8'), 0)).fetchone()[0]
                conn.commit()
                return result == 0
            except pyodbc.Error as e:
                print(f"An error occurred completing password reset: {e}")
                return False


def login_user(email: str, password: str) -> Tuple[int or None, str or None]:
    with pyodbc.connect(DB_CONNECTION_STRING) as conn:
        with conn.cursor() as cursor:
            try:
                result = cursor.execute("{CALL sp_UserLogin(?, ?)}",
                                        (email, pyodbc.SQL_PARAM_OUTPUT))
                row = result.fetchone()
                login_result = row[1]  # Assuming the output parameter is the second column

                if login_result == -1:
                    return None, "User not found"
                elif login_result == -2:
                    return None, "Email not verified"
                elif login_result == -3:
                    return None, "Account is locked, contact support"
                elif login_result == 0:
                    user_id, stored_hash = row.User_IdKey, row.User_PasswordHash
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                        # Reset failed login attempts on successful login
                        cursor.execute("{CALL sp_UpdateFailedLoginAttempts(?, 0)}", (user_id,))
                        conn.commit()
                        return user_id, None
                    else:
                        # Increment failed login attempts
                        cursor.execute("{CALL sp_UpdateFailedLoginAttempts(?, 1)}", (user_id,))
                        conn.commit()
                        return None, "Invalid password"
                else:
                    return None, "Unknown error occurred"
            except pyodbc.Error as e:
                return None, f"An error occurred during login: {e}"


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
    instance_id = int(input("Enter instance ID: "))

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
    data = fetch_vps_data(20)
    print(data)
