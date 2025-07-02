"""
Firebase logging utility for Python backend
Safely logs to Firebase through Flutter bridge when available
"""
import traceback
import os
from typing import Dict, Any, Optional

# Debug flag - set to False to reduce log noise once bridge is confirmed working
FIREBASE_LOGGER_DEBUG = False  # Bridge is working, reduce noise

# Release mode logging - keep console logging for important messages
FIREBASE_LOGGER_CONSOLE_LOGGING = True

class FirebaseLogger:
    """
    Logger that sends logs to Firebase through Flutter bridge
    Fails silently if bridge is not available (e.g., during testing)
    """
    
    def __init__(self):
        self._bridge_available = self._check_bridge_availability()
        self._activity = None
        
        if FIREBASE_LOGGER_DEBUG:
            print(f"[FIREBASE_LOGGER] Bridge available: {self._bridge_available}")
        
        if self._bridge_available:
            try:
                from com.chaquo.python import Python
                python = Python.getInstance()
                
                # Try multiple ways to get the activity
                if FIREBASE_LOGGER_DEBUG:
                    print("[FIREBASE_LOGGER] Attempting to get activity...")
                
                # Method 1: Check __main__ module
                main_module = python.getModule("__main__")
                if hasattr(main_module, 'activity'):
                    self._activity = main_module.activity
                    if FIREBASE_LOGGER_DEBUG:
                        print(f"[FIREBASE_LOGGER] Activity found in __main__: {self._activity}")
                else:
                    if FIREBASE_LOGGER_DEBUG:
                        print("[FIREBASE_LOGGER] No activity attribute in __main__ module")
                    
                    # Method 2: Check if we can get activity from current context
                    try:
                        # This is a more flexible approach - activity might be set later
                        if FIREBASE_LOGGER_DEBUG:
                            print("[FIREBASE_LOGGER] Activity not found in __main__, will try to get it during logging")
                        # Don't disable bridge availability yet - activity might be set later
                    except Exception as e2:
                        if FIREBASE_LOGGER_DEBUG:
                            print(f"[FIREBASE_LOGGER] Could not find activity: {e2}")
                        
            except Exception as e:
                if FIREBASE_LOGGER_DEBUG:
                    print(f"[FIREBASE_LOGGER] Failed to initialize Python instance: {e}")
                self._bridge_available = False
    
    def _check_bridge_availability(self) -> bool:
        """Check if we're running in a Flutter/Chaquopy environment"""
        if FIREBASE_LOGGER_DEBUG:
            print("[FIREBASE_LOGGER] Checking bridge availability...")
        
        # Method 1: Try to import Chaquopy
        chaquopy_available = False
        try:
            import com.chaquo.python
            chaquopy_available = True
            if FIREBASE_LOGGER_DEBUG:
                print("[FIREBASE_LOGGER] ✅ Chaquopy import successful")
        except ImportError as e:
            if FIREBASE_LOGGER_DEBUG:
                print(f"[FIREBASE_LOGGER] ❌ Chaquopy import failed: {e}")
        
        # Method 2: Check Python environment indicators
        python_indicators = []
        if hasattr(__builtins__, '__CHAQUOPY__'):
            python_indicators.append("__CHAQUOPY__ builtin found")
        if 'ANDROID_DATA' in os.environ:
            python_indicators.append("ANDROID_DATA environment variable found")
        if 'ANDROID_ROOT' in os.environ:
            python_indicators.append("ANDROID_ROOT environment variable found")
        
        if FIREBASE_LOGGER_DEBUG:
            print(f"[FIREBASE_LOGGER] Python environment indicators: {python_indicators}")
        
        # Method 3: Check FLUTTER_ENV
        flutter_env = os.environ.get('FLUTTER_ENV') == 'true'
        if FIREBASE_LOGGER_DEBUG:
            print(f"[FIREBASE_LOGGER] FLUTTER_ENV: {os.environ.get('FLUTTER_ENV', 'not set')}")
            print(f"[FIREBASE_LOGGER] Flutter env flag: {flutter_env}")
        
        # Method 4: Check for other Android/Java indicators
        java_available = False
        try:
            import sys
            if 'java' in sys.platform.lower() or any('android' in str(p).lower() for p in sys.path):
                java_available = True
                if FIREBASE_LOGGER_DEBUG:
                    print("[FIREBASE_LOGGER] ✅ Java/Android platform indicators found")
        except Exception:
            pass
        
        # Determine availability - be more permissive
        is_available = chaquopy_available or len(python_indicators) > 0 or flutter_env or java_available
        
        if FIREBASE_LOGGER_DEBUG:
            print(f"[FIREBASE_LOGGER] Final bridge availability decision: {is_available}")
            print(f"[FIREBASE_LOGGER] - Chaquopy: {chaquopy_available}")
            print(f"[FIREBASE_LOGGER] - Android indicators: {len(python_indicators) > 0}")
            print(f"[FIREBASE_LOGGER] - Flutter env: {flutter_env}")
            print(f"[FIREBASE_LOGGER] - Java platform: {java_available}")
        
        return is_available
    
    def _log_to_bridge(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Internal method to send log to Flutter through bridge"""
        # Always log to console for debugging
        console_msg = f"🔥 [FIREBASE-{level}] {message}"
        if metadata:
            console_msg += f" | Metadata: {metadata}"
        print(console_msg)
        
        if FIREBASE_LOGGER_DEBUG:
            print(f"🚀 [FIREBASE-BRIDGE] Attempting to send {level} log to Firebase...")
            print(f"🚀 [FIREBASE-BRIDGE] Message: {message}")
            if metadata:
                print(f"🚀 [FIREBASE-BRIDGE] Metadata: {metadata}")
        
        if not self._bridge_available:
            if FIREBASE_LOGGER_DEBUG or FIREBASE_LOGGER_CONSOLE_LOGGING:
                print("❌ [FIREBASE-BRIDGE] Bridge not available - log will NOT be sent to Firebase")
                print(f"   Bridge available: {self._bridge_available}")
                print(f"   Activity: {self._activity}")
            return
            
        # Try to get activity if we don't have one yet
        if not self._activity:
            if FIREBASE_LOGGER_DEBUG:
                print("🔧 [FIREBASE-BRIDGE] No activity cached, trying to get it now...")
            try:
                from com.chaquo.python import Python
                python = Python.getInstance()
                main_module = python.getModule("__main__")
                if hasattr(main_module, 'activity'):
                    self._activity = main_module.activity
                    if FIREBASE_LOGGER_DEBUG:
                        print(f"🔧 [FIREBASE-BRIDGE] Found activity: {self._activity}")
                else:
                    if FIREBASE_LOGGER_DEBUG or FIREBASE_LOGGER_CONSOLE_LOGGING:
                        print("❌ [FIREBASE-BRIDGE] Still no activity found in __main__")
                    # Try alternative method - check if activity was set via environment
                    try:
                        # Sometimes the activity is available through different means
                        if hasattr(main_module, '__dict__') and 'activity' in main_module.__dict__:
                            self._activity = main_module.__dict__['activity']
                            if FIREBASE_LOGGER_DEBUG:
                                print(f"🔧 [FIREBASE-BRIDGE] Found activity via __dict__: {self._activity}")
                        else:
                            if FIREBASE_LOGGER_CONSOLE_LOGGING:
                                print("⚠️ [FIREBASE-BRIDGE] No activity found - Firebase logging will not work")
                            return
                    except Exception as alt_e:
                        if FIREBASE_LOGGER_CONSOLE_LOGGING:
                            print(f"⚠️ [FIREBASE-BRIDGE] Alternative activity lookup failed: {alt_e}")
                        return
            except Exception as e:
                if FIREBASE_LOGGER_DEBUG or FIREBASE_LOGGER_CONSOLE_LOGGING:
                    print(f"❌ [FIREBASE-BRIDGE] Failed to get activity: {e}")
                return
            
        try:
            if FIREBASE_LOGGER_DEBUG:
                print("🔥 [FIREBASE-BRIDGE] Bridge is available - converting metadata for Java...")
            # Convert metadata to Java-compatible format
            if metadata:
                # Create a proper Java HashMap
                from java.util import HashMap
                java_metadata = HashMap()
                for key, value in metadata.items():
                    # Convert all values to strings for Java compatibility
                    java_metadata.put(str(key), str(value))
                if FIREBASE_LOGGER_DEBUG:
                    print(f"🔥 [FIREBASE-BRIDGE] Converted {len(metadata)} metadata items to Java HashMap")
            else:
                from java.util import HashMap
                java_metadata = HashMap()
                if FIREBASE_LOGGER_DEBUG:
                    print("🔥 [FIREBASE-BRIDGE] Created empty Java HashMap for metadata")
            
            if FIREBASE_LOGGER_DEBUG:
                print(f"🔥 [FIREBASE-BRIDGE] Calling activity.logToFirebase({level}, {message}, HashMap with {java_metadata.size()} items)")
            # Call the logToFirebase method on the activity
            self._activity.logToFirebase(level, message, java_metadata)
            if FIREBASE_LOGGER_DEBUG or FIREBASE_LOGGER_CONSOLE_LOGGING:
                print("✅ [FIREBASE-BRIDGE] Successfully sent log to Firebase through bridge!")
            
        except Exception as e:
            # Print debug info to help diagnose the issue
            if FIREBASE_LOGGER_DEBUG or FIREBASE_LOGGER_CONSOLE_LOGGING:
                print(f"❌ [BRIDGE_ERROR] Failed to log to Firebase: {e}")
                print(f"[BRIDGE_ERROR] Bridge available: {self._bridge_available}")
                print(f"[BRIDGE_ERROR] Activity: {self._activity}")
                print(f"[BRIDGE_ERROR] Activity type: {type(self._activity)}")
                try:
                    print(f"[BRIDGE_ERROR] Activity methods: {dir(self._activity)}")
                except:
                    print("[BRIDGE_ERROR] Could not list activity methods")
            # Silent fail - don't let logging errors crash the app
    
    def info(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log info message"""
        print(f"[INFO] {message}")  # Always print to console
        if FIREBASE_LOGGER_DEBUG:
            print(f"📝 [FIREBASE-LOGGER] Preparing to send INFO log to bridge...")
        self._log_to_bridge("INFO", message, metadata)
        if FIREBASE_LOGGER_DEBUG:
            print(f"📝 [FIREBASE-LOGGER] INFO log processing complete")
    
    def warn(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        print(f"[WARN] {message}")
        if FIREBASE_LOGGER_DEBUG:
            print(f"⚠️ [FIREBASE-LOGGER] Preparing to send WARN log to bridge...")
        self._log_to_bridge("WARN", message, metadata)
        if FIREBASE_LOGGER_DEBUG:
            print(f"⚠️ [FIREBASE-LOGGER] WARN log processing complete")
    
    def error(self, message: str, metadata: Optional[Dict[str, Any]] = None, exception: Optional[Exception] = None):
        """Log error message"""
        print(f"[ERROR] {message}")
        if FIREBASE_LOGGER_DEBUG:
            print(f"❌ [FIREBASE-LOGGER] Preparing to send ERROR log to bridge...")
        
        # Add exception details to metadata if provided
        if exception and metadata is None:
            metadata = {}
        
        if exception:
            metadata = metadata or {}
            metadata.update({
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "stack_trace": traceback.format_exc()
            })
        
        self._log_to_bridge("ERROR", message, metadata)
        if FIREBASE_LOGGER_DEBUG:
            print(f"❌ [FIREBASE-LOGGER] ERROR log processing complete")
    
    def debug(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log debug message"""
        print(f"[DEBUG] {message}")
        if FIREBASE_LOGGER_DEBUG:
            print(f"🐛 [FIREBASE-LOGGER] Preparing to send DEBUG log to bridge...")
        self._log_to_bridge("DEBUG", message, metadata)
        if FIREBASE_LOGGER_DEBUG:
            print(f"🐛 [FIREBASE-LOGGER] DEBUG log processing complete")
    
    def set_activity(self, activity):
        """Manually set the activity object for Firebase logging"""
        self._activity = activity
        if FIREBASE_LOGGER_DEBUG:
            print(f"[FIREBASE_LOGGER] Activity manually set: {activity}")
        if activity:
            self._bridge_available = True
            if FIREBASE_LOGGER_DEBUG:
                print("[FIREBASE_LOGGER] Bridge now available with manual activity")
    
    def get_bridge_status(self):
        """Get current bridge status for debugging"""
        return {
            "bridge_available": self._bridge_available,
            "activity": self._activity,
            "has_activity": self._activity is not None
        }
    
    def force_bridge_availability(self, force_available: bool = True):
        """Force bridge availability for testing purposes"""
        self._bridge_available = force_available
        if FIREBASE_LOGGER_DEBUG:
            print(f"[FIREBASE_LOGGER] Bridge availability FORCED to: {force_available}")
        if force_available:
            if FIREBASE_LOGGER_DEBUG:
                print("[FIREBASE_LOGGER] WARNING: Bridge forced ON - logs will attempt to send even without proper setup")
        else:
            if FIREBASE_LOGGER_DEBUG:
                print("[FIREBASE_LOGGER] Bridge forced OFF - logs will not be sent")

# Global logger instance
firebase_logger = FirebaseLogger()

# Convenience functions
def log_info(message: str, metadata: Optional[Dict[str, Any]] = None):
    firebase_logger.info(message, metadata)

def log_warn(message: str, metadata: Optional[Dict[str, Any]] = None):
    firebase_logger.warn(message, metadata)

def log_error(message: str, metadata: Optional[Dict[str, Any]] = None, exception: Optional[Exception] = None):
    firebase_logger.error(message, metadata, exception)

def log_debug(message: str, metadata: Optional[Dict[str, Any]] = None):
    firebase_logger.debug(message, metadata)

def force_firebase_bridge(force_available: bool = True):
    """Force Firebase bridge availability for testing"""
    firebase_logger.force_bridge_availability(force_available)

def set_firebase_activity(activity):
    """Set Firebase activity for manual bridge setup"""
    firebase_logger.set_activity(activity)

def get_firebase_status():
    """Get Firebase bridge status for debugging"""
    return firebase_logger.get_bridge_status()

def test_firebase_logging():
    """Test Firebase logging functionality and print detailed diagnostics"""
    print("\n" + "="*60)
    print("🧪 FIREBASE LOGGING DIAGNOSTIC TEST")
    print("="*60)
    
    # Get current status
    status = get_firebase_status()
    print(f"📊 Current Firebase Status:")
    print(f"   Bridge Available: {status['bridge_available']}")
    print(f"   Has Activity: {status['has_activity']}")
    print(f"   Activity: {status['activity']}")
    
    # Test environment detection
    print(f"\n🌍 Environment Detection:")
    print(f"   FLUTTER_ENV: {os.environ.get('FLUTTER_ENV', 'not set')}")
    print(f"   ANDROID_DATA: {'set' if 'ANDROID_DATA' in os.environ else 'not set'}")
    print(f"   ANDROID_ROOT: {'set' if 'ANDROID_ROOT' in os.environ else 'not set'}")
    
    # Test Chaquopy availability
    try:
        import com.chaquo.python
        print(f"   Chaquopy Import: ✅ SUCCESS")
        try:
            from com.chaquo.python import Python
            python = Python.getInstance()
            print(f"   Python Instance: ✅ SUCCESS")
            
            main_module = python.getModule("__main__")
            print(f"   Main Module: ✅ SUCCESS")
            
            if hasattr(main_module, 'activity'):
                activity = main_module.activity
                print(f"   Activity Found: ✅ SUCCESS - {activity}")
                print(f"   Activity Type: {type(activity)}")
                try:
                    print(f"   Activity Methods: {[m for m in dir(activity) if 'log' in m.lower()]}")
                except:
                    print(f"   Activity Methods: Could not inspect")
            else:
                print(f"   Activity Found: ❌ NOT FOUND in main module")
        except Exception as e:
            print(f"   Python Instance: ❌ FAILED - {e}")
    except ImportError as e:
        print(f"   Chaquopy Import: ❌ FAILED - {e}")
    
    # Test sending a log
    print(f"\n📝 Testing Log Transmission:")
    try:
        log_info("🧪 Firebase logging test message", {
            "test_type": "diagnostic",
            "timestamp": str(os.times()),
            "environment": "release" if not FIREBASE_LOGGER_DEBUG else "debug"
        })
        print("   Test Message Sent: ✅ No exceptions thrown")
    except Exception as e:
        print(f"   Test Message Sent: ❌ FAILED - {e}")
    
    print("="*60)
    print("🧪 DIAGNOSTIC TEST COMPLETED")
    print("="*60 + "\n")

def diagnose_release_mode_issues():
    """Diagnose specific issues that might occur in release mode vs debug mode"""
    print("\n🔍 RELEASE MODE DIAGNOSTIC")
    print("="*40)
    
    issues_found = []
    
    # Check 1: Environment variables
    flutter_env = os.environ.get('FLUTTER_ENV')
    if flutter_env != 'true':
        issues_found.append(f"FLUTTER_ENV not set to 'true' (current: {flutter_env})")
    
    # Check 2: Chaquopy availability
    try:
        import com.chaquo.python
        from com.chaquo.python import Python
        python = Python.getInstance()
        
        # Check 3: Main module and activity
        main_module = python.getModule("__main__")
        if not hasattr(main_module, 'activity'):
            issues_found.append("Activity not found in __main__ module")
        else:
            activity = main_module.activity
            if activity is None:
                issues_found.append("Activity is None in __main__ module")
            else:
                # Check if activity has the required method
                if not hasattr(activity, 'logToFirebase'):
                    issues_found.append("Activity does not have 'logToFirebase' method")
                else:
                    try:
                        # Test if we can call the method (this might fail but shouldn't crash)
                        activity.logToFirebase("TEST", "Diagnostic test", {})
                        print("✅ Successfully called activity.logToFirebase()")
                    except Exception as e:
                        issues_found.append(f"Failed to call activity.logToFirebase(): {e}")
        
    except ImportError as e:
        issues_found.append(f"Chaquopy not available: {e}")
    except Exception as e:
        issues_found.append(f"Python environment error: {e}")
    
    # Check 4: Java HashMap availability
    try:
        from java.util import HashMap
        test_map = HashMap()
        test_map.put("test", "value")
        print("✅ Java HashMap working correctly")
    except ImportError as e:
        issues_found.append(f"Java HashMap not available: {e}")
    except Exception as e:
        issues_found.append(f"Java HashMap error: {e}")
    
    # Report findings
    if issues_found:
        print("\n❌ ISSUES FOUND:")
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
        
        print("\n💡 SUGGESTED SOLUTIONS:")
        if any("FLUTTER_ENV" in issue for issue in issues_found):
            print("   • Ensure MainActivity.kt sets FLUTTER_ENV=true in configureFlutterEngine()")
        
        if any("Activity" in issue for issue in issues_found):
            print("   • Check that MainActivity.kt sets __main__.activity = this")
            print("   • Ensure Python is initialized after MainActivity is created")
        
        if any("logToFirebase" in issue for issue in issues_found):
            print("   • Verify logToFirebase method exists in MainActivity.kt")
            print("   • Check method signature matches: logToFirebase(String, String, Map)")
        
        if any("Chaquopy" in issue for issue in issues_found):
            print("   • Ensure app is running on Android with Chaquopy plugin")
            print("   • This is expected when running on desktop/testing")
        
        if any("HashMap" in issue for issue in issues_found):
            print("   • Java interop may not be available in current environment")
    else:
        print("✅ No issues found - Firebase logging should work!")
    
    print("="*40)

def test_firebase_bridge():
    """Run comprehensive Firebase bridge test"""
    test_firebase_logging()

def diagnose_release_issues():
    """Diagnose release mode specific issues"""
    diagnose_release_mode_issues()

def test_bridge_from_python():
    """Test the bridge by calling Flutter from Python"""
    try:
        from com.chaquo.python import Python
        python = Python.getInstance()
        main_module = python.getModule("__main__")
        
        if hasattr(main_module, 'activity'):
            activity = main_module.activity
            print("🧪 [PYTHON-BRIDGE] Testing bridge call to Flutter...")
            activity.callFlutterMethod("test_bridge", {
                "test_type": "python_to_flutter_test",
                "message": "Bridge test from Python backend",
                "timestamp": str(__import__('datetime').datetime.now())
            })
            print("✅ [PYTHON-BRIDGE] Bridge call to Flutter successful")
            return True
        else:
            print("❌ [PYTHON-BRIDGE] No activity found for bridge test")
            return False
    except Exception as e:
        print(f"❌ [PYTHON-BRIDGE] Bridge test failed: {e}")
        return False
