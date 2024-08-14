import sqlite3

import exceptions

from settings import DB_HASH_KEY
from settings import DB_FILE_NAME

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class CryptoHasher:
    def __init__(self):
        self.key = DB_HASH_KEY.encode()

    def encrypt(self, text):
        # Create an AES cipher object with the key and AES.MODE_ECB mode
        cipher = AES.new(self.key, AES.MODE_ECB)
        # Pad the plaintext and encrypt it
        ciphertext = cipher.encrypt(pad(text.encode(), AES.block_size))
        return ciphertext
    
    def decrypt(self, ciphertext):
        # Create an AES cipher object with the key and AES.MODE_ECB mode
        cipher = AES.new(self.key, AES.MODE_ECB)
        # Decrypt the ciphertext and remove the padding
        decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted_data.decode()

class DBManager:
    def __init__(self):
        self.db_file_name = DB_FILE_NAME
        self.hasher = CryptoHasher()

        with sqlite3.connect(self.db_file_name) as db:
            cursor = db.cursor()

            query = """
            CREATE TABLE IF NOT EXISTS users(
                chat_id TEXT,
                username TEXT,
                password TEXT
            )
            """

            cursor.executescript(query)

    def register(self, chat_id, account):
        try:
            db = sqlite3.connect(self.db_file_name)
            cursor = db.cursor()

            cursor.execute("SELECT chat_id FROM users WHERE chat_id = ?", [chat_id])
            if cursor.fetchone() is None:
                values = [chat_id, account['username'], self.hasher.encrypt(account['password'])]

                cursor.execute("INSERT INTO users(chat_id, username, password) VALUES(?, ?, ?)", values)
                db.commit()
            else:
                raise exceptions.DatabaseRegisterError
        except sqlite3.Error:
            raise exceptions.SQLiteError
        finally:
            cursor.close()
            db.close()

    def get_account(self, chat_id):
        account = dict()
        try:
            db = sqlite3.connect(self.db_file_name)
            cursor = db.cursor()
    
            cursor.execute("SELECT chat_id FROM users WHERE chat_id = ?", [chat_id])
            if cursor.fetchone() is not None:
                cursor.execute("SELECT username FROM users WHERE chat_id = ?", [chat_id])
                account['username'] = cursor.fetchone()[0]
                cursor.execute("SELECT password FROM users WHERE chat_id = ?", [chat_id])
                account['password'] = self.hasher.decrypt(cursor.fetchone()[0])
        except sqlite3.Error:
            raise exceptions.SQLiteError
        finally:
            cursor.close()
            db.close()
    
            if not account:
                raise exceptions.DatabaseSelectError
            else:
                return account

    def delete(self, chat_id):
        try:
            db = sqlite3.connect(self.db_file_name)
            cursor = db.cursor()

            cursor.execute("DELETE FROM users WHERE chat_id = ?", [chat_id])
            db.commit()
        except sqlite3.Error:
            raise exceptions.SQLiteError
        finally:
            cursor.close()
            db.close()

    def get_total_users(self):
        try:
            db = sqlite3.connect(self.db_file_name)
            cursor = db.cursor()

            cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]
        except sqlite3.Error:
            raise exceptions.SQLiteError
        finally:
            cursor.close()
            db.close()