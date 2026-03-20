"""Program ID constants and ELF loading utilities."""

from __future__ import annotations

from pathlib import Path

import solders.pubkey as sp

# Standard program IDs
SPL_TOKEN_PROGRAM_ID = sp.Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
SPL_TOKEN_2022_PROGRAM_ID = sp.Pubkey.from_string(
    "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
)
SPL_ASSOCIATED_TOKEN_PROGRAM_ID = sp.Pubkey.from_string(
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
)
SYSTEM_PROGRAM_ID = sp.Pubkey.from_string("11111111111111111111111111111111")

# Loader versions
LOADER_V2 = 2
LOADER_V3 = 3

# Constants
LAMPORTS_PER_SOL = 1_000_000_000


def _programs_dir() -> Path:
    """Get programs directory (contains .so files)."""
    # programs/ is at workspace root, 4 levels up from this file
    return Path(__file__).resolve().parent.parent.parent.parent / "programs"


def load_elf(name: str) -> bytes:
    """Load ELF binary from programs directory.

    Args:
        name: Program binary name (e.g., "spl_token.so")

    Returns:
        ELF binary data

    Raises:
        FileNotFoundError: If program binary not found
    """
    path = _programs_dir() / name
    if not path.exists():
        raise FileNotFoundError(f"Program binary not found: {path}")
    return path.read_bytes()


def load_spl_token() -> bytes:
    """Load SPL Token program binary."""
    return load_elf("spl_token.so")


def load_spl_token_2022() -> bytes:
    """Load SPL Token-2022 program binary."""
    return load_elf("spl_token_2022.so")


def load_spl_associated_token() -> bytes:
    """Load SPL Associated Token program binary."""
    return load_elf("spl_associated_token.so")
