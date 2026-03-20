"""Account factory functions for creating mint, token, and system accounts."""

from __future__ import annotations

import struct

import solders.pubkey as sp

from .programs import SPL_ASSOCIATED_TOKEN_PROGRAM_ID, SPL_TOKEN_PROGRAM_ID, SYSTEM_PROGRAM_ID
from .result import KeyedAccount


def rent_minimum_balance(data_len: int) -> int:
    """Calculate rent-exempt balance for account data length.

    Matches TypeScript calculation: (data_len + 128) * 3480 * 2
    """
    return (data_len + 128) * 3480 * 2


def create_keyed_system_account(
    address: sp.Pubkey, lamports: int = 1_000_000_000
) -> KeyedAccount:
    """Create a system-owned account.

    Args:
        address: Account address
        lamports: Starting lamports (default: 1 SOL)

    Returns:
        KeyedAccount ready for SVM
    """
    return KeyedAccount(
        address=address,
        owner=SYSTEM_PROGRAM_ID,
        lamports=lamports,
        data=b"",
        executable=False,
    )


def create_keyed_mint_account(
    address: sp.Pubkey,
    mint_authority: sp.Pubkey | None = None,
    decimals: int = 9,
    supply: int = 0,
    freeze_authority: sp.Pubkey | None = None,
    token_program_id: sp.Pubkey = SPL_TOKEN_PROGRAM_ID,
) -> KeyedAccount:
    """Create a pre-initialized SPL Token mint account.

    Uses SPL Token Mint layout (82 bytes):
    - mint_authority: COption<Pubkey> (4 + 32 bytes)
    - supply: u64 (8 bytes)
    - decimals: u8 (1 byte)
    - is_initialized: bool (1 byte)
    - freeze_authority: COption<Pubkey> (4 + 32 bytes)

    Args:
        address: Mint address
        mint_authority: Optional mint authority
        decimals: Token decimals (default: 9)
        supply: Initial supply (default: 0)
        freeze_authority: Optional freeze authority
        token_program_id: SPL Token or Token-2022 program

    Returns:
        KeyedAccount with initialized mint data
    """
    # Encode COption<Pubkey> - 4 byte discriminant + 32 bytes if Some
    def encode_option_pubkey(pubkey: sp.Pubkey | None) -> bytes:
        if pubkey is None:
            return struct.pack("<I", 0) + bytes(32)  # None
        return struct.pack("<I", 1) + bytes(pubkey)  # Some

    data = b"".join(
        [
            encode_option_pubkey(mint_authority),
            struct.pack("<Q", supply),  # u64 supply
            struct.pack("<B", decimals),  # u8 decimals
            struct.pack("<B", 1),  # bool is_initialized = true
            encode_option_pubkey(freeze_authority),
        ]
    )

    return KeyedAccount(
        address=address,
        owner=token_program_id,
        lamports=rent_minimum_balance(len(data)),
        data=data,
        executable=False,
    )


def create_keyed_token_account(
    address: sp.Pubkey,
    mint: sp.Pubkey,
    owner: sp.Pubkey,
    amount: int = 0,
    token_program_id: sp.Pubkey = SPL_TOKEN_PROGRAM_ID,
) -> KeyedAccount:
    """Create a pre-initialized SPL Token account.

    Uses SPL Token Account layout (165 bytes):
    - mint: Pubkey (32 bytes)
    - owner: Pubkey (32 bytes)
    - amount: u64 (8 bytes)
    - delegate: COption<Pubkey> (4 + 32 bytes)
    - state: u8 (1 byte) - 0=Uninitialized, 1=Initialized, 2=Frozen
    - is_native: COption<u64> (4 + 8 bytes)
    - delegated_amount: u64 (8 bytes)
    - close_authority: COption<Pubkey> (4 + 32 bytes)

    Args:
        address: Token account address
        mint: Mint address
        owner: Token account owner
        amount: Initial token balance (default: 0)
        token_program_id: SPL Token or Token-2022 program

    Returns:
        KeyedAccount with initialized token account data
    """
    # Encode COption<Pubkey>
    def encode_option_pubkey(pubkey: sp.Pubkey | None) -> bytes:
        if pubkey is None:
            return struct.pack("<I", 0) + bytes(32)
        return struct.pack("<I", 1) + bytes(pubkey)

    # Encode COption<u64>
    def encode_option_u64(value: int | None) -> bytes:
        if value is None:
            return struct.pack("<I", 0) + struct.pack("<Q", 0)
        return struct.pack("<I", 1) + struct.pack("<Q", value)

    data = b"".join(
        [
            bytes(mint),  # Pubkey mint
            bytes(owner),  # Pubkey owner
            struct.pack("<Q", amount),  # u64 amount
            encode_option_pubkey(None),  # COption<Pubkey> delegate (None)
            struct.pack("<B", 1),  # u8 state = Initialized
            encode_option_u64(None),  # COption<u64> is_native (None)
            struct.pack("<Q", 0),  # u64 delegated_amount
            encode_option_pubkey(None),  # COption<Pubkey> close_authority (None)
        ]
    )

    return KeyedAccount(
        address=address,
        owner=token_program_id,
        lamports=rent_minimum_balance(len(data)),
        data=data,
        executable=False,
    )


def create_keyed_associated_token_account(
    owner: sp.Pubkey,
    mint: sp.Pubkey,
    amount: int = 0,
    token_program_id: sp.Pubkey = SPL_TOKEN_PROGRAM_ID,
) -> KeyedAccount:
    """Create a pre-initialized associated token account.

    Derives the ATA address automatically using PDA.

    Args:
        owner: Wallet owner
        mint: Mint address
        amount: Initial token balance (default: 0)
        token_program_id: SPL Token or Token-2022 program

    Returns:
        KeyedAccount with derived ATA address
    """
    # Derive ATA address
    ata_address, _ = sp.Pubkey.find_program_address(
        [
            bytes(owner),
            bytes(token_program_id),
            bytes(mint),
        ],
        SPL_ASSOCIATED_TOKEN_PROGRAM_ID,
    )

    return create_keyed_token_account(
        address=ata_address, mint=mint, owner=owner, amount=amount, token_program_id=token_program_id
    )
