# QuasarSVM Python Bindings

Python bindings for QuasarSVM with [solders](https://github.com/kevinheavey/solders) integration.

## Installation

```bash
pip install quasar-svm
```

## Requirements

- Python >= 3.10
- solders >= 0.27.0

## Quick Start

```python
from quasar_svm import (
    QuasarSvm,
    create_keyed_mint_account,
    create_keyed_token_account,
    SPL_TOKEN_PROGRAM_ID,
)
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta

# Initialize with SPL programs loaded
with QuasarSvm() as svm:
    # Create accounts
    authority = Pubkey.new_unique()
    mint = create_keyed_mint_account(
        Pubkey.new_unique(),
        mint_authority=authority,
        decimals=6,
        supply=10_000,
    )
    token_account = create_keyed_token_account(
        Pubkey.new_unique(),
        mint=mint.address,
        owner=authority,
        amount=1_000,
    )

    # Execute instruction
    result = svm.process_instruction(transfer_ix, [mint, token_account])
    result.assert_success()
    print(f"Compute units: {result.compute_units}")
```

## Core API

### QuasarSvm

Main class for SVM execution.

```python
from quasar_svm import QuasarSvm

# Auto-load all SPL programs
svm = QuasarSvm()

# Selective program loading
svm = QuasarSvm(
    load_token=True,
    load_token_2022=False,
    load_associated_token=True,
)

# Context manager for automatic cleanup
with QuasarSvm() as svm:
    result = svm.process_instruction(ix, accounts)
```

#### Methods

**`add_program(program_id: Pubkey, elf: bytes, loader_version: int = 3)`**

Load a custom BPF program.

```python
from quasar_svm import LOADER_V2, LOADER_V3

svm.add_program(program_id, elf_data, LOADER_V3)
```

**`process_instruction(instruction: Instruction, accounts: List[KeyedAccount]) -> ExecutionResult`**

Execute a single instruction.

```python
result = svm.process_instruction(ix, [account1, account2])
```

**`process_instruction_chain(instructions: List[Instruction], accounts: List[KeyedAccount]) -> ExecutionResult`**

Execute multiple instructions atomically.

```python
result = svm.process_instruction_chain([ix1, ix2], accounts)
```

#### Sysvar Configuration

```python
# Warp to future slot
svm.warp_to_slot(100)

# Set clock
svm.set_clock(
    slot=100,
    epoch_start_timestamp=0,
    epoch=0,
    leader_schedule_epoch=0,
    unix_timestamp=1000000,
)

# Set rent
svm.set_rent(lamports_per_byte_year=6960)

# Set epoch schedule
svm.set_epoch_schedule(
    slots_per_epoch=432000,
    leader_schedule_slot_offset=0,
    warmup=False,
    first_normal_epoch=0,
    first_normal_slot=0,
)

# Set compute budget
svm.set_compute_budget(max_units=200_000)
```

### ExecutionResult

Rich result object with metadata and helper methods.

#### Properties

```python
result.status              # ExecutionStatus (ok or error)
result.compute_units       # int - compute units consumed
result.execution_time_us   # int - execution time in microseconds
result.return_data         # bytes - program return data
result.accounts            # List[KeyedAccount] - resulting accounts
result.logs                # List[str] - program logs

# RPC metadata
result.pre_balances        # List[int]
result.post_balances       # List[int]
result.pre_token_balances  # List[TokenBalance]
result.post_token_balances # List[TokenBalance]
result.execution_trace     # ExecutionTrace
```

#### Methods

**`is_success() -> bool`**

Check if execution succeeded.

```python
if result.is_success():
    print("Success!")
```

**`is_error() -> bool`**

Check if execution failed.

**`assert_success()`**

Raise RuntimeError if execution failed.

```python
result.assert_success()
```

**`assert_error(expected: ProgramError)`**

Raise RuntimeError if didn't fail with expected error.

```python
from quasar_svm.types import ProgramErrorInsufficientFunds

result.assert_error(ProgramErrorInsufficientFunds())
```

**`assert_custom_error(code: int)`**

Convenience for asserting custom error code.

```python
result.assert_custom_error(6001)
```

**`account(address: Pubkey, decoder=None) -> KeyedAccount | Any | None`**

Get account by address, optionally decode data.

```python
# Get raw account
acct = result.account(address)
print(acct.lamports)

# Decode account data
def decode_token(data: bytes) -> dict:
    # Your decoder logic
    return {...}

token = result.account(address, decode_token)
print(token['amount'])
```

**`print_logs()`**

Print all logs to stdout.

```python
result.print_logs()
```

## Account Factories

Convenient functions for creating pre-initialized accounts.

### System Account

```python
from quasar_svm import create_keyed_system_account, LAMPORTS_PER_SOL

account = create_keyed_system_account(
    Pubkey.new_unique(),
    lamports=LAMPORTS_PER_SOL,  # 1 SOL
)
```

### Mint Account

```python
from quasar_svm import create_keyed_mint_account, SPL_TOKEN_PROGRAM_ID

mint = create_keyed_mint_account(
    Pubkey.new_unique(),
    mint_authority=authority_pubkey,
    decimals=6,
    supply=10_000,
    freeze_authority=None,  # optional
    token_program_id=SPL_TOKEN_PROGRAM_ID,  # default
)
```

### Token Account

```python
from quasar_svm import create_keyed_token_account

token_account = create_keyed_token_account(
    Pubkey.new_unique(),
    mint=mint_pubkey,
    owner=owner_pubkey,
    amount=1_000,
    token_program_id=SPL_TOKEN_PROGRAM_ID,  # default
)
```

### Associated Token Account

```python
from quasar_svm import create_keyed_associated_token_account

# Automatically derives ATA address
ata = create_keyed_associated_token_account(
    owner=owner_pubkey,
    mint=mint_pubkey,
    amount=1_000,
    token_program_id=SPL_TOKEN_PROGRAM_ID,  # default
)
print(ata.address)  # Derived ATA address
```

## Program Constants

```python
from quasar_svm import (
    SPL_TOKEN_PROGRAM_ID,
    SPL_TOKEN_2022_PROGRAM_ID,
    SPL_ASSOCIATED_TOKEN_PROGRAM_ID,
    SYSTEM_PROGRAM_ID,
    LOADER_V2,
    LOADER_V3,
    LAMPORTS_PER_SOL,
)
```

## Complete Example

```python
from quasar_svm import (
    QuasarSvm,
    create_keyed_mint_account,
    create_keyed_associated_token_account,
    SPL_TOKEN_PROGRAM_ID,
)
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta

# Create authority and accounts
authority = Pubkey.new_unique()
recipient = Pubkey.new_unique()

# Initialize VM with SPL programs
with QuasarSvm() as svm:
    # Create mint
    mint = create_keyed_mint_account(
        Pubkey.new_unique(),
        mint_authority=authority,
        decimals=6,
        supply=10_000,
    )

    # Create token accounts (ATAs derived automatically)
    alice = create_keyed_associated_token_account(
        owner=authority,
        mint=mint.address,
        amount=5_000,
    )
    bob = create_keyed_associated_token_account(
        owner=recipient,
        mint=mint.address,
        amount=0,
    )

    # Build transfer instruction
    # Use spl-token instruction builders or build manually
    transfer_ix = Instruction(
        program_id=SPL_TOKEN_PROGRAM_ID,
        data=bytes([3]) + (1_000).to_bytes(8, 'little'),  # Transfer instruction
        accounts=[
            AccountMeta(alice.address, is_signer=False, is_writable=True),
            AccountMeta(bob.address, is_signer=False, is_writable=True),
            AccountMeta(authority, is_signer=True, is_writable=False),
        ],
    )

    # Execute
    result = svm.process_instruction(transfer_ix, [mint, alice, bob])

    # Verify
    result.assert_success()
    print(f"Compute units: {result.compute_units}")
    print(f"Execution time: {result.execution_time_us}μs")

    # Check updated account
    bob_account = result.account(bob.address)
    print(f"Bob's lamports: {bob_account.lamports}")
```

## Type System

### KeyedAccount

```python
@dataclass
class KeyedAccount:
    address: Pubkey        # Account address
    owner: Pubkey          # Owner program
    lamports: int          # Account balance
    data: bytes            # Account data
    executable: bool       # Executable flag
```

### ProgramError

Discriminated union of error types:

```python
ProgramErrorCustom(code=6001)
ProgramErrorInvalidArgument()
ProgramErrorInvalidInstructionData()
ProgramErrorInsufficientFunds()
# ... and more
```

### ExecutionStatus

```python
ExecutionStatusOk()  # Successful execution
ExecutionStatusError(error=ProgramErrorCustom(code=6001))  # Failed execution
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black quasar_svm/
ruff check quasar_svm/

# Type checking
mypy quasar_svm/
```

## Comparison with TypeScript Kit Layer

The Python API closely mirrors the TypeScript kit layer:

| Feature | Python | TypeScript (kit) |
|---------|--------|------------------|
| Address Type | `solders.Pubkey` | `Address` (branded string) |
| Instruction Type | `solders.Instruction` | `Instruction` from `@solana/instructions` |
| Account Type | `KeyedAccount` | `Account<Uint8Array>` from `@solana/accounts` |
| ATA Derivation | `Pubkey.find_program_address()` | `getProgramDerivedAddress()` (async) |
| Memory Management | Context manager (`with`) | `using` or explicit `free()` |

Both provide the same core functionality with type-safe, ergonomic APIs.

## License

MIT
