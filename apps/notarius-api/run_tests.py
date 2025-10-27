#!/usr/bin/env python3
"""
Test runner script for Notarius API.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    print(f"Exit code: {result.returncode}")
    return result.returncode == 0


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run Notarius API tests")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "security", "performance", "e2e", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML test report"
    )
    parser.add_argument(
        "--junit-report",
        action="store_true",
        help="Generate JUnit XML report"
    )
    
    args = parser.parse_args()
    
    # Change to the correct directory
    os.chdir(Path(__file__).parent)
    
    # Build pytest command
    pytest_args = ["pytest"]
    
    # Add test path based on type
    if args.type == "all":
        pytest_args.append("tests/")
    else:
        pytest_args.append(f"tests/{args.type}/")
    
    # Add verbosity
    if args.verbose:
        pytest_args.append("-v")
    else:
        pytest_args.append("-q")
    
    # Add parallel execution
    if args.parallel:
        pytest_args.extend(["-n", "auto"])
    
    # Add fail fast
    if args.fail_fast:
        pytest_args.append("--maxfail=1")
    
    # Add coverage
    if args.coverage:
        pytest_args.extend([
            "--cov=apps",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml",
            "--cov-fail-under=95"
        ])
    
    # Add HTML report
    if args.html_report:
        pytest_args.extend([
            "--html=test-report.html",
            "--self-contained-html"
        ])
    
    # Add JUnit report
    if args.junit_report:
        pytest_args.extend([
            "--junitxml=test-results.xml"
        ])
    
    # Add markers for specific test types
    if args.type == "unit":
        pytest_args.extend(["-m", "unit"])
    elif args.type == "integration":
        pytest_args.extend(["-m", "integration"])
    elif args.type == "security":
        pytest_args.extend(["-m", "security"])
    elif args.type == "performance":
        pytest_args.extend(["-m", "performance"])
    elif args.type == "e2e":
        pytest_args.extend(["-m", "e2e"])
    
    # Add additional pytest options
    pytest_args.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings",
        "--durations=10"
    ])
    
    # Run the tests
    command = " ".join(pytest_args)
    success = run_command(command, f"Running {args.type} tests")
    
    if success:
        print(f"\n{'='*60}")
        print("✅ All tests passed!")
        print(f"{'='*60}")
        return 0
    else:
        print(f"\n{'='*60}")
        print("❌ Some tests failed!")
        print(f"{'='*60}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
