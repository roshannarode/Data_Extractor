# 🚀 Building Executable with PyInstaller

This guide shows you how to create a standalone executable (.exe) from your Data Extractor application with version information and a custom icon.

## 📋 Prerequisites

1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Prepare an Icon** (Optional):
   - Create or download a `.ico` file
   - Name it `icon.ico` and place it in your project directory
   - Recommended size: 256x256 pixels or higher
   - You can convert PNG/JPG to ICO using online converters

## 🎯 Quick Build (Automated)

The easiest way is to use the provided build script:

```bash
python build_exe.py
```

This script will:
- ✅ Check and install PyInstaller if needed
- ✅ Look for icon files automatically
- ✅ Include version information
- ✅ Create a single executable file
- ✅ Clean up temporary files

## 🔧 Manual Build Commands

### Basic Command (No Version/Icon)
```bash
pyinstaller --onefile --windowed app.py
```

### With Version Information
```bash
pyinstaller --onefile --windowed --version-file=version_info.txt app.py
```

### With Icon
```bash
pyinstaller --onefile --windowed --icon=icon.ico app.py
```

### Complete Command (Version + Icon)
```bash
pyinstaller --onefile --windowed --name=DataExtractor --version-file=version_info.txt --icon=icon.ico app.py
```

## 📝 PyInstaller Options Explained

| Option | Description |
|--------|-------------|
| `--onefile` | Create a single executable file |
| `--windowed` | Hide console window (for GUI apps) |
| `--console` | Show console window (for debugging) |
| `--name=NAME` | Name of the executable |
| `--icon=PATH` | Path to icon file (.ico) |
| `--version-file=PATH` | Path to version info file |
| `--add-data` | Include additional data files |
| `--hidden-import` | Force import of modules |

## 📄 Version Information File

The `version_info.txt` file contains metadata that will be embedded in your executable:

```python
# Example version_info.txt structure
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(2,0,0,0),      # File version (major, minor, patch, build)
    prodvers=(2,0,0,0),      # Product version
    # ... other metadata
  ),
  kids=[
    StringFileInfo([
      StringTable(u'040904B0', [
        StringStruct(u'CompanyName', u'Your Company'),
        StringStruct(u'FileDescription', u'Your App Description'),
        StringStruct(u'FileVersion', u'2.0.0.0'),
        StringStruct(u'ProductName', u'Your Product Name'),
        # ... other strings
      ])
    ])
  ]
)
```

### Customizing Version Info

Edit `version_info.txt` to change:
- **Company Name**: Your organization
- **File Description**: App description
- **Version Numbers**: Update version numbers
- **Copyright**: Your copyright notice
- **Product Name**: Your application name

## 🎨 Icon Requirements

### Supported Formats
- **Windows**: `.ico` files (recommended)
- **Alternative**: `.exe` files (to extract icon from)

### Icon Creation Tips
1. **Size**: Use 256x256 pixels or higher
2. **Format**: ICO format with multiple sizes embedded
3. **Tools**: 
   - Online converters (PNG/JPG → ICO)
   - GIMP, Photoshop, or other image editors
   - IconForge, IcoFX (specialized icon editors)

### Icon Placement
Place your icon file in the project directory with one of these names:
- `icon.ico` (preferred)
- `app_icon.ico`
- `data_extractor.ico`

## 📁 Build Output

After building, you'll find:
- **`dist/`** folder: Contains your executable
- **`build/`** folder: Temporary build files (can be deleted)
- **`*.spec`** file: PyInstaller specification file

## 🛠️ Troubleshooting

### Common Issues

**1. "Module not found" errors**
```bash
# Add hidden imports
pyinstaller --onefile --hidden-import=MODULE_NAME app.py
```

**2. Missing data files**
```bash
# Include data files
pyinstaller --onefile --add-data "data_file.txt;." app.py
```

**3. Large executable size**
```bash
# Exclude unnecessary modules
pyinstaller --onefile --exclude-module=MODULE_NAME app.py
```

**4. Version info not working**
- Ensure `version_info.txt` syntax is correct
- Check file encoding (should be UTF-8)

**5. Icon not showing**
- Verify icon file format (.ico)
- Check icon file path
- Try absolute path to icon

### Debug Build
For debugging, use console mode:
```bash
pyinstaller --onefile --console --version-file=version_info.txt --icon=icon.ico app.py
```

## 🔄 Advanced Configuration

### Custom Spec File
For complex builds, you can modify the `.spec` file:
```bash
# Generate spec file first
pyi-makespec --onefile --windowed app.py

# Edit DataExtractor.spec file
# Then build from spec
pyinstaller DataExtractor.spec
```

### Multiple Files
If you need to include additional files:
```python
# In the .spec file
datas=[('data_folder', 'data_folder')]
```

## ✅ Verification

After building, verify your executable:

1. **Check file properties** (Windows):
   - Right-click → Properties → Details
   - Verify version information appears

2. **Test the executable**:
   - Run from different locations
   - Test on different machines
   - Verify all features work

3. **File size check**:
   - Typical size: 15-50 MB (depending on dependencies)
   - Large size might indicate unnecessary inclusions

## 📦 Distribution

Your executable is now ready for distribution:
- **Single file**: Easy to share
- **No Python required**: Runs on any Windows machine
- **Portable**: Can run from any location
- **Professional**: Includes version info and icon

Remember to test your executable on different systems before final distribution! 