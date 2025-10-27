#!/usr/bin/env python3
"""
Comprehensive test runner for the entire Notarius monorepo.
"""
import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


def run_command(command, cwd=None, capture_output=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out after 5 minutes"
    except Exception as e:
        return -1, "", str(e)


def run_notarius_api_tests():
    """Run Notarius API tests."""
    print("🧪 Running Notarius API tests...")
    
    # Change to notarius-api directory
    notarius_api_dir = Path("apps/notarius-api")
    if not notarius_api_dir.exists():
        print("❌ Notarius API directory not found")
        return False
    
    # Run Django tests
    returncode, stdout, stderr = run_command(
        "python manage.py test --verbosity=2",
        cwd=notarius_api_dir
    )
    
    if returncode == 0:
        print("✅ Notarius API tests passed")
        return True
    else:
        print("❌ Notarius API tests failed")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False


def run_lexnode_api_tests():
    """Run LexNode API tests."""
    print("🧪 Running LexNode API tests...")
    
    # Change to lexnode-api directory
    lexnode_api_dir = Path("apps/lexnode-api")
    if not lexnode_api_dir.exists():
        print("❌ LexNode API directory not found")
        return False
    
    # Run FastAPI tests
    returncode, stdout, stderr = run_command(
        "pytest tests/ -v",
        cwd=lexnode_api_dir
    )
    
    if returncode == 0:
        print("✅ LexNode API tests passed")
        return True
    else:
        print("❌ LexNode API tests failed")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False


def run_intent_engine_tests():
    """Run Intent Engine tests."""
    print("🧪 Running Intent Engine tests...")
    
    # Change to intent-engine directory
    intent_engine_dir = Path("apps/intent-engine")
    if not intent_engine_dir.exists():
        print("❌ Intent Engine directory not found")
        return False
    
    # Run FastAPI tests
    returncode, stdout, stderr = run_command(
        "pytest tests/ -v",
        cwd=intent_engine_dir
    )
    
    if returncode == 0:
        print("✅ Intent Engine tests passed")
        return True
    else:
        print("❌ Intent Engine tests failed")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False


def run_pii_vault_tests():
    """Run PII Vault tests."""
    print("🧪 Running PII Vault tests...")
    
    # Change to pii-vault directory
    pii_vault_dir = Path("apps/pii-vault")
    if not pii_vault_dir.exists():
        print("❌ PII Vault directory not found")
        return False
    
    # Run FastAPI tests
    returncode, stdout, stderr = run_command(
        "pytest tests/ -v",
        cwd=pii_vault_dir
    )
    
    if returncode == 0:
        print("✅ PII Vault tests passed")
        return True
    else:
        print("❌ PII Vault tests failed")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False


def run_packages_tests():
    """Run shared packages tests."""
    print("🧪 Running shared packages tests...")
    
    packages_dir = Path("packages")
    if not packages_dir.exists():
        print("❌ Packages directory not found")
        return False
    
    # Run tests for each package
    packages = ["core", "observability", "pii"]
    all_passed = True
    
    for package in packages:
        package_dir = packages_dir / package
        if package_dir.exists():
            print(f"  Testing {package} package...")
            returncode, stdout, stderr = run_command(
                "pytest tests/ -v",
                cwd=package_dir
            )
            
            if returncode == 0:
                print(f"  ✅ {package} package tests passed")
            else:
                print(f"  ❌ {package} package tests failed")
                print(f"  STDOUT: {stdout}")
                print(f"  STDERR: {stderr}")
                all_passed = False
        else:
            print(f"  ⚠️  {package} package directory not found")
    
    return all_passed


def run_integration_tests():
    """Run integration tests."""
    print("🧪 Running integration tests...")
    
    # Change to root directory
    root_dir = Path(".")
    
    # Run integration tests
    returncode, stdout, stderr = run_command(
        "pytest tests/test_integration.py -v",
        cwd=root_dir
    )
    
    if returncode == 0:
        print("✅ Integration tests passed")
        return True
    else:
        print("❌ Integration tests failed")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False


def run_e2e_tests():
    """Run end-to-end tests."""
    print("🧪 Running end-to-end tests...")
    
    # Change to root directory
    root_dir = Path(".")
    
    # Run E2E tests
    returncode, stdout, stderr = run_command(
        "pytest tests/test_e2e.py -v",
        cwd=root_dir
    )
    
    if returncode == 0:
        print("✅ End-to-end tests passed")
        return True
    else:
        print("❌ End-to-end tests failed")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False


def run_security_tests():
    """Run security tests."""
    print("🧪 Running security tests...")
    
    # Change to notarius-api directory
    notarius_api_dir = Path("apps/notarius-api")
    if not notarius_api_dir.exists():
        print("❌ Notarius API directory not found")
        return False
    
    # Run security tests
    returncode, stdout, stderr = run_command(
        "pytest tests/security/ -v",
        cwd=notarius_api_dir
    )
    
    if returncode == 0:
        print("✅ Security tests passed")
        return True
    else:
        print("❌ Security tests failed")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False


def run_performance_tests():
    """Run performance tests."""
    print("🧪 Running performance tests...")
    
    # Change to notarius-api directory
    notarius_api_dir = Path("apps/notarius-api")
    if not notarius_api_dir.exists():
        print("❌ Notarius API directory not found")
        return False
    
    # Run performance tests
    returncode, stdout, stderr = run_command(
        "pytest tests/performance/ -v",
        cwd=notarius_api_dir
    )
    
    if returncode == 0:
        print("✅ Performance tests passed")
        return True
    else:
        print("❌ Performance tests failed")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False


def run_linting():
    """Run linting checks."""
    print("🔍 Running linting checks...")
    
    # Change to root directory
    root_dir = Path(".")
    
    # Run flake8
    returncode, stdout, stderr = run_command(
        "flake8 . --exclude=venv,node_modules,.git",
        cwd=root_dir
    )
    
    if returncode == 0:
        print("✅ Linting checks passed")
        return True
    else:
        print("❌ Linting checks failed")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False


def run_type_checking():
    """Run type checking."""
    print("🔍 Running type checking...")
    
    # Change to root directory
    root_dir = Path(".")
    
    # Run mypy
    returncode, stdout, stderr = run_command(
        "mypy . --ignore-missing-imports",
        cwd=root_dir
    )
    
    if returncode == 0:
        print("✅ Type checking passed")
        return True
    else:
        print("❌ Type checking failed")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run comprehensive tests for Notarius monorepo")
    parser.add_argument("--services", nargs="+", 
                       choices=["notarius", "lexnode", "intent-engine", "pii-vault", "packages"],
                       help="Specific services to test")
    parser.add_argument("--test-types", nargs="+",
                       choices=["unit", "integration", "e2e", "security", "performance", "linting", "type-checking"],
                       help="Specific test types to run")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only (unit + linting)")
    
    args = parser.parse_args()
    
    # Determine what to run
    if args.all:
        services = ["notarius", "lexnode", "intent-engine", "pii-vault", "packages"]
        test_types = ["unit", "integration", "e2e", "security", "performance", "linting", "type-checking"]
    elif args.quick:
        services = ["notarius", "lexnode", "intent-engine", "pii-vault", "packages"]
        test_types = ["unit", "linting"]
    else:
        services = args.services or ["notarius", "lexnode", "intent-engine", "pii-vault", "packages"]
        test_types = args.test_types or ["unit", "integration", "e2e", "security", "performance", "linting", "type-checking"]
    
    print("🚀 Starting comprehensive test run for Notarius monorepo")
    print(f"Services: {', '.join(services)}")
    print(f"Test types: {', '.join(test_types)}")
    print("=" * 60)
    
    start_time = time.time()
    results = {}
    
    # Run service tests
    if "notarius" in services and "unit" in test_types:
        results["notarius"] = run_notarius_api_tests()
    
    if "lexnode" in services and "unit" in test_types:
        results["lexnode"] = run_lexnode_api_tests()
    
    if "intent-engine" in services and "unit" in test_types:
        results["intent-engine"] = run_intent_engine_tests()
    
    if "pii-vault" in services and "unit" in test_types:
        results["pii-vault"] = run_pii_vault_tests()
    
    if "packages" in services and "unit" in test_types:
        results["packages"] = run_packages_tests()
    
    # Run integration tests
    if "integration" in test_types:
        results["integration"] = run_integration_tests()
    
    # Run E2E tests
    if "e2e" in test_types:
        results["e2e"] = run_e2e_tests()
    
    # Run security tests
    if "security" in test_types:
        results["security"] = run_security_tests()
    
    # Run performance tests
    if "performance" in test_types:
        results["performance"] = run_performance_tests()
    
    # Run linting
    if "linting" in test_types:
        results["linting"] = run_linting()
    
    # Run type checking
    if "type-checking" in test_types:
        results["type-checking"] = run_type_checking()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Print summary
    print("=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
