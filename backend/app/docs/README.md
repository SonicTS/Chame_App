# Documentation

This directory contains comprehensive documentation for the Chame App backend.

## 📚 Available Documentation

### API Testing Documentation
- **[API_TESTING.md](API_TESTING.md)** - Complete guide to the testing framework
  - Framework overview and components
  - Usage instructions and examples
  - Test database types and contents
  - Troubleshooting and debugging guide
  - CI/CD integration instructions
  - Best practices for development and production

## 📖 Quick Reference

### Testing Framework
- **Location**: `../testing/`
- **Quick Start**: `cd ../testing && python run_api_tests.py --quick`
- **Full Test**: `python run_api_tests.py`
- **Generate DBs**: `python generate_test_databases.py all`

### Key Documentation Topics

#### Testing Framework
- Complete API function validation
- Realistic test data generation
- Edge case and error condition testing
- Performance testing capabilities
- CI/CD integration guidelines

#### Database Testing
- Multiple test database scenarios
- Minimal, comprehensive, edge case, and performance variants
- Data integrity validation
- Business logic testing

#### Development Workflow
- Test-driven development practices
- Debugging failed tests
- Custom test case creation
- Production deployment validation

## 🎯 Documentation Standards

### For Contributors
When adding new documentation:

1. **Clear Structure** - Use proper markdown formatting
2. **Practical Examples** - Include code snippets and commands
3. **Troubleshooting** - Document common issues and solutions
4. **Cross-References** - Link related documentation
5. **Keep Updated** - Maintain accuracy with code changes

### Documentation Types
- **API Guides** - Function usage and examples
- **Testing Guides** - Framework usage and best practices
- **Deployment Guides** - Production setup instructions
- **Troubleshooting** - Common issues and solutions

## 🔗 Related Resources

### Code Locations
- **Main API**: `../services/admin_api.py`
- **Testing Framework**: `../testing/`
- **Database Models**: `../models/`
- **Configuration**: `../config.py`

### External Resources
- SQLAlchemy Documentation
- Flask Documentation  
- Python Testing Best Practices
- Database Design Patterns

---

**Need help?** Check the relevant documentation file or the testing framework overview.
