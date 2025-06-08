buildscript {
    repositories {
        google()
        mavenCentral()
    }

    dependencies {
        // Updated to a more recent version of AGP
        classpath("com.android.tools.build:gradle:8.10.0")
    }
}

plugins {
    id("com.chaquo.python") version "16.1.0" apply false
    id("com.google.gms.google-services") version "4.4.2" apply false
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}



val newBuildDir: Directory = rootProject.layout.buildDirectory.dir("../../build").get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}

