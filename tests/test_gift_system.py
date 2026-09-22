from __future__ import annotations

import os
import tempfile
from pathlib import Path
import pytest

from gift_system.core.crypto import (
    decrypt_message,
    encrypt_message,
    generate_private_key,
    generate_thread_key,
    hash_key,
    normalize_key,
)
from gift_system.core.matching import generate_cycle_derangement, partition_and_match
from gift_system.services.chat_service import (
    ChatAccessError,
    get_thread_messages,
    post_thread_message,
)
from gift_system.services.santa_service import (
    build_and_save_assignments,
    get_session_by_key,
    resolve_worker_name,
)
from gift_system.storage.database import get_db_connection, init_db
from gift_system.storage.repository import GiftRepository


def test_crypto_key_and_hashing():
    k1 = generate_private_key()
    k2 = generate_private_key()
    assert len(k1) == 5
    assert k1 != k2

    h1 = hash_key(k1, salt="test-salt")
    h2 = hash_key(k1.lower(), salt="test-salt")
    assert h1 == h2
    assert len(h1) == 64


def test_crypto_fernet_encryption():
    t_key = generate_thread_key()
    secret_text = "Coucou secret Père Noël 🎁"

    cipher = encrypt_message(secret_text, t_key)
    assert cipher != secret_text

    plain = decrypt_message(cipher, t_key)
    assert plain == secret_text

    # Invalid thread key returns None
    other_key = generate_thread_key()
    assert decrypt_message(cipher, other_key) is None
    assert decrypt_message("corrupted_base64_data", t_key) is None


def test_matching_derangement():
    items = ["Alice", "Bob", "Charlie", "David", "Emma"]
    matches = generate_cycle_derangement(items)

    assert len(matches) == len(items)
    givers = [g for g, r in matches]
    receivers = [r for g, r in matches]

    assert set(givers) == set(items)
    assert set(receivers) == set(items)
    for g, r in matches:
        assert g != r


def test_partition_and_match_pools():
    employees = [
        ("Alice", "alice@example.com", "active", "public"),
        ("Bob", "bob@example.com", "active", "public"),
        ("Charlie", "charlie@example.com", "active", "public"),
        ("Diana", "diana@example.com", "active", "private"),
        ("Edward", "edward@example.com", "active", "private"),
        ("Frank", "frank@example.com", "inactive", "public"),  # Should be excluded
    ]

    assignments = partition_and_match(employees)
    assert len(assignments) == 5  # 3 public + 2 private

    for giver, receiver in assignments:
        assert giver[1] != receiver[1]
        assert giver[3] == receiver[3]  # Public gives to public, private to private


def test_full_letterbox_and_chat_flow(monkeypatch, tmp_path):
    # Use temporary sqlite db
    db_path = tmp_path / "test_gift.db"
    monkeypatch.setattr("gift_system.config.DB_FILE", db_path)
    monkeypatch.setattr("gift_system.storage.database.DB_FILE", db_path)
    monkeypatch.setattr("gift_system.services.santa_service.DB_FILE", db_path)

    # Create dummy employees file
    emp_file = tmp_path / "employees.txt"
    emp_file.write_text(
        "Alice|alice@test.com|active|public\n"
        "Bob|bob@test.com|active|public\n"
        "Charlie|charlie@test.com|active|public\n",
        encoding="utf-8",
    )

    # Build assignments
    keys = build_and_save_assignments(emp_file, send_emails=False, force_reset=True)
    assert len(keys) == 3

    keys_by_email = {mail: (name, k, rec) for name, mail, k, rec in keys}

    # Pick Alice
    alice_name, alice_key, alice_target = keys_by_email["alice@test.com"]

    # Alice resolves worker name (legacy compatibility)
    assert resolve_worker_name(alice_key) == alice_target

    # Alice logs into session
    alice_session = get_session_by_key(alice_key)
    assert alice_session is not None
    assert alice_session.participant_name == "Alice"
    assert alice_session.santa_mission.target_name == alice_target

    # Alice writes as Santa to her Child (alice_target)
    thread_id = alice_session.santa_mission.thread_id
    msg = post_thread_message(thread_id, alice_key, "Bonjour mon enfant secret ! Que souhaites-tu pour Noël ?")
    assert msg.is_mine is True
    assert msg.sender_role == "SANTA"

    # Find who is Alice's target
    target_mail = [mail for mail, (n, k, r) in keys_by_email.items() if n == alice_target][0]
    target_name, target_key, _ = keys_by_email[target_mail]

    # Target (Child) logs in
    target_session = get_session_by_key(target_key)
    assert target_session is not None
    assert target_session.child_mission is not None
    assert target_session.child_mission.thread_id == thread_id

    # Target reads letterbox messages
    child_view_msgs = get_thread_messages(thread_id, target_key)
    assert len(child_view_msgs) == 1
    assert child_view_msgs[0].content == "Bonjour mon enfant secret ! Que souhaites-tu pour Noël ?"
    assert child_view_msgs[0].sender_display == "Père Noël 🎅"
    assert child_view_msgs[0].is_mine is False
    # CRITICAL: Alice's name is NOT in sender_display or anywhere in msg
    assert "Alice" not in child_view_msgs[0].sender_display

    # Target replies to Santa
    reply = post_thread_message(thread_id, target_key, "Merci Père Noël ! Un beau livre d'aventure me ferait plaisir !")
    assert reply.is_mine is True
    assert reply.sender_role == "CHILD"

    # Alice checks her Santa letterbox again
    santa_view_msgs = get_thread_messages(thread_id, alice_key)
    assert len(santa_view_msgs) == 2
    assert santa_view_msgs[0].is_mine is True
    assert santa_view_msgs[1].is_mine is False
    assert santa_view_msgs[1].sender_display == "Votre Enfant 🎁"
    assert "livre d'aventure" in santa_view_msgs[1].content

    # Third-party intruder tries to read this thread
    intruder_mail = [mail for mail in keys_by_email.keys() if mail not in ("alice@test.com", target_mail)][0]
    intruder_name, intruder_key, _ = keys_by_email[intruder_mail]

    with pytest.raises(ChatAccessError):
        get_thread_messages(thread_id, intruder_key)

    with pytest.raises(ChatAccessError):
        post_thread_message(thread_id, intruder_key, "Coucou pirate")
