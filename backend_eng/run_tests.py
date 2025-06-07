import os
import sys
import pytest
import time

def run_tests():
    """Run all tests and report results"""
    print("\n===== RUNNING BACKEND TESTS =====")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=================================\n")
    
    # Make sure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the tests
    test_args = [
        "-v",                  # Verbose output
        "--tb=short",          # Shorter traceback format
        "-n", "auto",          # 使用多進程並行執行測試 (需要 pytest-xdist)
        "--dist=loadfile",     # 按檔案分配測試，提高效率
        "app/tests/test_models.py",  # Model tests
        "app/tests/test_api.py",     # API tests
        "app/tests/test_crud.py",    # CRUD tests
        "app/tests/test_file_utils.py",  # File utils tests
        "app/tests/test_database.py",    # Database tests
        "app/tests/test_coverage.py",    # Coverage tests
        "--cov=app",           # Coverage report
        "--cov-report=html",   # HTML coverage report
        "--cov-report=term-missing",  # Terminal report with missing lines
    ]
    
    # Run the tests and capture the result
    result = pytest.main(test_args)
    
    # Print summary
    if result == 0:
        print("\n All tests passed successfully!")
        print("\n HTML coverage report generated in the 'htmlcov' directory.")
        print(" Open 'htmlcov/index.html' in a browser to view the report.")
    else:
        print("\n Some tests failed. Please fix the issues and run the tests again.")
    
    return result

if __name__ == "__main__":
    sys.exit(run_tests())
