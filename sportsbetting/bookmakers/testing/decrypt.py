import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

import json


def b64fix(s: str) -> str:
    s = s.strip().strip('"').strip("'")     # remove quotes/whitespace if present
    return s + '=' * (-len(s) % 4)          # add missing padding

def decrypt_oddsportal_token(e_b64: str, sCt: str, aCt: str) -> str:
    # 1) atob(e) -> "<cipher_b64>:<iv_hex>"
    payload = base64.urlsafe_b64decode(b64fix(e_b64)).decode("ascii")
    cipher_b64, iv_hex = payload.split(":", 1)

    # 2) parse ciphertext and IV
    ct = base64.urlsafe_b64decode(b64fix(cipher_b64))   # bytes
    iv = bytes.fromhex(iv_hex)                          # 16 bytes

    # 3) PBKDF2-HMAC-SHA256 (1000 iters) -> 32-byte key
    kdf = PBKDF2HMAC(
        algorithm=SHA256(),
        length=32,
        salt=aCt.encode("utf-8"),   # JS uses TextEncoder on the salt string
        iterations=1000,
        backend=default_backend()
    )
    key = kdf.derive(sCt.encode("utf-8"))               # password is the sCt string

    # 4) AES-CBC decrypt (+ PKCS7 unpad)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    dec = cipher.decryptor()
    pt = dec.update(ct) + dec.finalize()

    # PKCS#7 unpad (needed for CBC)
    unpad = padding.PKCS7(128).unpadder()
    pt = unpad.update(pt) + unpad.finalize()

    return pt.decode("utf-8", "replace")

e_b64 = "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"
sCt  = "J*8sQ!p$7aD_fR2yW@gHn*3bVp#sAdLd_k"
aCt  = "5b9a8f2c3e6d1a4b7c8e9d0f1a2b3c4d"

plaintext = decrypt_oddsportal_token(e_b64, sCt=sCt, aCt=aCt)
#print(plaintext)

data = json.loads(plaintext)
print(data)
print("EOL")

with open("output.json", "w") as f:
    json.dump(data, f, indent=2)
