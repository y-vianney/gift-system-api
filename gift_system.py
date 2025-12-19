from gs_smtp import send_key_email

from pathlib import Path
import os
import sys
import hashlib
import base64
import secrets
import string
import random


# ================= CONFIG =================
INTERNAL_DIR = Path.home() / ".gs-project_internal"
ASSIGN_FILE = "assignments.enc"
STATE_FILE = "state.log"
ADMIN_FILE = "admin.hash"
MASK = "*****"
DEFAULT_ADMIN_CODE = "ADMIN-RESET"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SEPARATOR = " → "
# ==========================================


def generate_private_key():
    letters = string.ascii_uppercase
    digits = string.digits
    return (
        secrets.choice(letters) +
        secrets.choice(letters) +
        ''.join(secrets.choice(digits) for _ in range(3))
    )


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def derive_key(code: str) -> bytes:
    return hashlib.sha256(code.encode()).digest()


def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encrypt(text: str, code: str) -> str:
    key = derive_key(code)
    ct = xor_bytes(text.encode(), key)
    return base64.b64encode(ct).decode()


def decrypt(cipher: str, code: str) -> str | None:
    try:
        key = derive_key(code)
        pt = xor_bytes(base64.b64decode(cipher), key).decode()
        return pt if SEPARATOR in pt else None
    except Exception:
        return None


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def ensure_internal():
    os.makedirs(INTERNAL_DIR, exist_ok=True)

    admin_path = INTERNAL_DIR / ADMIN_FILE
    if not admin_path.exists():
        admin_path.write_text(sha256(DEFAULT_ADMIN_CODE))

    state_path = INTERNAL_DIR / STATE_FILE
    if not state_path.exists():
        state_path.write_text("EMPTY")


def read_state() -> str:
    return (INTERNAL_DIR / STATE_FILE).read_text().strip()


def write_state(state: str):
    return (INTERNAL_DIR / STATE_FILE).write_text(state)


def check_admin():
    code = input("Code admin requis : ").strip()
    return sha256(code) == (INTERNAL_DIR / ADMIN_FILE).read_text().strip()


def load_employees(path: str):
    employees = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            name, email = line.strip().split("|")
            employees.append((name, email))

    return employees


def generate_assignments(employees):
    givers = employees[:]
    receivers = employees[:]
    while True:
        random.shuffle(receivers)
        if all(g[0] != r[0] for g, r in zip(givers, receivers)):
            break
    return [(g[0], r[0], g[1]) for g, r in zip(givers, receivers)]


def build(employees_file: str):
    ensure_internal()

    if read_state() == "INITIALIZED":
        print("⚠️ Assignation déjà réalisée.")
        if not check_admin():
            print("Accès refusé.")
            return
        print("Réinitialisation autorisée.")

    employees = load_employees(employees_file)
    if len(employees) <= 1:
        print("Besoin d'au moins 2 utilisateurs.")
        sys.exit(1)
    assignments = generate_assignments(employees)

    out_lines = []
    for giver, receiver, giver_mail in assignments:
        private_key = generate_private_key()
        phrase = f"{giver} → {receiver}"
        cipher = encrypt(phrase, private_key)
        out_lines.append(cipher)

        send_key_email(SMTP_HOST, SMTP_PORT, giver_mail, giver, private_key)

    (INTERNAL_DIR / ASSIGN_FILE).write_text("\n".join(out_lines))
    write_state("INITIALIZED")
    print("✅ Assignations générées et chiffrées.")


def view(key: str = None):
    ensure_internal()

    if not key:
        if read_state() != "INITIALIZED":
            print("Aucune assignation disponible.")
            return None

        key = input("Collez votre clé privée : ").strip()
        if key == "":
            print("Code invalide.")
            return None
    else:
        employees_file = os.path.dirname(os.path.abspath(__file__)) / Path("data/employees.txt")
        if read_state() != "INITIALIZED" and employees_file.exists():
            build(employees_file)

    rows = (INTERNAL_DIR / ASSIGN_FILE).read_text().splitlines()

    revealed = None
    for row in rows:
        res = decrypt(row, key)
        if res:
            revealed = res
            break

    if key and revealed:
        return revealed.split(SEPARATOR)[-1]
    else:
        clear_screen()
        print("=== Attribution ===\n")
        for row in rows:
            if revealed and decrypt(row, key) == revealed:
                print(revealed)
            else:
                print(f"{MASK} → {MASK}")

    return None


def usage():
    print(
        "Usage:\n"
        "  python gift_system.py build employees.txt\n"
        "  python gift_system.py view\n"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "build" and len(sys.argv) == 3:
        build(sys.argv[2])
    elif cmd == "view":
        view()
    else:
        usage()
