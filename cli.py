from core import load_employees, build_assignments, resolve_assignment
from gs_smtp import send_key_email
# from pathlib import Path
import sys
import time


def run_cli(employees):
    try:
        start = time.time()
        keys = build_assignments(employees)
        for name, mail, key, _ in keys:
            send_key_email(
                smtp_host = "smtp.gmail.com",
                smtp_port = 587,
                name = name,
                email = mail,
                key = key
            )

        # with open("keys_log.log", "w") as f:
        #     for k in keys:
        #         f.write(" - ".join(k) + '\n')
        end = time.time()
        print("Assignations générées.\n")
        print("Temps écoulé:", round(end - start, 2), "secondes.")
    except RuntimeError:
        print("Déjà généré.")

def view_cli():
    key = input("Clé privée : ").strip()
    res = resolve_assignment(key)
    if res:
        print(res)
    else:
        print("Clé invalide.")

def usage():
    print(
        "Usage:\n"
        "  python cli.py build employees.txt\n"
        "  python cli.py view\n"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "build" and len(sys.argv) == 3:
        employees = load_employees(sys.argv[2])
        run_cli(employees)
    elif cmd == "view":
        view_cli()
    else:
        usage()
