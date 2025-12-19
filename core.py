import hashlib, base64, secrets, string, random
from config import ASSIGN_FILE, STATE_FILE, IS_PROD
from pathlib import Path


SEPARATOR = " → "

# --- crypto ---

def generate_private_key():
    letters = string.ascii_uppercase
    digits = string.digits
    return (
        secrets.choice(letters) +
        secrets.choice(letters) +
        ''.join(secrets.choice(digits) for _ in range(3))
    )

def derive_key(code: str) -> bytes:
    return hashlib.sha256(code.encode()).digest()

def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def encrypt(text: str, code: str) -> str:
    return base64.b64encode(xor_bytes(text.encode(), derive_key(code))).decode()

def decrypt(cipher: str, code: str):
    try:
        pt = xor_bytes(base64.b64decode(cipher), derive_key(code)).decode()
        return pt if SEPARATOR in pt else None
    except Exception as e:
        # print(e)
        return None

# --- state ---

def is_initialized():
    return (
        STATE_FILE.exists() and STATE_FILE.read_text().strip() == "INITIALIZED"
    ) or (
        (Path("data") / "state.log").exists() and (Path("data") / "state.log").read_text().strip() == "INITIALIZED"
    )

def mark_initialized():
    STATE_FILE.write_text("INITIALIZED")
    if IS_PROD:
        (Path("data") / "state.log").write_text("INITIALIZED")

# --- business ---

def load_employees(path: str):
    employees = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            name, email = line.strip().split("|")
            employees.append((name, email))
    return employees

def generate_assignments(employees):
    if len(employees) < 2:
        raise ValueError("Au moins 2 employés requis.")

    shuffled = employees[:]
    random.shuffle(shuffled)

    return list(zip(employees, shuffled[1:] + shuffled[:1]))

def build_assignments(employees):
    if is_initialized():
        raise RuntimeError("Déjà initialisé")

    used_keys = set()
    out = []
    keys = []

    assignments = generate_assignments(employees)

    for (giver, email), (receiver, _) in assignments:
        while True:
            key = generate_private_key()
            if key not in used_keys:
                used_keys.add(key)
                break

        out.append(encrypt(f"{giver}{SEPARATOR}{receiver}", key))
        keys.append((giver, email, key))

    ASSIGN_FILE.write_text("\n".join(out))
    if IS_PROD:
        (Path("data") / "assignments.enc").write_text("\n".join(out))
    mark_initialized()

    return keys

def resolve_assignment(key: str):
    if not is_initialized():
        return None

    rows = []
    if not IS_PROD and ASSIGN_FILE.exists():
        rows = ASSIGN_FILE.read_text().splitlines()
    elif IS_PROD:
        rows = (Path("data") / "assignments.enc").read_text().splitlines()

    for row in rows:
        res = decrypt(row, key)
        if res:
            return res
    return None
