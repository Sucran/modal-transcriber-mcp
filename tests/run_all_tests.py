"""
Main test runner for all integration tests
主测试运行器，用于执行所有集成测试
"""

import pytest
import sys
import os
from pathlib import Path


def main():
    """Run all integration tests in sequence"""
    
    print("🚀 Starting Podcast MCP Gradio Integration Tests")
    print("=" * 60)
    
    # Get the tests directory
    tests_dir = Path(__file__).parent
    
    # Define test files in execution order
    test_files = [
        "test_01_podcast_download.py",
        "test_02_remote_transcription.py", 
        "test_03_transcription_file_management.py",
        "test_04_mp3_file_management.py",
        "test_05_real_world_integration.py"
    ]
    
    # Test results tracking
    results = {}
    overall_success = True
    
    for test_file in test_files:
        test_path = tests_dir / test_file
        
        print(f"\n📋 Running: {test_file}")
        print("-" * 40)
        
        if not test_path.exists():
            print(f"❌ Test file not found: {test_path}")
            results[test_file] = "NOT_FOUND"
            overall_success = False
            continue
        
        # Run the test file
        try:
            exit_code = pytest.main([
                str(test_path),
                "-v",  # verbose
                "-s",  # no capture (show print statements)
                "--tb=short",  # shorter traceback format
                "--disable-warnings"  # reduce noise
            ])
            
            if exit_code == 0:
                results[test_file] = "PASSED"
                print(f"✅ {test_file}: PASSED")
            else:
                results[test_file] = "FAILED"
                overall_success = False
                print(f"❌ {test_file}: FAILED (exit code: {exit_code})")
                
        except Exception as e:
            results[test_file] = f"EXCEPTION: {str(e)}"
            overall_success = False
            print(f"💥 {test_file}: EXCEPTION - {str(e)}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST EXECUTION SUMMARY")
    print("=" * 60)
    
    for test_file, result in results.items():
        status_icon = "✅" if result == "PASSED" else "❌"
        print(f"{status_icon} {test_file}: {result}")
    
    print(f"\n🏁 Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILURES DETECTED'}")
    
    if overall_success:
        print("🎉 All integration tests completed successfully!")
        print("✨ Your Podcast MCP Gradio application is ready for deployment!")
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        print("🔧 Check the specific test failures and fix any issues before deployment.")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 