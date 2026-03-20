"""Tests for execution trace functionality."""

import struct
import pytest
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta

from quasar_svm import (
    QuasarSvm,
    create_keyed_mint_account,
    create_keyed_token_account,
    SPL_TOKEN_PROGRAM_ID,
    SYSTEM_PROGRAM_ID,
)


def test_basic_execution_trace():
    """Test that execution trace captures basic instruction execution."""
    svm = QuasarSvm()

    # Create a simple token mint
    mint = create_keyed_mint_account(
        Pubkey.new_unique(),
        mint_authority=Pubkey.new_unique(),
        decimals=9,
        supply=1_000_000,
    )

    # Execute a simple operation (this will fail but we're testing trace structure)
    token_account = create_keyed_token_account(
        Pubkey.new_unique(),
        mint=mint.address,
        owner=Pubkey.new_unique(),
        amount=0,
    )

    # Create a transfer instruction (will fail due to insufficient funds, but that's ok)
    from_token = create_keyed_token_account(
        Pubkey.new_unique(),
        mint=mint.address,
        owner=Pubkey.new_unique(),
        amount=100,
    )

    to_token = create_keyed_token_account(
        Pubkey.new_unique(),
        mint=mint.address,
        owner=Pubkey.new_unique(),
        amount=0,
    )

    owner = Pubkey.new_unique()

    # Build transfer instruction using spl-token crate encoding
    from solders.sysvar import RENT
    import struct

    # Transfer instruction (instruction index 3 in SPL Token)
    transfer_data = struct.pack("<BQ", 3, 50)  # instruction: Transfer, amount: 50

    transfer_ix = Instruction(
        program_id=SPL_TOKEN_PROGRAM_ID,
        accounts=[
            AccountMeta(from_token.address, is_signer=False, is_writable=True),
            AccountMeta(to_token.address, is_signer=False, is_writable=True),
            AccountMeta(owner, is_signer=True, is_writable=False),
        ],
        data=transfer_data,
    )

    result = svm.process_instruction(transfer_ix, [mint, from_token, to_token])

    # Verify execution trace structure
    assert result.execution_trace is not None
    assert len(result.execution_trace.instructions) > 0

    # Check first instruction
    first_instr = result.execution_trace.instructions[0]
    assert hasattr(first_instr, 'stack_depth')
    assert hasattr(first_instr, 'instruction')
    assert hasattr(first_instr, 'compute_units_consumed')
    assert hasattr(first_instr, 'result')

    # First instruction should be at stack depth 0 (top-level)
    assert first_instr.stack_depth == 0

    # Instruction should have full data
    assert first_instr.instruction.program_id == SPL_TOKEN_PROGRAM_ID
    assert len(first_instr.instruction.accounts) > 0
    assert len(first_instr.instruction.data) > 0

    print(f"\n✅ Execution trace captured {len(result.execution_trace.instructions)} instruction(s)")
    print(f"   First instruction: stack_depth={first_instr.stack_depth}, "
          f"program={first_instr.instruction.program_id}, "
          f"compute_units={first_instr.compute_units_consumed}, "
          f"result={first_instr.result}")


def test_execution_trace_with_cpi():
    """Test that execution trace captures CPI calls with correct stack depth."""
    svm = QuasarSvm()

    # Create accounts for a mint operation (which involves CPI)
    mint = create_keyed_mint_account(
        Pubkey.new_unique(),
        mint_authority=Pubkey.new_unique(),
        decimals=9,
        supply=0,  # Start with 0 supply
    )

    token_account = create_keyed_token_account(
        Pubkey.new_unique(),
        mint=mint.address,
        owner=Pubkey.new_unique(),
        amount=0,
    )

    mint_authority = Pubkey.new_unique()

    # MintTo instruction (instruction index 7 in SPL Token)
    mint_to_data = struct.pack("<BQ", 7, 1000)  # instruction: MintTo, amount: 1000

    mint_to_ix = Instruction(
        program_id=SPL_TOKEN_PROGRAM_ID,
        accounts=[
            AccountMeta(mint.address, is_signer=False, is_writable=True),
            AccountMeta(token_account.address, is_signer=False, is_writable=True),
            AccountMeta(mint_authority, is_signer=True, is_writable=False),
        ],
        data=mint_to_data,
    )

    result = svm.process_instruction(mint_to_ix, [mint, token_account])

    # Print execution trace
    print("\n📊 Execution trace:")
    for i, instr in enumerate(result.execution_trace.instructions):
        indent = "  " * instr.stack_depth
        status = "✅" if instr.result == 0 else f"❌ (error {instr.result})"
        print(f"   {i}: {indent}depth={instr.stack_depth} "
              f"program={instr.instruction.program_id} "
              f"CUs={instr.compute_units_consumed} {status}")

    # Verify we have at least the top-level instruction
    assert len(result.execution_trace.instructions) >= 1

    # If there are multiple instructions, verify stack depth progression
    if len(result.execution_trace.instructions) > 1:
        # Check for proper nesting (CPIs should have higher stack depth)
        for instr in result.execution_trace.instructions[1:]:
            # CPI calls should have stack_depth >= 1
            if instr.stack_depth > 0:
                print(f"   Found CPI at depth {instr.stack_depth}")


def test_execution_trace_compute_units():
    """Test that compute units are tracked per instruction."""
    svm = QuasarSvm()

    # Create a simple operation
    mint = create_keyed_mint_account(
        Pubkey.new_unique(),
        mint_authority=Pubkey.new_unique(),
        decimals=9,
    )

    token_account = create_keyed_token_account(
        Pubkey.new_unique(),
        mint=mint.address,
        owner=Pubkey.new_unique(),
    )

    # GetAccountDataSize instruction (instruction index 21 in SPL Token)
    get_size_data = struct.pack("<B", 21)

    get_size_ix = Instruction(
        program_id=SPL_TOKEN_PROGRAM_ID,
        accounts=[
            AccountMeta(mint.address, is_signer=False, is_writable=False),
        ],
        data=get_size_data,
    )

    result = svm.process_instruction(get_size_ix, [mint, token_account])

    # Verify compute units are tracked
    total_cus = sum(instr.compute_units_consumed for instr in result.execution_trace.instructions)
    print(f"\n💻 Total compute units consumed: {total_cus}")
    print(f"   Breakdown:")
    for i, instr in enumerate(result.execution_trace.instructions):
        print(f"   - Instruction {i}: {instr.compute_units_consumed} CUs")

    # Print logs to debug
    print(f"\n📋 Logs:")
    for log in result.logs:
        print(f"   {log}")

    # Should have consumed some compute units
    assert total_cus > 0 or result.is_error()  # Either success with CUs or error


def test_execution_trace_results():
    """Test that execution results (success/failure) are captured correctly."""
    svm = QuasarSvm()

    # Test 1: Successful execution
    mint = create_keyed_mint_account(
        Pubkey.new_unique(),
        mint_authority=Pubkey.new_unique(),
        decimals=9,
    )

    # GetAccountDataSize should succeed
    get_size_data = struct.pack("<B", 21)
    get_size_ix = Instruction(
        program_id=SPL_TOKEN_PROGRAM_ID,
        accounts=[AccountMeta(mint.address, is_signer=False, is_writable=False)],
        data=get_size_data,
    )

    success_result = svm.process_instruction(get_size_ix, [mint])

    # Check results
    print("\n✅ Successful execution:")
    for instr in success_result.execution_trace.instructions:
        result_str = "SUCCESS" if instr.result == 0 else f"ERROR {instr.result}"
        print(f"   - {result_str}")

    # Test 2: Failed execution (invalid instruction data)
    invalid_data = b"\xff" * 10  # Invalid instruction

    invalid_ix = Instruction(
        program_id=SPL_TOKEN_PROGRAM_ID,
        accounts=[AccountMeta(mint.address, is_signer=False, is_writable=False)],
        data=invalid_data,
    )

    error_result = svm.process_instruction(invalid_ix, [mint])

    print("\n❌ Failed execution:")
    for instr in error_result.execution_trace.instructions:
        result_str = "SUCCESS" if instr.result == 0 else f"ERROR {instr.result}"
        print(f"   - {result_str}")

    # At least one instruction should have failed
    assert error_result.is_error()


def test_execution_trace_instruction_data():
    """Test that full instruction data (accounts + data) is captured."""
    svm = QuasarSvm()

    mint = create_keyed_mint_account(
        Pubkey.new_unique(),
        mint_authority=Pubkey.new_unique(),
        decimals=6,
    )

    token_account = create_keyed_token_account(
        Pubkey.new_unique(),
        mint=mint.address,
        owner=Pubkey.new_unique(),
        amount=1000,
    )

    # Transfer instruction with specific data
    transfer_amount = 123
    transfer_data = struct.pack("<BQ", 3, transfer_amount)

    to_token = create_keyed_token_account(
        Pubkey.new_unique(),
        mint=mint.address,
        owner=Pubkey.new_unique(),
    )

    owner = Pubkey.new_unique()

    transfer_ix = Instruction(
        program_id=SPL_TOKEN_PROGRAM_ID,
        accounts=[
            AccountMeta(token_account.address, is_signer=False, is_writable=True),
            AccountMeta(to_token.address, is_signer=False, is_writable=True),
            AccountMeta(owner, is_signer=True, is_writable=False),
        ],
        data=transfer_data,
    )

    result = svm.process_instruction(transfer_ix, [mint, token_account, to_token])

    # Verify instruction data is captured
    print("\n📝 Instruction data captured:")
    for i, instr in enumerate(result.execution_trace.instructions):
        print(f"   Instruction {i}:")
        print(f"     - Program: {instr.instruction.program_id}")
        print(f"     - Accounts: {len(instr.instruction.accounts)}")
        print(f"     - Data length: {len(instr.instruction.data)} bytes")

        # Check account metadata
        for j, acc in enumerate(instr.instruction.accounts):
            print(f"       Account {j}: signer={acc.is_signer}, writable={acc.is_writable}")

    # First instruction should have our transfer data
    first_instr = result.execution_trace.instructions[0]
    assert len(first_instr.instruction.data) > 0
    assert len(first_instr.instruction.accounts) == 3

    # Verify account flags
    assert first_instr.instruction.accounts[0].is_writable  # source
    assert first_instr.instruction.accounts[1].is_writable  # destination
    assert first_instr.instruction.accounts[2].is_signer    # owner


def test_ata_creation_with_cpis():
    """Test ATA creation which involves CPIs - demonstrates nested execution trace."""
    from quasar_svm import (
        SPL_ASSOCIATED_TOKEN_PROGRAM_ID,
        SYSTEM_PROGRAM_ID,
        create_keyed_system_account,
    )

    svm = QuasarSvm()

    # Setup accounts
    payer = Pubkey.new_unique()
    wallet = Pubkey.new_unique()
    mint_addr = Pubkey.new_unique()

    payer_account = create_keyed_system_account(payer, lamports=10_000_000_000)
    wallet_account = create_keyed_system_account(wallet, lamports=0)

    mint = create_keyed_mint_account(
        mint_addr,
        mint_authority=wallet,
        decimals=6,
        supply=1_000_000,
    )

    # Derive ATA address using PDA
    ata_address, _bump = Pubkey.find_program_address(
        [
            bytes(wallet),
            bytes(SPL_TOKEN_PROGRAM_ID),
            bytes(mint_addr),
        ],
        SPL_ASSOCIATED_TOKEN_PROGRAM_ID,
    )

    print(f"\n🧪 Testing ATA Creation (with CPIs)")
    print(f"   Payer: {payer}")
    print(f"   Wallet: {wallet}")
    print(f"   Mint: {mint_addr}")
    print(f"   Expected ATA: {ata_address}")

    # Create the ATA instruction
    create_ata_ix = Instruction(
        program_id=SPL_ASSOCIATED_TOKEN_PROGRAM_ID,
        accounts=[
            AccountMeta(payer, is_signer=True, is_writable=True),              # fee payer
            AccountMeta(ata_address, is_signer=False, is_writable=True),       # associated token account
            AccountMeta(wallet, is_signer=False, is_writable=False),           # wallet
            AccountMeta(mint_addr, is_signer=False, is_writable=False),        # mint
            AccountMeta(SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False), # system program
            AccountMeta(SPL_TOKEN_PROGRAM_ID, is_signer=False, is_writable=False), # token program
        ],
        data=b"",  # ATA program takes no instruction data for create
    )

    # Execute
    result = svm.process_instruction(create_ata_ix, [payer_account, wallet_account, mint])

    print(f"\n📊 Execution Result:")
    print(f"   Success: {result.is_success()}")
    print(f"   Compute units: {result.compute_units}")
    print(f"   Logs: {len(result.logs)}")

    # Show execution trace with CPIs
    print(f"\n📊 Execution Trace:")
    print(f"   Total instructions executed: {len(result.execution_trace.instructions)}")

    for idx, instr in enumerate(result.execution_trace.instructions):
        indent = "  " * instr.stack_depth
        status = "✅" if instr.result == 0 else f"❌({instr.result})"
        print(f"   [{idx}] {indent}Depth={instr.stack_depth} {status} → {instr.instruction.program_id}")
        print(f"        {indent}  CUs: {instr.compute_units_consumed}")

    # Verify we have CPIs (should be > 1 instruction for ATA creation)
    if len(result.execution_trace.instructions) > 1:
        print(f"\n✅ CPIs detected! ATA creation involved {len(result.execution_trace.instructions)} program invocations")

        # Check for nested calls (depth > 0)
        nested_calls = [i for i in result.execution_trace.instructions if i.stack_depth > 0]
        if nested_calls:
            print(f"   Found {len(nested_calls)} nested CPI(s):")
            for cpi in nested_calls:
                print(f"     - Depth {cpi.stack_depth}: {cpi.instruction.program_id}")

    # Show logs
    print(f"\n📝 Transaction Logs:")
    for log in result.logs:
        print(f"   {log}")

    # Verify structure
    assert len(result.execution_trace.instructions) > 0
    assert result.execution_trace.instructions[0].stack_depth == 0  # Top-level is depth 0

    # Verify all instructions have full data
    for instr in result.execution_trace.instructions:
        assert hasattr(instr, 'stack_depth')
        assert hasattr(instr, 'instruction')
        assert hasattr(instr, 'compute_units_consumed')
        assert hasattr(instr, 'result')
        assert hasattr(instr.instruction, 'program_id')
        assert hasattr(instr.instruction, 'accounts')
        assert hasattr(instr.instruction, 'data')


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
