"""Type definitions for execution status and program errors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union


# Program Error Types - discriminated union using dataclasses
@dataclass
class ProgramErrorCustom:
    """Custom program error with numeric code."""

    type: Literal["Custom"] = "Custom"
    code: int = 0


@dataclass
class ProgramErrorInvalidArgument:
    """The arguments provided to a program instruction were invalid."""

    type: Literal["InvalidArgument"] = "InvalidArgument"


@dataclass
class ProgramErrorInvalidInstructionData:
    """An instruction's data contents was invalid."""

    type: Literal["InvalidInstructionData"] = "InvalidInstructionData"


@dataclass
class ProgramErrorInvalidAccountData:
    """An account's data contents was invalid."""

    type: Literal["InvalidAccountData"] = "InvalidAccountData"


@dataclass
class ProgramErrorAccountDataTooSmall:
    """An account's data was too small."""

    type: Literal["AccountDataTooSmall"] = "AccountDataTooSmall"


@dataclass
class ProgramErrorInsufficientFunds:
    """An account's balance was too small to complete the operation."""

    type: Literal["InsufficientFunds"] = "InsufficientFunds"


@dataclass
class ProgramErrorIncorrectProgramId:
    """The account did not have the expected program id."""

    type: Literal["IncorrectProgramId"] = "IncorrectProgramId"


@dataclass
class ProgramErrorMissingRequiredSignature:
    """A signature was required but not found."""

    type: Literal["MissingRequiredSignature"] = "MissingRequiredSignature"


@dataclass
class ProgramErrorAccountAlreadyInitialized:
    """An initialize instruction was sent to an account that has already been initialized."""

    type: Literal["AccountAlreadyInitialized"] = "AccountAlreadyInitialized"


@dataclass
class ProgramErrorUninitializedAccount:
    """An attempt to operate on an account that hasn't been initialized."""

    type: Literal["UninitializedAccount"] = "UninitializedAccount"


@dataclass
class ProgramErrorMissingAccount:
    """The instruction expected additional account keys."""

    type: Literal["MissingAccount"] = "MissingAccount"


@dataclass
class ProgramErrorInvalidSeeds:
    """Failed to create a program address."""

    type: Literal["InvalidSeeds"] = "InvalidSeeds"


@dataclass
class ProgramErrorArithmeticOverflow:
    """An arithmetic operation overflowed."""

    type: Literal["ArithmeticOverflow"] = "ArithmeticOverflow"


@dataclass
class ProgramErrorAccountNotRentExempt:
    """Account is not rent exempt."""

    type: Literal["AccountNotRentExempt"] = "AccountNotRentExempt"


@dataclass
class ProgramErrorInvalidAccountOwner:
    """Account does not have the expected owner."""

    type: Literal["InvalidAccountOwner"] = "InvalidAccountOwner"


@dataclass
class ProgramErrorIncorrectAuthority:
    """Account does not match the expected authority."""

    type: Literal["IncorrectAuthority"] = "IncorrectAuthority"


@dataclass
class ProgramErrorImmutable:
    """The account cannot be modified."""

    type: Literal["Immutable"] = "Immutable"


@dataclass
class ProgramErrorBorshIoError:
    """Failed to serialize or deserialize account data."""

    type: Literal["BorshIoError"] = "BorshIoError"


@dataclass
class ProgramErrorComputeBudgetExceeded:
    """Computational budget exceeded."""

    type: Literal["ComputeBudgetExceeded"] = "ComputeBudgetExceeded"


@dataclass
class ProgramErrorRuntime:
    """Runtime error with message."""

    type: Literal["Runtime"] = "Runtime"
    message: str = ""


# Union of all program error types
ProgramError = Union[
    ProgramErrorCustom,
    ProgramErrorInvalidArgument,
    ProgramErrorInvalidInstructionData,
    ProgramErrorInvalidAccountData,
    ProgramErrorAccountDataTooSmall,
    ProgramErrorInsufficientFunds,
    ProgramErrorIncorrectProgramId,
    ProgramErrorMissingRequiredSignature,
    ProgramErrorAccountAlreadyInitialized,
    ProgramErrorUninitializedAccount,
    ProgramErrorMissingAccount,
    ProgramErrorInvalidSeeds,
    ProgramErrorArithmeticOverflow,
    ProgramErrorAccountNotRentExempt,
    ProgramErrorInvalidAccountOwner,
    ProgramErrorIncorrectAuthority,
    ProgramErrorImmutable,
    ProgramErrorBorshIoError,
    ProgramErrorComputeBudgetExceeded,
    ProgramErrorRuntime,
]


# Execution Status Types
@dataclass
class ExecutionStatusOk:
    """Successful execution."""

    ok: Literal[True] = True


@dataclass
class ExecutionStatusError:
    """Failed execution with error."""

    ok: Literal[False] = False
    error: ProgramError | None = None


ExecutionStatus = Union[ExecutionStatusOk, ExecutionStatusError]


def program_error_from_status(status: int, error_message: str | None) -> ProgramError:
    """Map wire status code to ProgramError.

    Status codes:
    - 0 = success (not an error)
    - Positive = Custom error with code
    - Negative = Known Solana error variant
    """
    if status > 0:
        return ProgramErrorCustom(code=status)

    # Map negative status codes to specific error types
    error_map: dict[int, type[ProgramError]] = {
        -1: ProgramErrorInvalidArgument,
        -2: ProgramErrorInvalidInstructionData,
        -3: ProgramErrorInvalidAccountData,
        -4: ProgramErrorAccountDataTooSmall,
        -5: ProgramErrorInsufficientFunds,
        -6: ProgramErrorIncorrectProgramId,
        -7: ProgramErrorMissingRequiredSignature,
        -8: ProgramErrorAccountAlreadyInitialized,
        -9: ProgramErrorUninitializedAccount,
        -10: ProgramErrorMissingAccount,
        -11: ProgramErrorInvalidSeeds,
        -12: ProgramErrorArithmeticOverflow,
        -13: ProgramErrorAccountNotRentExempt,
        -14: ProgramErrorInvalidAccountOwner,
        -15: ProgramErrorIncorrectAuthority,
        -16: ProgramErrorImmutable,
        -17: ProgramErrorBorshIoError,
        -18: ProgramErrorComputeBudgetExceeded,
    }

    error_class = error_map.get(status)
    if error_class:
        return error_class()

    # Fallback to runtime error with message
    return ProgramErrorRuntime(message=error_message or f"Unknown error (code {status})")
