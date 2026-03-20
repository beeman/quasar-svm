"""Adapters for converting between solders types and internal wire format."""

from __future__ import annotations

from typing import TYPE_CHECKING

import solders.instruction as si
import solders.pubkey as sp

from . import _wire

if TYPE_CHECKING:
    from .result import KeyedAccount


def solders_pubkey_to_bytes(pubkey: sp.Pubkey) -> bytes:
    """Convert solders Pubkey to 32-byte array."""
    return bytes(pubkey)


def bytes_to_solders_pubkey(data: bytes) -> sp.Pubkey:
    """Convert 32-byte array to solders Pubkey."""
    return sp.Pubkey(data)


def solders_account_meta_to_wire(meta: si.AccountMeta) -> _wire.AccountMeta:
    """Convert solders AccountMeta to internal wire format."""
    return _wire.AccountMeta(
        pubkey=bytes(meta.pubkey),
        is_signer=meta.is_signer,
        is_writable=meta.is_writable,
    )


def solders_instruction_to_wire(ix: si.Instruction) -> _wire.Instruction:
    """Convert solders Instruction to internal wire format."""
    accounts = [solders_account_meta_to_wire(meta) for meta in ix.accounts]
    return _wire.Instruction(
        program_id=bytes(ix.program_id),
        data=bytes(ix.data) if ix.data else b"",
        accounts=accounts,
    )


def keyed_account_to_wire(acct: KeyedAccount) -> _wire.Account:
    """Convert KeyedAccount to wire Account for serialization."""
    return _wire.Account(
        pubkey=bytes(acct.address),
        owner=bytes(acct.owner),
        lamports=acct.lamports,
        data=acct.data,
        executable=acct.executable,
    )


def wire_account_to_keyed(acct: _wire.ResultAccount) -> KeyedAccount:
    """Convert wire ResultAccount to KeyedAccount."""
    from .result import KeyedAccount

    return KeyedAccount(
        address=bytes_to_solders_pubkey(acct.pubkey),
        owner=bytes_to_solders_pubkey(acct.owner),
        lamports=acct.lamports,
        data=acct.data,
        executable=acct.executable,
    )
