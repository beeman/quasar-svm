# QuasarSVM Python Tests

This directory contains tests for the QuasarSVM Python bindings, demonstrating the execution trace functionality.

## Setup

1. **Build the native library:**
   ```bash
   cd ../../..  # Go to project root
   cargo build --release
   ```

2. **Install dependencies:**
   ```bash
   cd bindings/python
   pip install -e ".[dev]"
   ```

## Running Tests

Run all tests:
```bash
pytest tests/ -v
```

Run with detailed output:
```bash
pytest tests/ -v -s
```

Run a specific test:
```bash
pytest tests/test_execution_trace.py::test_basic_execution_trace -v -s
```

## Test Coverage

The test suite covers:

### test_simple.py
- **`test_execution_trace_exists`**: Verifies execution trace structure and basic fields
- **`test_execution_trace_structure`**: Validates all execution trace fields have correct types
- **`test_stack_depth_top_level`**: Confirms top-level instructions have stack_depth = 0
- **`test_instruction_data_captured`**: Verifies full instruction data capture

### test_execution_trace.py
- **`test_basic_execution_trace`**: Tests basic single-instruction execution with trace
- **`test_execution_trace_with_cpi`**: Demonstrates CPI tracking with ATA creation
- **`test_execution_trace_compute_units`**: Validates per-instruction compute unit tracking
- **`test_execution_trace_results`**: Tests success/failure result codes
- **`test_execution_trace_instruction_data`**: Verifies account metadata in instructions

## Expected Output

Each test produces detailed output showing:
- Stack depth for each instruction (0 = top-level, 1+ = CPI)
- Program ID that executed
- Compute units consumed
- Execution result (0 = success, non-zero = error code)
- Full instruction data (accounts with flags, data bytes)

Example output:
```
📊 Execution trace:
   0:   depth=0 program=TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA CUs=1234 ✅
   1:     depth=1 program=11111111111111111111111111111111 CUs=567 ✅
```

## Troubleshooting

**Import errors:**
- Make sure you've built the native library: `cargo build --release`
- Verify the dylib/so/dll is in the right location
- Check that solders is installed: `pip install solders>=0.27.0`

**Module not found:**
- Install the package in development mode: `pip install -e .`
- Make sure you're in the `bindings/python` directory

**Tests failing:**
- Some tests may fail if instruction behavior changes
- Check the logs output to understand what happened
- The tests are designed to demonstrate structure, not assert specific values
