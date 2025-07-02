#!/usr/bin/env python3
"""
Firebase Logging Test Script
Run this to test Firebase logging functionality in your app
"""

import sys
import os

# Add the utils directory to path so we can import the firebase logger
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))

try:
    from firebase_logger import test_firebase_logging, log_info, log_warn, log_error, get_firebase_status
    
    def main():
        print("🚀 Starting Firebase Logging Test")
        
        # Run comprehensive diagnostic
        test_firebase_logging()
        
        # Test different log levels
        print("📝 Testing different log levels:")
        log_info("Test INFO message from Python", {"test": "info_level"})
        log_warn("Test WARNING message from Python", {"test": "warn_level"})
        log_error("Test ERROR message from Python", {"test": "error_level"})
        
        # Show final status
        status = get_firebase_status()
        print(f"\n📊 Final Status: {status}")
        
        print("✅ Test completed - check your Firebase console and app logs")

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ Failed to import firebase_logger: {e}")
    print("Make sure you're running this from the correct directory")
