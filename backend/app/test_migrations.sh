#!/bin/bash
# test_migrations.sh - Easy migration testing script

echo "🧪 Database Migration Test Suite"
echo "================================"

# Check if we're in the right directory
if [ ! -f "test_migrations.py" ]; then
    echo "❌ Error: Please run this script from the backend/app directory"
    echo "   Expected files: test_migrations.py, simple_migrations.py"
    exit 1
fi

# Check Python availability
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python not found. Please install Python 3.10+"
    exit 1
fi

# Install requirements if needed
if [ -f "requirements.txt" ]; then
    echo "📦 Installing requirements..."
    pip install -r requirements.txt > /dev/null 2>&1
fi

# Run the migration tests
echo "🚀 Running migration tests..."
echo ""

python run_migration_tests.py

TEST_RESULT=$?

echo ""
echo "================================"

if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ All migration tests passed!"
    echo "   Your database migrations are working correctly."
    echo "   It's safe to deploy these changes."
else
    echo "❌ Some migration tests failed!"
    echo "   Please review the output above and fix any issues."
    echo "   Do not deploy until all tests pass."
fi

echo ""
echo "💡 Tips:"
echo "   • Run 'pytest test_migrations.py -v' for detailed test output"
echo "   • Check MIGRATION_TESTING.md for troubleshooting guide"
echo "   • Test with actual production data before deployment"

exit $TEST_RESULT
