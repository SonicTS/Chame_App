# chame_flutter

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.

## Building:

### Debug APK (for testing):
```
flutter build apk --debug
```

### Release APK (requires signing setup):
```
flutter build apk --release
```

Note: Release builds require keystore configuration. See signing setup below.

## Signing Setup for Release Builds

### Step 1: Create a new keystore (if you don't have one)
```bash
keytool -genkey -v -keystore android/app/upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```

Follow the prompts to enter:
- Keystore password (remember this!)
- Key password (can be same as keystore password)
- Your name and organization details

### Step 2: Create key.properties file
Create `key.properties` in the Flutter project root (same level as pubspec.yaml) with your keystore details:
```properties
storePassword=your_keystore_password
keyPassword=your_key_password
keyAlias=upload
storeFile=android/app/upload-keystore.jks
```

### Step 3: Build release APK
```bash
flutter build apk --release
```

**Important Notes:**
- Keep your keystore file and passwords safe - you'll need them for all future releases
- Never commit the keystore file or key.properties to version control
- For production apps, use the same keystore across all builds to maintain app signing consistency