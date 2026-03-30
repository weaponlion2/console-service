import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Hash import SHA1

# --- Constants ---
passPhrase = "D4i5w6e7s8H9"
saltValue = "ZEDON"
passwordIterations = 2
initVector = "@1B2c3D4e5F6g7H8"
keySize = 32 

def derive_key(passphrase, salt, iterations, key_size):
    password = passphrase.encode('utf-8')
    salt = salt.encode('ascii')

    hash_obj = SHA1.new(password + salt)
    result = hash_obj.digest()

    for _ in range(1, iterations):
        hash_obj = SHA1.new(result)
        result = hash_obj.digest()

    key = result
    while len(key) < key_size:
        hash_obj = SHA1.new(key)
        key += hash_obj.digest()

    return key[:key_size]

# --- Encrypt ---
def encrypt(plain_text):
    key = derive_key(passPhrase, saltValue, passwordIterations, keySize)
    iv = initVector.encode('ascii')

    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(plain_text.encode('utf-8'), AES.block_size))

    return base64.b64encode(encrypted).decode()

# --- Decrypt ---
def decrypt(cipher_text):
    key = derive_key(passPhrase, saltValue, passwordIterations, keySize)
    iv = initVector.encode('ascii')

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(base64.b64decode(cipher_text))

    return unpad(decrypted, AES.block_size).decode('utf-8')
