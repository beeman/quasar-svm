# Python Test Setup

## Quick Start (macOS with externally-managed Python)

```bash
# 1. Navigate to the Python bindings directory
cd bindings/python

# 2. Create a virtual environment
python3 -m venv .venv

# 3. Activate the virtual environment
source .venv/bin/activate

# 4. Upgrade pip
pip install --upgrade pip

# 5. Install the package with dev dependencies
pip install -e ".[dev]"

# 6. Verify installation
python -c "from quasar_svm import QuasarSvm; print('✅ Import successful')"

# 7. Run the tests
pytest tests/ -v -s
```

## Step-by-Step Explanation

### 1. Create Virtual Environment
```bash
python3 -m venv .venv
```
This creates a `.venv` directory containing an isolated Python environment.

### 2. Activate Virtual Environment
```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```
Your prompt should change to show `(.venv)` at the beginning.

### 3. Install Package
```bash
pip install -e ".[dev]"
```
- `-e` = editable mode (changes to code are reflected immediately)
- `[dev]` = includes development dependencies (pytest, black, mypy, ruff)

### 4. Run Tests

All tests:
```bash
pytest tests/ -v -s
```

Simple tests only:
```bash
pytest tests/test_simple.py -v -s
```

Single test:
```bash
pytest tests/test_simple.py::test_execution_trace_exists -v -s
```

### 5. Deactivate When Done
```bash
deactivate
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'solders'"
```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### "ModuleNotFoundError: No module named 'quasar_svm'"
```bash
# Make sure you're in bindings/python directory
pwd  # Should show .../quasar-svm/bindings/python

# Install in editable mode
pip install -e .
```

### Tests fail with library loading errors
```bash
# Build the native library first
cd ../../  # Go to project root
cargo build --release
cd bindings/python

# Verify the library exists
ls -la ../../target/release/libquasar_svm.*
```

### "Cannot find module" errors
```bash
# Reinstall everything
pip uninstall quasar-svm -y
pip install -e ".[dev]"
```

## VSCode Integration

If using VSCode, select the virtual environment:
1. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "Python: Select Interpreter"
3. Choose `.venv/bin/python`

## Alternative: Using pipx

If you prefer not to manage virtual environments manually:

```bash
# Install pipx (if not already installed)
brew install pipx

# Install the package
pipx install -e "bindings/python[dev]"

# Run tests
cd bindings/python
pytest tests/ -v -s
```
