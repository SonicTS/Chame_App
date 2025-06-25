# Scripts

Utility scripts for building, deployment, and maintenance tasks.

## 📁 Available Scripts

### Build Scripts
- **`build_executeable.bat`** - Creates executable build of the application
  - Uses PyInstaller to create standalone executable
  - Packages all dependencies
  - Creates distribution-ready build

## 🚀 Usage

### Building Executable
```bash
# Run from the main app directory
scripts\build_executeable.bat
```

This will:
1. Install PyInstaller if not present
2. Create executable build with all dependencies
3. Output build artifacts to `build/` directory
4. Create standalone executable for distribution

### Build Output
- **Location**: `../build/`
- **Executable**: Look for `.exe` files in build subdirectories
- **Artifacts**: Analysis files, dependency mappings, warnings

## 🔧 Script Maintenance

### Adding New Scripts
When adding new utility scripts:

1. **Windows Batch Files** - Use `.bat` extension
2. **Python Scripts** - Use `.py` extension with shebang
3. **Shell Scripts** - Use `.sh` extension for cross-platform
4. **Documentation** - Update this README with usage instructions

### Script Categories
- **Build Scripts** - Compilation and packaging
- **Deployment Scripts** - Production setup and deployment
- **Maintenance Scripts** - Database cleanup, log rotation, etc.
- **Development Scripts** - Development environment setup

## 📋 Common Tasks

### Build Troubleshooting
If build fails:
1. Check Python and PyInstaller installation
2. Verify all dependencies in `requirements.txt`
3. Check for missing imports or circular dependencies
4. Review build warnings and errors

### Adding Dependencies
When adding new dependencies:
1. Update `requirements.txt`
2. Test build process
3. Update build script if needed
4. Document any special build requirements

## 🛠️ Development

### Script Development Guidelines
- **Error Handling** - Include proper error checking
- **Documentation** - Comment complex operations
- **Cross-Platform** - Consider Windows/Linux compatibility
- **Testing** - Test scripts in clean environments

### Dependencies
- PyInstaller for executable builds
- Python 3.x environment
- All application dependencies from `requirements.txt`

---

**Ready to build:** Run `scripts\build_executeable.bat` from the main app directory.
