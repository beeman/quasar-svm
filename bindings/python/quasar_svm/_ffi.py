"""Load the quasar-svm shared library and declare C function signatures."""

from __future__ import annotations

import ctypes
import os
import platform
import sys
from pathlib import Path


def _find_library() -> str:
    """Find the quasar-svm native library.

    Search order:
    1. QUASAR_SVM_LIB environment variable
    2. Bundled library in package directory (for installed wheels)
    3. Local build in target/release/ (for development)
    """
    # 1. Environment variable override
    env = os.environ.get("QUASAR_SVM_LIB")
    if env:
        return env

    system = platform.system()
    pkg_dir = Path(__file__).resolve().parent

    # 2. Bundled library (for pip-installed wheels)
    if system == "Darwin":
        bundled = pkg_dir / "libquasar_svm.dylib"
    elif system == "Windows":
        bundled = pkg_dir / "quasar_svm.dll"
    else:
        bundled = pkg_dir / "libquasar_svm.so"

    if bundled.exists():
        return str(bundled)

    # 3. Development build
    base = pkg_dir.parent.parent.parent
    if system == "Darwin":
        return str(base / "target" / "release" / "libquasar_svm.dylib")
    elif system == "Windows":
        return str(base / "target" / "release" / "quasar_svm.dll")
    else:
        return str(base / "target" / "release" / "libquasar_svm.so")


_lib = ctypes.CDLL(_find_library())

# -- Error query --
_lib.quasar_last_error.restype = ctypes.c_char_p
_lib.quasar_last_error.argtypes = []

# -- Lifecycle --
_lib.quasar_svm_new.restype = ctypes.c_void_p
_lib.quasar_svm_new.argtypes = []

_lib.quasar_svm_free.restype = None
_lib.quasar_svm_free.argtypes = [ctypes.c_void_p]

# -- Program management --
_lib.quasar_svm_add_program.restype = ctypes.c_int32
_lib.quasar_svm_add_program.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.c_uint8,
]

# -- Sysvars --
_lib.quasar_svm_set_clock.restype = ctypes.c_int32
_lib.quasar_svm_set_clock.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.c_int64,
    ctypes.c_uint64,
    ctypes.c_uint64,
    ctypes.c_int64,
]

_lib.quasar_svm_warp_to_slot.restype = ctypes.c_int32
_lib.quasar_svm_warp_to_slot.argtypes = [ctypes.c_void_p, ctypes.c_uint64]

_lib.quasar_svm_set_rent.restype = ctypes.c_int32
_lib.quasar_svm_set_rent.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.c_double,
    ctypes.c_uint8,
]

_lib.quasar_svm_set_epoch_schedule.restype = ctypes.c_int32
_lib.quasar_svm_set_epoch_schedule.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.c_uint64,
    ctypes.c_bool,
    ctypes.c_uint64,
    ctypes.c_uint64,
]

_lib.quasar_svm_set_compute_budget.restype = ctypes.c_int32
_lib.quasar_svm_set_compute_budget.argtypes = [ctypes.c_void_p, ctypes.c_uint64]

# -- Execution --
# Note: The FFI only exports process_transaction which handles one or more instructions
_lib.quasar_svm_process_transaction.restype = ctypes.c_int32
_lib.quasar_svm_process_transaction.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.POINTER(ctypes.c_uint64),
]

# -- Result free --
_lib.quasar_result_free.restype = None
_lib.quasar_result_free.argtypes = [ctypes.c_void_p, ctypes.c_uint64]


def last_error() -> str | None:
    err = _lib.quasar_last_error()
    return err.decode("utf-8") if err else None


def svm_new() -> ctypes.c_void_p:
    return _lib.quasar_svm_new()


def svm_free(ptr: ctypes.c_void_p) -> None:
    _lib.quasar_svm_free(ptr)


def svm_add_program(
    ptr: ctypes.c_void_p, program_id: bytes, elf: bytes, loader_version: int = 3
) -> int:
    return _lib.quasar_svm_add_program(ptr, program_id, elf, len(elf), loader_version)


def svm_set_clock(
    ptr: ctypes.c_void_p,
    slot: int,
    epoch_start_timestamp: int,
    epoch: int,
    leader_schedule_epoch: int,
    unix_timestamp: int,
) -> int:
    return _lib.quasar_svm_set_clock(
        ptr, slot, epoch_start_timestamp, epoch, leader_schedule_epoch, unix_timestamp
    )


def svm_warp_to_slot(ptr: ctypes.c_void_p, slot: int) -> int:
    return _lib.quasar_svm_warp_to_slot(ptr, slot)


def svm_set_rent(
    ptr: ctypes.c_void_p,
    lamports_per_byte_year: int,
    exemption_threshold: float,
    burn_percent: int,
) -> int:
    return _lib.quasar_svm_set_rent(
        ptr, lamports_per_byte_year, exemption_threshold, burn_percent
    )


def svm_set_epoch_schedule(
    ptr: ctypes.c_void_p,
    slots_per_epoch: int,
    leader_schedule_slot_offset: int,
    warmup: bool,
    first_normal_epoch: int,
    first_normal_slot: int,
) -> int:
    return _lib.quasar_svm_set_epoch_schedule(
        ptr,
        slots_per_epoch,
        leader_schedule_slot_offset,
        warmup,
        first_normal_epoch,
        first_normal_slot,
    )


def svm_set_compute_budget(ptr: ctypes.c_void_p, max_units: int) -> int:
    return _lib.quasar_svm_set_compute_budget(ptr, max_units)


def _execute(fn, ptr: ctypes.c_void_p, ix_buf: bytes, acct_buf: bytes) -> bytes:
    result_ptr = ctypes.c_void_p()
    result_len = ctypes.c_uint64()

    code = fn(
        ptr,
        ix_buf,
        len(ix_buf),
        acct_buf,
        len(acct_buf),
        ctypes.byref(result_ptr),
        ctypes.byref(result_len),
    )

    if code != 0:
        err = last_error()
        raise RuntimeError(f"Execution error ({code}): {err or 'unknown'}")

    length = result_len.value
    buf = (ctypes.c_uint8 * length).from_address(result_ptr.value)
    data = bytes(buf)
    _lib.quasar_result_free(result_ptr, length)
    return data


def svm_process_instruction(
    ptr: ctypes.c_void_p, ix_buf: bytes, acct_buf: bytes
) -> bytes:
    """Process a single instruction (uses process_transaction internally)."""
    return _execute(_lib.quasar_svm_process_transaction, ptr, ix_buf, acct_buf)


def svm_process_instruction_chain(
    ptr: ctypes.c_void_p, ix_buf: bytes, acct_buf: bytes
) -> bytes:
    """Process multiple instructions (uses process_transaction internally)."""
    return _execute(_lib.quasar_svm_process_transaction, ptr, ix_buf, acct_buf)


def svm_process_transaction(
    ptr: ctypes.c_void_p, ix_buf: bytes, acct_buf: bytes
) -> bytes:
    """Process a transaction with one or more instructions."""
    return _execute(_lib.quasar_svm_process_transaction, ptr, ix_buf, acct_buf)
