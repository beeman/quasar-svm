"""Binary wire format serialization/deserialization matching src/wire.rs."""

from __future__ import annotations

import struct
from dataclasses import dataclass


@dataclass
class AccountMeta:
    pubkey: bytes  # 32 bytes
    is_signer: bool
    is_writable: bool


@dataclass
class Instruction:
    program_id: bytes  # 32 bytes
    data: bytes
    accounts: list[AccountMeta]


@dataclass
class Account:
    pubkey: bytes  # 32 bytes
    owner: bytes  # 32 bytes
    lamports: int
    data: bytes
    executable: bool


@dataclass
class ResultAccount:
    pubkey: bytes
    owner: bytes
    lamports: int
    data: bytes
    executable: bool


@dataclass
class TokenBalance:
    account_index: int
    mint: str
    owner: str | None
    decimals: int
    amount: str
    ui_amount: float | None


@dataclass
class ExecutedInstruction:
    stack_depth: int
    instruction: Instruction
    compute_units_consumed: int
    result: int


@dataclass
class ExecutionResult:
    status: int
    compute_units: int
    execution_time_us: int
    return_data: bytes
    accounts: list[ResultAccount]
    logs: list[str]
    error_message: str | None
    pre_balances: list[int]
    post_balances: list[int]
    pre_token_balances: list[TokenBalance]
    post_token_balances: list[TokenBalance]
    execution_trace: list[ExecutedInstruction]


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def serialize_instruction(ix: Instruction) -> bytes:
    parts = [
        ix.program_id,
        struct.pack("<I", len(ix.data)),
        ix.data,
        struct.pack("<I", len(ix.accounts)),
    ]
    for m in ix.accounts:
        parts.append(m.pubkey)
        parts.append(bytes([1 if m.is_signer else 0]))
        parts.append(bytes([1 if m.is_writable else 0]))
    return b"".join(parts)


def serialize_instructions(ixs: list[Instruction]) -> bytes:
    parts = [struct.pack("<I", len(ixs))]
    for ix in ixs:
        parts.append(serialize_instruction(ix))
    return b"".join(parts)


def serialize_accounts(accounts: list[Account]) -> bytes:
    parts = [struct.pack("<I", len(accounts))]
    for a in accounts:
        parts.append(a.pubkey)
        parts.append(a.owner)
        parts.append(struct.pack("<Q", a.lamports))
        parts.append(struct.pack("<I", len(a.data)))
        parts.append(a.data)
        parts.append(bytes([1 if a.executable else 0]))
    return b"".join(parts)


# ---------------------------------------------------------------------------
# Deserialization
# ---------------------------------------------------------------------------


def deserialize_result(data: bytes) -> ExecutionResult:
    o = 0

    (status,) = struct.unpack_from("<i", data, o)
    o += 4
    (compute_units,) = struct.unpack_from("<Q", data, o)
    o += 8
    (execution_time_us,) = struct.unpack_from("<Q", data, o)
    o += 8

    (rd_len,) = struct.unpack_from("<I", data, o)
    o += 4
    return_data = data[o : o + rd_len]
    o += rd_len

    (num_accts,) = struct.unpack_from("<I", data, o)
    o += 4
    accounts: list[ResultAccount] = []
    for _ in range(num_accts):
        pubkey = data[o : o + 32]
        o += 32
        owner = data[o : o + 32]
        o += 32
        (lamports,) = struct.unpack_from("<Q", data, o)
        o += 8
        (d_len,) = struct.unpack_from("<I", data, o)
        o += 4
        acct_data = data[o : o + d_len]
        o += d_len
        executable = data[o] != 0
        o += 1
        accounts.append(ResultAccount(pubkey, owner, lamports, acct_data, executable))

    (num_logs,) = struct.unpack_from("<I", data, o)
    o += 4
    logs: list[str] = []
    for _ in range(num_logs):
        (l_len,) = struct.unpack_from("<I", data, o)
        o += 4
        logs.append(data[o : o + l_len].decode("utf-8"))
        o += l_len

    (em_len,) = struct.unpack_from("<I", data, o)
    o += 4
    error_message = data[o : o + em_len].decode("utf-8") if em_len > 0 else None
    o += em_len

    # Pre-balances
    (num_pre_balances,) = struct.unpack_from("<I", data, o)
    o += 4
    pre_balances: list[int] = []
    for _ in range(num_pre_balances):
        (balance,) = struct.unpack_from("<Q", data, o)
        o += 8
        pre_balances.append(balance)

    # Post-balances
    (num_post_balances,) = struct.unpack_from("<I", data, o)
    o += 4
    post_balances: list[int] = []
    for _ in range(num_post_balances):
        (balance,) = struct.unpack_from("<Q", data, o)
        o += 8
        post_balances.append(balance)

    # Pre-token balances
    (num_pre_token_balances,) = struct.unpack_from("<I", data, o)
    o += 4
    pre_token_balances: list[TokenBalance] = []
    for _ in range(num_pre_token_balances):
        (account_index,) = struct.unpack_from("<I", data, o)
        o += 4
        (mint_len,) = struct.unpack_from("<I", data, o)
        o += 4
        mint = data[o : o + mint_len].decode("utf-8")
        o += mint_len
        has_owner = data[o] != 0
        o += 1
        owner = None
        if has_owner:
            (owner_len,) = struct.unpack_from("<I", data, o)
            o += 4
            owner = data[o : o + owner_len].decode("utf-8")
            o += owner_len
        decimals = data[o]
        o += 1
        (amount_len,) = struct.unpack_from("<I", data, o)
        o += 4
        amount = data[o : o + amount_len].decode("utf-8")
        o += amount_len
        has_ui_amount = data[o] != 0
        o += 1
        ui_amount = None
        if has_ui_amount:
            (ui_amount,) = struct.unpack_from("<d", data, o)
            o += 8
        pre_token_balances.append(
            TokenBalance(account_index, mint, owner, decimals, amount, ui_amount)
        )

    # Post-token balances
    (num_post_token_balances,) = struct.unpack_from("<I", data, o)
    o += 4
    post_token_balances: list[TokenBalance] = []
    for _ in range(num_post_token_balances):
        (account_index,) = struct.unpack_from("<I", data, o)
        o += 4
        (mint_len,) = struct.unpack_from("<I", data, o)
        o += 4
        mint = data[o : o + mint_len].decode("utf-8")
        o += mint_len
        has_owner = data[o] != 0
        o += 1
        owner = None
        if has_owner:
            (owner_len,) = struct.unpack_from("<I", data, o)
            o += 4
            owner = data[o : o + owner_len].decode("utf-8")
            o += owner_len
        decimals = data[o]
        o += 1
        (amount_len,) = struct.unpack_from("<I", data, o)
        o += 4
        amount = data[o : o + amount_len].decode("utf-8")
        o += amount_len
        has_ui_amount = data[o] != 0
        o += 1
        ui_amount = None
        if has_ui_amount:
            (ui_amount,) = struct.unpack_from("<d", data, o)
            o += 8
        post_token_balances.append(
            TokenBalance(account_index, mint, owner, decimals, amount, ui_amount)
        )

    # Execution trace (list of all executed instructions with full data, compute units, and results)
    (num_executed_instructions,) = struct.unpack_from("<I", data, o)
    o += 4
    execution_trace: list[ExecutedInstruction] = []
    for _ in range(num_executed_instructions):
        stack_depth = data[o]
        o += 1

        # Read full instruction data
        program_id = data[o : o + 32]
        o += 32
        (num_accounts,) = struct.unpack_from("<I", data, o)
        o += 4
        instruction_accounts: list[AccountMeta] = []
        for _ in range(num_accounts):
            pubkey = data[o : o + 32]
            o += 32
            is_signer = data[o] != 0
            o += 1
            is_writable = data[o] != 0
            o += 1
            instruction_accounts.append(AccountMeta(pubkey, is_signer, is_writable))
        (data_len,) = struct.unpack_from("<I", data, o)
        o += 4
        ix_data = data[o : o + data_len]
        o += data_len

        # Read compute units and result
        (compute_units_consumed,) = struct.unpack_from("<Q", data, o)
        o += 8
        (result,) = struct.unpack_from("<Q", data, o)
        o += 8

        instruction = Instruction(program_id, ix_data, instruction_accounts)
        execution_trace.append(
            ExecutedInstruction(stack_depth, instruction, compute_units_consumed, result)
        )

    return ExecutionResult(
        status=status,
        compute_units=compute_units,
        execution_time_us=execution_time_us,
        return_data=return_data,
        accounts=accounts,
        logs=logs,
        error_message=error_message,
        pre_balances=pre_balances,
        post_balances=post_balances,
        pre_token_balances=pre_token_balances,
        post_token_balances=post_token_balances,
        execution_trace=execution_trace,
    )
