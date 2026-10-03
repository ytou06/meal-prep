#!/usr/bin/env python3
"""Chiffrement des plans mensuels de l'appli Meal prep.

Les fichiers data/AAAA-MM.json publiés sont chiffrés (AES-256-GCM, clé dérivée
du mot de passe par PBKDF2-SHA256). Le mot de passe n'est jamais écrit dans le
dépôt : il est lu dans la variable d'environnement MP_PASSWORD.

  python3 tools/crypt.py init                       # une seule fois : sel + contrôle dans data/index.json
  python3 tools/crypt.py encrypt plan.json data/2026-11.json
  python3 tools/crypt.py decrypt data/2026-10.json [sortie.json]
  python3 tools/crypt.py check                      # vérifie que chaque mois se déchiffre

Ne jamais committer de plan en clair (voir .gitignore).
"""
import base64, json, os, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "data", "index.json")
ITER = 600000
CHECK_TEXT = b"meal-prep-ok"

b64e = lambda b: base64.b64encode(b).decode()
b64d = lambda s: base64.b64decode(s)

def password():
    pw = os.environ.get("MP_PASSWORD")
    if not pw:
        sys.exit("MP_PASSWORD manquant")
    return pw.encode()

def load_index():
    with open(INDEX, encoding="utf-8") as f:
        return json.load(f)

def save_index(idx):
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
        f.write("\n")

def key_for(idx):
    kdf = idx["kdf"]
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b64d(kdf["salt"]), iterations=kdf["iter"]).derive(password())

def seal(key, data: bytes):
    iv = os.urandom(12)
    return {"v": 1, "iv": b64e(iv), "ct": b64e(AESGCM(key).encrypt(iv, data, None))}

def open_(key, blob):
    return AESGCM(key).decrypt(b64d(blob["iv"]), b64d(blob["ct"]), None)

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "init":
        idx = load_index() if os.path.exists(INDEX) else {"months": []}
        idx["kdf"] = {"alg": "PBKDF2-SHA256", "iter": ITER, "salt": b64e(os.urandom(16))}
        idx["check"] = seal(key_for(idx), CHECK_TEXT)
        save_index(idx); print("index initialisé")
    elif cmd == "encrypt":
        src, dst = sys.argv[2], sys.argv[3]
        idx = load_index(); key = key_for(idx)
        if open_(key, idx["check"]) != CHECK_TEXT:
            sys.exit("mot de passe incorrect")
        with open(src, encoding="utf-8") as f:
            plan = json.load(f)  # valide le JSON
        with open(dst, "w") as f:
            json.dump(seal(key, json.dumps(plan, ensure_ascii=False, separators=(",", ":")).encode()), f)
        print("chiffré :", dst)
    elif cmd == "decrypt":
        src = sys.argv[2]
        idx = load_index(); key = key_for(idx)
        with open(src) as f:
            txt = open_(key, json.load(f)).decode()
        if len(sys.argv) > 3:
            with open(sys.argv[3], "w", encoding="utf-8") as f:
                f.write(json.dumps(json.loads(txt), ensure_ascii=False, indent=1))
        else:
            print(txt)
    elif cmd == "check":
        idx = load_index(); key = key_for(idx)
        assert open_(key, idx["check"]) == CHECK_TEXT, "mot de passe incorrect"
        for k in idx["months"]:
            with open(os.path.join(ROOT, "data", k + ".json")) as f:
                plan = json.loads(open_(key, json.load(f)))
            assert plan["key"] == k and len(plan["sessions"]) == 5, k
            print("ok", k, "-", len(plan["sessions"]), "sessions")
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
