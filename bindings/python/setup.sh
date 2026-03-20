#!/bin/bash
# Setup script for Python bindings development and testing

set -e  # Exit on error

echo "🔧 QuasarSVM Python Bindings - Setup & Test"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run from bindings/python directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected: .../quasar-svm/bindings/python"
    exit 1
fi

# Step 1: Build native library
echo "📦 Step 1: Building native library..."
cd ../..
cargo build --release
if [ $? -eq 0 ]; then
    echo "   ✅ Native library built successfully"
else
    echo "   ❌ Failed to build native library"
    exit 1
fi
cd bindings/python

# Step 2: Check for virtual environment
if [ ! -d ".venv" ]; then
    echo ""
    echo "🐍 Step 2: Creating virtual environment..."
    python3 -m venv .venv
    echo "   ✅ Virtual environment created"
else
    echo ""
    echo "🐍 Step 2: Virtual environment already exists"
fi

# Step 3: Activate virtual environment
echo ""
echo "🔌 Step 3: Activating virtual environment..."
source .venv/bin/activate
echo "   ✅ Virtual environment activated"

# Step 4: Upgrade pip
echo ""
echo "📦 Step 4: Upgrading pip..."
pip install --upgrade pip -q
echo "   ✅ pip upgraded"

# Step 5: Install package
echo ""
echo "📦 Step 5: Installing package with dev dependencies..."
pip install -e ".[dev]" -q
echo "   ✅ Package installed"

# Step 6: Verify installation
echo ""
echo "🧪 Step 6: Verifying installation..."
python -c "from quasar_svm import QuasarSvm; print('   ✅ Import successful')"

# Step 7: Run tests
echo ""
echo "🧪 Step 7: Running tests..."
echo "=========================================="
echo ""

pytest tests/ -v -s

# Done
echo ""
echo "=========================================="
echo "✨ All done!"
echo ""
echo "To manually activate the virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "To run tests again:"
echo "   pytest tests/ -v -s"
echo ""
echo "To deactivate when done:"
echo "   deactivate"
echo ""
