import java.util.Properties
import java.io.FileInputStream


plugins {
    id("com.android.application")
    id("dev.flutter.flutter-gradle-plugin")
    id("com.chaquo.python")

    id("org.jetbrains.kotlin.android")  
    id("com.google.gms.google-services")  // Google services plugin for Firebase, etc.
    // Remove explicit version to avoid conflict
    
}

dependencies {
  // Import the Firebase BoM
  implementation(platform("com.google.firebase:firebase-bom:33.15.0"))


  // TODO: Add the dependencies for Firebase products you want to use
  // When using the BoM, don't specify versions in Firebase dependencies
  implementation("com.google.firebase:firebase-analytics")


  // Add the dependencies for any other desired Firebase products
  // https://firebase.google.com/docs/android/setup#available-libraries
}

val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("key.properties")
if (keystorePropertiesFile.exists()) {
    FileInputStream(keystorePropertiesFile).use { keystoreProperties.load(it) }
    println("Keystore properties loaded successfully")
    println("keyAlias: ${keystoreProperties["keyAlias"]}")
    println("storeFile: ${keystoreProperties["storeFile"]}")
} else {
    println("Keystore properties file not found at: ${keystorePropertiesFile.absolutePath}")
}

android {
    namespace = "com.chame.kasse"
    compileSdk = 35
    ndkVersion = "27.0.12077973"
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_11.toString()
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.chame.kasse"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = 24
        targetSdk = 34
        versionCode = 2
        versionName = "2.5.1-beta"
        ndk {
            abiFilters += listOf("armeabi-v7a", "arm64-v8a", "x86", "x86_64") //
        }
    }
    signingConfigs {
        create("release") {
            if (keystorePropertiesFile.exists() && keystoreProperties.containsKey("keyAlias")) {
                keyAlias = keystoreProperties["keyAlias"] as String
                keyPassword = keystoreProperties["keyPassword"] as String
                storeFile = file(keystoreProperties["storeFile"] as String)
                storePassword = keystoreProperties["storePassword"] as String
                println("Release signing config created successfully")
            } else {
                println("WARNING: Keystore properties not properly loaded, release signing will fail")
            }
        }
    }

    buildTypes {
        getByName("release") {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = false
            isShrinkResources = false
            // Weitere Optionen...
        }
    }

    sourceSets {
        getByName("main") {
            manifest.srcFile("src/main/AndroidManifest.xml")
        }
    }
}

chaquopy {
    sourceSets {
        getByName("main") {
            srcDir("../../../../../backend/app")
        }
    }
    defaultConfig {
        pip {
            // A requirement specifier, with or without a version number:
            install("sqlalchemy")
            install("passlib")
            install("argon2-cffi")
        }
    }
}

flutter {
    source = "../.."
}
