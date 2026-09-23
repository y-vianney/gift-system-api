from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
    except Exception:
        pass

from .core.crypto import normalize_key
from .services.chat_service import get_thread_messages, post_thread_message
from .services.santa_service import (
    build_and_save_assignments,
    get_session_by_key,
    is_system_initialized
)
from .storage.database import get_db_connection, init_db


def run_build(file_path: str, send_emails: bool = False, log_keys: bool = False, force: bool = False) -> None:
    try:
        start = time.time()
        path = Path(file_path)
        if not path.exists():
            print(f"Erreur : Le fichier {file_path} est introuvable.")
            return

        print(f"<> Génération des assignations à partir de {file_path}...")
        keys = build_and_save_assignments(path, send_emails=send_emails, log_keys=log_keys, force_reset=force)

        # Write keys log for administrator reference
        if log_keys:
            with open("keys_log.log", "w", encoding="utf-8") as handle:
                for giver, mail, key, receiver in keys:
                    handle.write(f"{giver} | {mail} | {key} | {receiver}\n")
                print(f"# Journal des clés enregistré dans 'keys_log.log'.")

        elapsed = time.time() - start
        print(f"<--> Assignations générées avec succès ({len(keys)} participants).")
        print(f"... Temps écoulé : {round(elapsed, 2)} secondes.")
    except RuntimeError as exc:
        print(f"!! {exc}")
        print("Utilisez --force pour réinitialiser complètement les assignations.")
    except Exception as exc:
        print(f"#!! Erreur inattendue : {exc}")


def run_view() -> None:
    raw_key = input("Clé privée : ").strip()
    key = normalize_key(raw_key)
    session = get_session_by_key(key)
    if session and session.santa_mission:
        print(f"\n** Bienvenue {session.participant_name} !")
        print(f"#* Vous êtes le Père Noël de : {session.santa_mission.target_name}")
        print(";) Gardez ce nom strictement secret !")
    else:
        print("<!> Clé invalide ou aucune assignation trouvée.")


def run_chat() -> None:
    raw_key = input("Clé privée : ").strip()
    key = normalize_key(raw_key)
    session = get_session_by_key(key)
    if not session:
        print("<!> Clé invalide.")
        return

    print(f"\n>> Boîte aux lettres secrète de {session.participant_name}")
    print("1. Messages avec votre Enfant (à qui vous offrez)")
    print("2. Messages avec votre Père Noël Mystère")
    choice = input("Votre choix (1 ou 2) : ").strip()

    thread_id = None
    role_label = ""
    if choice == "1" and session.santa_mission:
        thread_id = session.santa_mission.thread_id
        role_label = f"votre Enfant ({session.santa_mission.target_name})"
    elif choice == "2" and session.child_mission:
        thread_id = session.child_mission.thread_id
        role_label = "votre Père Noël Mystère :o"
    else:
        print("Choix invalide.")
        return

    messages = get_thread_messages(thread_id, key)
    print(f"\n--- Historique avec {role_label} ---")
    if not messages:
        print("(Aucun message pour le moment)")
    for msg in messages:
        sender = "Vous" if msg.is_mine else msg.sender_display
        print(f"[{msg.created_at[:16]}] {sender}: {msg.content}")

    print("\nÉcrire un message (laisser vide pour quitter) :")
    text = input(">> ").strip()
    if text:
        post_thread_message(thread_id, key, text)
        print("<> Message envoyé avec succès !")


def run_status() -> None:
    init_db()
    initialized = is_system_initialized()
    print(f"Statut système : {'INITIALISÉ' if initialized else 'NON INITIALISÉ'}")
    if initialized:
        with get_db_connection() as conn:
            p_count = conn.execute("SELECT COUNT(*) FROM participants").fetchone()[0]
            a_count = conn.execute("SELECT COUNT(*) FROM assignments").fetchone()[0]
            m_count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            print(f"Participants enregistrés : {p_count}")
            print(f"Assignations actives    : {a_count}")
            print(f"Messages échangés        : {m_count}")


def run_serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    import uvicorn
    print(f"###> Démarrage du serveur Gift System sur http://{host}:{port}")
    uvicorn.run("gift_system.api:app", host=host, port=port, reload=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Gift System CLI - Secret Santa Management")
    subparsers = parser.add_subparsers(dest="command")

    # build
    build_parser = subparsers.add_parser("build", help="Générer les assignations à partir d'un fichier")
    build_parser.add_argument("file", help="Chemin vers le fichier des employés (ex: data/employees.txt)")
    build_parser.add_argument("--send-emails", action="store_true", help="Envoyer les emails de notification")
    build_parser.add_argument("--force", action="store_true", help="Forcer la réinitialisation si déjà initialisé")
    build_parser.add_argument("--log-keys", action="store_true", help="Afficher les clés dans la console")

    # view
    subparsers.add_parser("view", help="Consulter son attribution avec sa clé privée")

    # chat
    subparsers.add_parser("chat", help="Consulter ou envoyer des messages anonymes")

    # status
    subparsers.add_parser("status", help="Afficher l'état du système")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Démarrer l'API FastAPI et l'interface Web")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Hôte d'écoute (défaut: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port d'écoute (défaut: 8000)")

    args = parser.parse_args()

    if args.command == "build":
        run_build(args.file, send_emails=args.send_emails, log_keys=args.log_keys, force=args.force)
        return 0
    elif args.command == "view":
        run_view()
        return 0
    elif args.command == "chat":
        run_chat()
        return 0
    elif args.command == "status":
        run_status()
        return 0
    elif args.command == "serve":
        run_serve(host=args.host, port=args.port)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
