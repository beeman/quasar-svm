"""Rich execution result with RPC metadata and helper methods."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import solders.pubkey as sp

from . import _wire, adapters
from .types import (
    ExecutionStatus,
    ExecutionStatusError,
    ExecutionStatusOk,
    ProgramError,
    ProgramErrorCustom,
    program_error_from_status,
)


@dataclass
class KeyedAccount:
    """Account with solders Pubkey address."""

    address: sp.Pubkey
    owner: sp.Pubkey
    lamports: int
    data: bytes
    executable: bool


@dataclass
class TokenBalance:
    """Token balance metadata."""

    account_index: int
    mint: str
    owner: str | None
    decimals: int
    amount: str
    ui_amount: float | None


@dataclass
class AccountMeta:
    """Account metadata for an instruction."""

    pubkey: sp.Pubkey
    is_signer: bool
    is_writable: bool


@dataclass
class Instruction:
    """Solana instruction."""

    program_id: sp.Pubkey
    accounts: list[AccountMeta]
    data: bytes


@dataclass
class ExecutedInstruction:
    """Executed instruction with full data, compute units, and result."""

    stack_depth: int
    instruction: Instruction
    compute_units_consumed: int
    result: int


@dataclass
class ExecutionTrace:
    """Complete execution trace of all instructions including CPIs."""

    instructions: list[ExecutedInstruction]


class ExecutionResult:
    """Rich execution result with RPC metadata and helper methods."""

    def __init__(self, raw_result: _wire.ExecutionResult) -> None:
        """Initialize ExecutionResult from wire format."""
        # Core execution data
        self.compute_units: int = raw_result.compute_units
        self.execution_time_us: int = raw_result.execution_time_us
        self.return_data: bytes = raw_result.return_data
        self.logs: list[str] = raw_result.logs

        # Status
        if raw_result.status == 0:
            self.status: ExecutionStatus = ExecutionStatusOk()
        else:
            error = program_error_from_status(raw_result.status, raw_result.error_message)
            self.status = ExecutionStatusError(error=error)

        # Accounts
        self.accounts: list[KeyedAccount] = [
            adapters.wire_account_to_keyed(acct) for acct in raw_result.accounts
        ]
        self._account_index: dict[str, int] = {
            bytes(acct.address).hex(): i for i, acct in enumerate(self.accounts)
        }

        # RPC metadata
        self.pre_balances: list[int] = raw_result.pre_balances
        self.post_balances: list[int] = raw_result.post_balances

        # Token balances
        self.pre_token_balances: list[TokenBalance] = [
            TokenBalance(
                tb.account_index,
                tb.mint,
                tb.owner,
                tb.decimals,
                tb.amount,
                tb.ui_amount,
            )
            for tb in raw_result.pre_token_balances
        ]
        self.post_token_balances: list[TokenBalance] = [
            TokenBalance(
                tb.account_index,
                tb.mint,
                tb.owner,
                tb.decimals,
                tb.amount,
                tb.ui_amount,
            )
            for tb in raw_result.post_token_balances
        ]

        # Execution trace (list of all executed instructions with full data, compute units, and results)
        self.execution_trace = ExecutionTrace(
            [
                ExecutedInstruction(
                    ei.stack_depth,
                    Instruction(
                        adapters.bytes_to_solders_pubkey(ei.instruction.program_id),
                        [
                            AccountMeta(
                                adapters.bytes_to_solders_pubkey(acc.pubkey),
                                acc.is_signer,
                                acc.is_writable,
                            )
                            for acc in ei.instruction.accounts
                        ],
                        ei.instruction.data,
                    ),
                    ei.compute_units_consumed,
                    ei.result,
                )
                for ei in raw_result.execution_trace
            ]
        )

    def is_success(self) -> bool:
        """Check if execution succeeded."""
        return self.status.ok

    def is_error(self) -> bool:
        """Check if execution failed."""
        return not self.status.ok

    def assert_success(self) -> None:
        """Raise if execution failed."""
        if not self.status.ok:
            error = self.status.error if isinstance(self.status, ExecutionStatusError) else None
            logs = "\n".join(self.logs)
            error_str = f"{error.type}: {error}" if error else "Unknown error"
            raise RuntimeError(f"Expected success, got {error_str}\n\nLogs:\n{logs}")

    def assert_error(self, expected: ProgramError) -> None:
        """Raise if execution didn't fail with expected error."""
        if self.status.ok:
            raise RuntimeError(f"Expected error {expected.type}, but execution succeeded")

        actual = self.status.error if isinstance(self.status, ExecutionStatusError) else None
        if actual is None or actual.type != expected.type:
            raise RuntimeError(
                f"Expected error {expected.type}, got {actual.type if actual else 'None'}"
            )

        # For custom errors, also check the code
        if expected.type == "Custom" and isinstance(expected, ProgramErrorCustom):
            if not isinstance(actual, ProgramErrorCustom) or actual.code != expected.code:
                raise RuntimeError(
                    f"Expected custom error code {expected.code}, got {actual.code if isinstance(actual, ProgramErrorCustom) else 'N/A'}"
                )

    def assert_custom_error(self, code: int) -> None:
        """Convenience for asserting custom error code."""
        self.assert_error(ProgramErrorCustom(code=code))

    def account(
        self, address: sp.Pubkey, decoder: Callable[[bytes], Any] | None = None
    ) -> KeyedAccount | Any | None:
        """Get account by address, optionally decode data.

        Args:
            address: Account address (solders Pubkey)
            decoder: Optional decoder function for account data

        Returns:
            KeyedAccount if no decoder, decoded data if decoder provided, or None if not found
        """
        hex_key = bytes(address).hex()
        idx = self._account_index.get(hex_key)
        if idx is None:
            return None

        acct = self.accounts[idx]
        if decoder:
            return decoder(acct.data)
        return acct

    def print_logs(self) -> None:
        """Print all logs to stdout."""
        for log in self.logs:
            print(log)
