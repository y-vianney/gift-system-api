from __future__ import annotations

import random
from typing import Sequence, TypeVar

T = TypeVar("T")


def generate_cycle_derangement(items: Sequence[T]) -> list[tuple[T, T]]:
    """
    Generate a guaranteed derangement (no self-assignments) for a list of items
    using a randomized cyclic permutation in O(N).
    """
    if len(items) < 2:
        raise ValueError("Au moins 2 participants sont requis pour un groupe.")

    shuffled = list(items)
    random.shuffle(shuffled)

    n = len(shuffled)
    return [(shuffled[i], shuffled[(i + 1) % n]) for i in range(n)]


def partition_and_match(
    employees: list[tuple[str, str, str, str]]
) -> list[tuple[tuple[str, str, str, str], tuple[str, str, str, str]]]:
    """
    Partition active employees by visibility ('public' and 'private') and generate
    Secret Santa assignments without self-assignments.
    """
    active = [e for e in employees if e[2].strip().lower() == "active"]
    if len(active) < 2:
        raise ValueError("Au moins 2 employés actifs sont requis.")

    public_pool = [e for e in active if e[3].strip().lower() == "public"]
    private_pool = [e for e in active if e[3].strip().lower() == "private"]

    if public_pool and len(public_pool) < 2:
        raise ValueError("Le groupe 'public' doit contenir au moins 2 employés.")
    if private_pool and len(private_pool) < 2:
        raise ValueError("Le groupe 'private' doit contenir au moins 2 employés.")

    assignments: list[tuple[tuple[str, str, str, str], tuple[str, str, str, str]]] = []
    if public_pool:
        assignments.extend(generate_cycle_derangement(public_pool))
    if private_pool:
        assignments.extend(generate_cycle_derangement(private_pool))

    # Double check that no giver is their own receiver
    for giver, receiver in assignments:
        if giver[1].strip() == receiver[1].strip():
            raise RuntimeError(f"Erreur d'attribution: auto-assignation détectée pour {giver[0]}")

    return assignments
