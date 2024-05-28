from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
import logger
import bcrypt
import json
import time
import os


# This script is a library for cryptography functions and secure storage.


# File paths
password_path = "/app/keys/password.pem"
api_key_path = "/app/keys/api_key.pem"
api_secret_path = "/app/keys/api_secret.pem"

# Variable that contains the unique ID


class Cryptography:
    def __init__(self):
        # Create private key
        self.__private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        # Create public key
        public_key = self.__private_key.public_key()
        self.public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Get the stored password
        with open(password_path, "r") as file:
            self.__password = file.read()
            
        # Set a variable to store/compare timestamps later
        self.last_password_change = 0
        
    def hash_password(self, password: str):
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")
            
    # Function to verify whether a password is correct
    def verify_password(self, password: str):
        # Check whether the password is correct
        try:
            if password and self.__password:
                return bcrypt.checkpw(password.encode("utf-8"), self.__password.encode("utf-8"))
            return False
        except:
            return False
        
    # Function to create a password
    def create_password(self, password: str):
        # Get current time
        timestamp = time.time()
        
        # Check whether the password hasn't been changed too recently
        if self.last_password_change - 1800 < timestamp: # 1800 (seconds) is 30 minutes
            # Update the timestamp value
            self.last_password_change = timestamp
            
            # Clear the API data
            with open(api_key_path, "w") as file:
                file.write("")
            with open(api_secret_path, "w") as file:
                file.write("")
                
            password = self.hash_password(password)
            
            # Update the password variable
            self.__password = password
            
            # Write the password to the file
            with open(password_path, "w") as file:
                file.write(password)
                
            logger.log("Client created a password")
            
            return True
        else:
            logger.log("Client attempted to create a new password during timeout", "warning")
            
    # Function to update the user's password     
    def update_password(self, password: str, new_password: str):
        # Verify the password
        if self.verify_password(password):
            # Get the current API data
            api_key = self.pem_decrypt(api_key_path)
            api_secret = self.pem_decrypt(api_secret_path)
                
            # Update the password variable
            self.__password = new_password
            
            # Update the API data with the new password
            self.pem_encrypt(api_key, api_key_path)
            self.pem_encrypt(api_secret, api_key_path)
            
            logger.log("Client updated password")
            
            return True
        else:
            logger.log("Client tried to update password, but received invalid password", "warning")
    
    # Function to decrypt JSON data
    def decrypt_data(self, encrypted_body):
        bytes_body = base64.b64decode(encrypted_body)

        try:
            body = self.__private_key.decrypt(
                bytes_body,
                padding.PKCS1v15()
            )
        except Exception:
            logger.log("Received incorrectly encrypted data from client")
            return "Invalid encryption", 400
        
        return json.loads(body.decode('utf-8'))
    
    # Function to encrypt data to files
    def pem_encrypt(self, data: any, file_path: str):
        # Generate random salt
        salt = os.urandom(16)
        # Get a key using Scrypt
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2**14,
            r=8,
            p=1,
            backend=default_backend()
        )
        key = kdf.derive(self.__password.encode())
        
        # Ensure data is in bytes
        if not isinstance(data, bytes):
            data = data.encode("utf-8")
            
        # Encrypt the data
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(data) + encryptor.finalize()
        
        # Store all info on top of eachother as a string
        data_to_store = salt + iv + encrypted_data
        # Convert bytes to string
        data_to_store = base64.b64encode(data_to_store).decode("ascii")
        
        # Write the data to the file
        with open(file_path, "w") as file:
            file.write(data_to_store)

    # Function to decrypt data from files
    def pem_decrypt(self, file_path: str):
        # Get the data from the file
        with open(file_path, "r") as file:
            encrypted_data = file.read()
            
        # Convert string to bytes
        encrypted_data = base64.b64decode(encrypted_data)
        
        # Extract the data
        salt = encrypted_data[:16]
        iv = encrypted_data[16:32]
        ciphertext = encrypted_data[32:]
        
        # Get the key using Scrypt
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2**14,
            r=8,
            p=1,
            backend=default_backend()
        )
        key = kdf.derive(self.__password.encode("utf-8"))
        
        # Decrypt the data with AES
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        data = decryptor.update(ciphertext) + decryptor.finalize()
        
        return data.decode("utf-8")
        
        