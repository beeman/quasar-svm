"""Simple tests demonstrating execution trace basics."""

import struct
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta

from quasar_svm import QuasarSvm, SPL_TOKEN_PROGRAM_ID, create_keyed_mint_account


def test_execution_trace_exists():
    """Verify execution trace is present in results."""
    svm = QuasarSvm()

    # Create a minimal mint account
    mint = create_keyed_mint_account(
        Pubkey.new_unique(),
        mint_authority=Pubkey.new_unique(),
    )

    # GetAccountDataSize instruction (simplest SPL token instruction)
    data = struct.pack("<B", 21)
    ix = Instruction(
        program_id=SPL_TOKEN_PROGRAM_ID,
        accounts=[AccountMeta(mint.address, is_signer=False, is_writable=False)],
        data=data,
    )

    result = svm.process_instruction(ix, [mint])

    # Basic assertions
    assert hasattr(result, 'execution_trace'), "execution_trace should exist"
    assert not hasattr(result, 'inner_instructions'), "inner_instructions should be removed"

    trace = result.execution_trace
    assert len(trace.instructions) > 0, "Should have at least one instruction"

    # Print trace info
    print("\n" + "="*60)
    print("EXECUTION TRACE")
    print("="*60)

    for i, instr in enumerate(trace.instructions):
        print(f"\nInstruction {i}:")
        print(f"  Stack Depth:      {instr.stack_depth}")
        print(f"  Program ID:       {instr.instruction.program_id}")
        print(f"  Accounts:         {len(instr.instruction.accounts)}")
        print(f"  Data Length:      {len(instr.instruction.data)} bytes")
        print(f"  Compute Units:    {instr.compute_units_consumed}")
        print(f"  Result:           {'✅ SUCCESS' if instr.result == 0 else f'❌ ERROR {instr.result}'}")

        if instr.instruction.accounts:
            print(f"  Account Details:")
            for j, acc in enumerate(instr.instruction.accounts):
                flags = []
                if acc.is_signer:
                    flags.append("signer")
                if acc.is_writable:
                    flags.append("writable")
                flag_str = ", ".join(flags) if flags else "read-only"
                print(f"    [{j}] {acc.pubkey} ({flag_str})")

    print("\n" + "="*60)
    print(f"Total instructions: {len(trace.instructions)}")
    print(f"Total compute units: {sum(i.compute_units_consumed for i in trace.instructions)}")
    print("="*60 + "\n")


def test_execution_trace_structure():
    """Verify execution trace has correct structure."""
    svm = QuasarSvm()

    mint = create_keyed_mint_account(Pubkey.new_unique(), mint_authority=Pubkey.new_unique())

    data = struct.pack("<B", 21)
    ix = Instruction(
        program_id=SPL_TOKEN_PROGRAM_ID,
        accounts=[AccountMeta(mint.address, is_signer=False, is_writable=False)],
        data=data,
    )

    result = svm.process_instruction(ix, [mint])

    # Verify structure
    first = result.execution_trace.instructions[0]

    # Check all fields exist and have correct types
    assert isinstance(first.stack_depth, int)
    assert first.stack_depth >= 0

    assert hasattr(first.instruction, 'program_id')
    assert hasattr(first.instruction, 'accounts')
    assert hasattr(first.instruction, 'data')

    assert isinstance(first.instruction.program_id, Pubkey)
    assert isinstance(first.instruction.accounts, list)
    assert isinstance(first.instruction.data, bytes)

    assert isinstance(first.compute_units_consumed, int)
    assert first.compute_units_consumed >= 0

    assert isinstance(first.result, int)
    assert first.result >= 0

    print("\n✅ All execution trace fields have correct types")


def test_stack_depth_top_level():
    """Verify top-level instructions have stack_depth = 0."""
    svm = QuasarSvm()

    mint = create_keyed_mint_account(Pubkey.new_unique(), mint_authority=Pubkey.new_unique())

    data = struct.pack("<B", 21)
    ix = Instruction(
        program_id=SPL_TOKEN_PROGRAM_ID,
        accounts=[AccountMeta(mint.address, is_signer=False, is_writable=False)],
        data=data,
    )

    result = svm.process_instruction(ix, [mint])

    # First instruction should always be stack depth 0
    first = result.execution_trace.instructions[0]
    assert first.stack_depth == 0, "Top-level instruction should have stack_depth = 0"

    print(f"\n✅ Top-level instruction has stack_depth = {first.stack_depth}")


def test_instruction_data_captured():
    """Verify instruction data is fully captured."""
    svm = QuasarSvm()

    mint = create_keyed_mint_account(Pubkey.new_unique(), mint_authority=Pubkey.new_unique())

    # Use specific data we can verify
    instruction_type = 21  # GetAccountDataSize
    data = struct.pack("<B", instruction_type)

    ix = Instruction(
        program_id=SPL_TOKEN_PROGRAM_ID,
        accounts=[AccountMeta(mint.address, is_signer=False, is_writable=False)],
        data=data,
    )

    result = svm.process_instruction(ix, [mint])

    first = result.execution_trace.instructions[0]

    # Verify program ID matches
    assert first.instruction.program_id == SPL_TOKEN_PROGRAM_ID

    # Verify account matches
    assert len(first.instruction.accounts) == 1
    assert first.instruction.accounts[0].pubkey == mint.address
    assert first.instruction.accounts[0].is_signer == False
    assert first.instruction.accounts[0].is_writable == False

    # Verify data matches
    assert len(first.instruction.data) == len(data)
    assert first.instruction.data == data

    print("\n✅ Instruction data fully captured:")
    print(f"   Program: {first.instruction.program_id}")
    print(f"   Accounts: {len(first.instruction.accounts)}")
    print(f"   Data: {first.instruction.data.hex()}")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
