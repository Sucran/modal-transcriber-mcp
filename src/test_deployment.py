#!/usr/bin/env python3
"""
Test script to verify deployment configuration
"""

import os
import sys

def test_local_mode():
    """Test local mode configuration"""
    print("🧪 Testing LOCAL mode configuration...")
    
    # Set local mode
    os.environ["DEPLOYMENT_MODE"] = "local"
    
    try:
        from config import is_local_mode, is_modal_mode, get_cache_dir
        
        assert is_local_mode() == True, "Should be in local mode"
        assert is_modal_mode() == False, "Should not be in modal mode"
        
        cache_dir = get_cache_dir()
        assert "gradio_mcp_cache" in cache_dir, f"Cache dir should be local: {cache_dir}"
        
        print("✅ Local mode configuration OK")
        return True
        
    except Exception as e:
        print(f"❌ Local mode test failed: {e}")
        return False

def test_modal_mode():
    """Test modal mode configuration"""
    print("🧪 Testing MODAL mode configuration...")
    
    # Set modal mode
    os.environ["DEPLOYMENT_MODE"] = "modal"
    
    try:
        # Clear config module cache to reload with new env var
        if 'config' in sys.modules:
            del sys.modules['config']
        
        from config import is_local_mode, is_modal_mode, get_cache_dir
        
        assert is_local_mode() == False, "Should not be in local mode"
        assert is_modal_mode() == True, "Should be in modal mode"
        
        cache_dir = get_cache_dir()
        assert cache_dir == "/root/cache", f"Cache dir should be modal: {cache_dir}"
        
        print("✅ Modal mode configuration OK")
        return True
        
    except Exception as e:
        print(f"❌ Modal mode test failed: {e}")
        return False

def test_gpu_adapters():
    """Test GPU adapters"""
    print("🧪 Testing GPU adapters...")
    
    try:
        from gpu_adapters import transcribe_audio_adaptive_sync
        
        # This should not crash, even if endpoints are not configured
        result = transcribe_audio_adaptive_sync(
            "test_file.mp3", 
            "turbo", 
            None, 
            "srt", 
            False
        )
        
        # Should return error result but not crash
        assert "processing_status" in result or "error_message" in result, "Should return valid result structure"
        
        print("✅ GPU adapters OK")
        return True
        
    except Exception as e:
        print(f"❌ GPU adapters test failed: {e}")
        return False

def test_imports():
    """Test all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        # Test config imports
        from config import DeploymentMode, get_deployment_mode
        
        # Test MCP tools imports
        from mcp_tools import get_mcp_server
        
        # Test app imports (should work in both modes)
        from app import create_app, main, get_app
        
        print("✅ All imports OK")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_hf_spaces_mode():
    """Test Hugging Face Spaces mode"""
    print("🧪 Testing HF Spaces mode...")
    
    try:
        # Clear deployment mode to simulate HF Spaces
        old_mode = os.environ.get("DEPLOYMENT_MODE")
        if "DEPLOYMENT_MODE" in os.environ:
            del os.environ["DEPLOYMENT_MODE"]
        
        # Clear config module cache
        if 'config' in sys.modules:
            del sys.modules['config']
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import get_app
        
        app = get_app()
        assert app is not None, "Should create app for HF Spaces"
        
        # Restore environment
        if old_mode:
            os.environ["DEPLOYMENT_MODE"] = old_mode
        
        print("✅ HF Spaces mode OK")
        return True
        
    except Exception as e:
        print(f"❌ HF Spaces test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running deployment configuration tests...\n")
    
    tests = [
        test_imports,
        test_local_mode,
        test_modal_mode,
        test_hf_spaces_mode,
        test_gpu_adapters,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
        print()
    
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Deployment configuration is ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 