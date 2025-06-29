"""
Firebase logging utility for Python backend
Safely logs to Firebase through Flutter bridge when available
"""
import traceback
import os
from typing import Dict, Any, Optional

# Debug flag - set to True to enable verbose logging output
FIREBASE_LOGGER_DEBUG = False

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
        if FIREBASE_LOGGER_DEBUG:
            print(f"🚀 [FIREBASE-BRIDGE] Attempting to send {level} log to Firebase...")
            print(f"🚀 [FIREBASE-BRIDGE] Message: {message}")
            if metadata:
                print(f"🚀 [FIREBASE-BRIDGE] Metadata: {metadata}")
        
        if not self._bridge_available:
            if FIREBASE_LOGGER_DEBUG:
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
                    if FIREBASE_LOGGER_DEBUG:
                        print("❌ [FIREBASE-BRIDGE] Still no activity found in __main__")
                    return
            except Exception as e:
                if FIREBASE_LOGGER_DEBUG:
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
            if FIREBASE_LOGGER_DEBUG:
                print("✅ [FIREBASE-BRIDGE] Successfully sent log to Firebase through bridge!")
            
        except Exception as e:
            # Print debug info to help diagnose the issue
            if FIREBASE_LOGGER_DEBUG:
                print(f"❌ [BRIDGE_ERROR] Failed to log to Firebase: {e}")
                print(f"[BRIDGE_ERROR] Bridge available: {self._bridge_available}")
                print(f"[BRIDGE_ERROR] Activity: {self._activity}")
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
