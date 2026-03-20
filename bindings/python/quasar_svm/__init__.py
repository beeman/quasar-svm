"""Quasar-SVM: Python bindings for the Solana SVM execution engine with solders integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

import solders.instruction as si
import solders.pubkey as sp

from . import _ffi, adapters
from .factories import (
    create_keyed_associated_token_account,
    create_keyed_mint_account,
    create_keyed_system_account,
    create_keyed_token_account,
    rent_minimum_balance,
)
from .programs import (
    LAMPORTS_PER_SOL,
    LOADER_V2,
    LOADER_V3,
    SPL_ASSOCIATED_TOKEN_PROGRAM_ID,
    SPL_TOKEN_2022_PROGRAM_ID,
    SPL_TOKEN_PROGRAM_ID,
    SYSTEM_PROGRAM_ID,
    load_spl_associated_token,
    load_spl_token,
    load_spl_token_2022,
)
from .result import (
    AccountMeta,
    ExecutedInstruction,
    ExecutionResult,
    ExecutionTrace,
    Instruction,
    KeyedAccount,
    TokenBalance,
)
from .types import ExecutionStatus, ProgramError

if TYPE_CHECKING:
    from typing_extensions import Self

__version__ = "0.1.0"

__all__ = [
    # Main class
    "QuasarSvm",
    # Result types
    "ExecutionResult",
    "KeyedAccount",
    "TokenBalance",
    "ExecutionTrace",
    "ExecutedInstruction",
    "Instruction",
    "AccountMeta",
    # Type definitions
    "ProgramError",
    "ExecutionStatus",
    # Program constants
    "SPL_TOKEN_PROGRAM_ID",
    "SPL_TOKEN_2022_PROGRAM_ID",
    "SPL_ASSOCIATED_TOKEN_PROGRAM_ID",
    "SYSTEM_PROGRAM_ID",
    "LOADER_V2",
    "LOADER_V3",
    "LAMPORTS_PER_SOL",
    # Factories
    "create_keyed_system_account",
    "create_keyed_mint_account",
    "create_keyed_token_account",
    "create_keyed_associated_token_account",
    "rent_minimum_balance",
]


class QuasarSvm:
    """Lightweight Solana SVM execution engine with solders integration.

    Example:
        >>> from quasar_svm import QuasarSvm
        >>> from solders.pubkey import Pubkey
        >>> from solders.instruction import Instruction, AccountMeta
        >>>
        >>> with QuasarSvm() as svm:
        ...     result = svm.process_instruction(instruction, accounts)
        ...     result.assert_success()
    """

    def __init__(
        self,
        *,
        load_token: bool = True,
        load_token_2022: bool = True,
        load_associated_token: bool = True,
    ) -> None:
        """Initialize QuasarSvm and optionally load SPL programs.

        Args:
            load_token: Load SPL Token program (default: True)
            load_token_2022: Load SPL Token-2022 program (default: True)
            load_associated_token: Load SPL Associated Token program (default: True)

        Raises:
            RuntimeError: If SVM initialization fails
        """
        self._ptr = _ffi.svm_new()
        if not self._ptr:
            raise RuntimeError(
                f"Failed to create QuasarSvm: {_ffi.last_error() or 'unknown'}"
            )
        self._freed = False

        # Load SPL programs by default
        if load_token:
            self.add_program(SPL_TOKEN_PROGRAM_ID, load_spl_token(), LOADER_V2)
        if load_token_2022:
            self.add_program(SPL_TOKEN_2022_PROGRAM_ID, load_spl_token_2022(), LOADER_V3)
        if load_associated_token:
            self.add_program(
                SPL_ASSOCIATED_TOKEN_PROGRAM_ID, load_spl_associated_token(), LOADER_V2
            )

    def __del__(self) -> None:
        """Free native resources on garbage collection."""
        self.free()

    def __enter__(self) -> Self:
        """Enter context manager."""
        return self

    def __exit__(self, *_: object) -> None:
        """Exit context manager and free resources."""
        self.free()

    def free(self) -> None:
        """Explicitly free native SVM resources."""
        if not self._freed and self._ptr:
            _ffi.svm_free(self._ptr)
            self._freed = True

    def _check(self, code: int) -> None:
        """Check FFI return code and raise on error."""
        if code != 0:
            raise RuntimeError(
                f"QuasarSvm error ({code}): {_ffi.last_error() or 'unknown'}"
            )

    def add_program(
        self, program_id: sp.Pubkey, elf: bytes, loader_version: int = LOADER_V3
    ) -> Self:
        """Add a BPF program to the SVM.

        Args:
            program_id: Program address (solders Pubkey)
            elf: ELF binary data
            loader_version: 2 for Loader v2, 3 for Loader v3 (default: 3)

        Returns:
            self for chaining

        Raises:
            RuntimeError: If program loading fails
        """
        self._check(
            _ffi.svm_add_program(self._ptr, bytes(program_id), elf, loader_version)
        )
        return self

    def set_clock(
        self,
        *,
        slot: int,
        epoch_start_timestamp: int,
        epoch: int,
        leader_schedule_epoch: int,
        unix_timestamp: int,
    ) -> None:
        """Set Clock sysvar.

        Args:
            slot: Current slot
            epoch_start_timestamp: Epoch start timestamp
            epoch: Current epoch
            leader_schedule_epoch: Leader schedule epoch
            unix_timestamp: Unix timestamp
        """
        self._check(
            _ffi.svm_set_clock(
                self._ptr,
                slot,
                epoch_start_timestamp,
                epoch,
                leader_schedule_epoch,
                unix_timestamp,
            )
        )

    def warp_to_slot(self, slot: int) -> None:
        """Warp to a future slot.

        Args:
            slot: Target slot number
        """
        self._check(_ffi.svm_warp_to_slot(self._ptr, slot))

    def set_rent(self, lamports_per_byte_year: int) -> None:
        """Set Rent sysvar.

        Args:
            lamports_per_byte_year: Lamports per byte-year
        """
        self._check(_ffi.svm_set_rent(self._ptr, lamports_per_byte_year))

    def set_epoch_schedule(
        self,
        *,
        slots_per_epoch: int,
        leader_schedule_slot_offset: int,
        warmup: bool,
        first_normal_epoch: int,
        first_normal_slot: int,
    ) -> None:
        """Set EpochSchedule sysvar.

        Args:
            slots_per_epoch: Slots per epoch
            leader_schedule_slot_offset: Leader schedule slot offset
            warmup: Whether warmup is enabled
            first_normal_epoch: First normal epoch
            first_normal_slot: First normal slot
        """
        self._check(
            _ffi.svm_set_epoch_schedule(
                self._ptr,
                slots_per_epoch,
                leader_schedule_slot_offset,
                warmup,
                first_normal_epoch,
                first_normal_slot,
            )
        )

    def set_compute_budget(self, max_units: int) -> None:
        """Set compute budget limit.

        Args:
            max_units: Maximum compute units
        """
        self._check(_ffi.svm_set_compute_budget(self._ptr, max_units))

    def process_instruction(
        self, instruction: si.Instruction, accounts: list[KeyedAccount]
    ) -> ExecutionResult:
        """Execute a single instruction.

        Args:
            instruction: solders Instruction
            accounts: List of accounts (KeyedAccount with solders Pubkeys)

        Returns:
            ExecutionResult with metadata

        Raises:
            RuntimeError: If execution call fails (not program errors)
        """
        from . import _wire

        ix_wire = adapters.solders_instruction_to_wire(instruction)
        accts_wire = [adapters.keyed_account_to_wire(a) for a in accounts]

        raw = _ffi.svm_process_transaction(
            self._ptr,
            _wire.serialize_instructions([ix_wire]),
            _wire.serialize_accounts(accts_wire),
        )
        return ExecutionResult(_wire.deserialize_result(raw))

    def process_instruction_chain(
        self, instructions: list[si.Instruction], accounts: list[KeyedAccount]
    ) -> ExecutionResult:
        """Execute multiple instructions atomically.

        Args:
            instructions: List of solders Instructions
            accounts: List of accounts (KeyedAccount with solders Pubkeys)

        Returns:
            ExecutionResult with metadata

        Raises:
            RuntimeError: If execution call fails (not program errors)
        """
        from . import _wire

        ixs_wire = [adapters.solders_instruction_to_wire(ix) for ix in instructions]
        accts_wire = [adapters.keyed_account_to_wire(a) for a in accounts]

        raw = _ffi.svm_process_transaction(
            self._ptr,
            _wire.serialize_instructions(ixs_wire),
            _wire.serialize_accounts(accts_wire),
        )
        return ExecutionResult(_wire.deserialize_result(raw))
