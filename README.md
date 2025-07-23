# WanChai INI Editor

A modern GUI application for viewing/editing/saving WanChai INI files.

## For What?
In the past, editing wanchai ini files usually involved opening the .ini file with Notepad, locating the values to be changed, and then performing replacements or batch replacements. However, because the data in .ini files is quite raw and not easy to read, and there are many entries, the process was difficult, error-prone, inefficient, and often made it hard to quickly resolve production line issues.

Therefore, we developed a GUI-based ini editor tool to help modify ini files. This tool provides a user-friendly interface, a range of features beyond expectations, and software version management that meets industry standards. It not only greatly improves data readability, but also significantly reduces operational difficulty and increases work efficiency.

## Features

### 🎯 Main Features
- **Visual Editing**: Intuitive graphical interface for editing wanchai INI files
- **Dual Tab Design**:   
  - Test Items Tab: Manage all test items
  - Basic Info Tab: Edit the [Info] section
- **Real-time Search**: Quickly search for specific content within test items
- **Responsive Design**: Supports window resizing

### 📁 File Management
- **File Browser**: Supports selecting different INI files for editing
- **Export INI file**: Export the edited INI content to a new INI file

### 🔧 Editing Features
- **Double-click to Edit**: Double-click a test item to open a dedicated interface edit window for the item.
- **Context Menu**: Right-click to show options such as Edit, Insert Before, Insert After, Copy, Copy To All SKUs, and Delete.
- **Batch Operations**: Supports batch modification of test items.

## 📁 Project File Structure

```
wanchai-tool/
├── wanchai-editor.py                # Main program file
├── .gitignore                       # Git ignore file
├── run.bat                          # Windows launch script
├── run.sh                           # Linux/Mac launch script
├── requirements.txt                 # Dependency specification
├── README.md                        # Documentation
├── editor.svg                       # Original program icon
├── editor.ico                       # Program icon
├── version_manager.py               # Version management tool
├── version.py                       # Version number storage file
├── index.html                       # Web version html file
├── wanchai-editor-web.js            # Core js for index.html
├── package.py                       # Packaging script
└── package-web.py                   # Web version packaging script
```

## System Requirements

- **Python Version**: 3.6 or higher
- **Operating Systems**: Windows, macOS, Linux
- **Dependencies**: All managed in requirements.txt

## Development Information

- **Programming Language**: Python 3
- **GUI Framework**: tkinter/ttk
- **File Format**: INI configuration file
- **Encoding**: UTF-8
- **Main Class Name**: WanchaiEditor

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

## Debug

### Way 1:
```bash
python wanchai-editor.py
```

### Way 2:
```bash
python -m wanchai-editor
```

## Package the application as a standalone executable (Windows)

```bash
# project usage
python package.py
python package.py prerelease
python package.py patch
python package.py minor
python package.py major

# for web version use
python package-web.py

# basic usage
pyinstaller --clean --onefile --windowed wanchai-editor.py
pyinstaller --clean --onefile --windowed --name wanchai-editor_v1.0.0-beta.1 wanchai-editor.py
pyinstaller --noconfirm --clean --onefile --windowed --name=wanchai-editor_v1.0.0-beta.1 --icon=editor.ico wanchai-editor.py
```

## Version Management

- The version number is stored in the `version.py` file, in the following format:
  ```python
  __version__ = '1.2.3'
  ```
- To read, bump, or set the version number, use the `version_manager.py` script:
  ```sh
  python version_manager.py get         # Get the current version
  python version_manager.py prerelease       # Bump the prerelease version
  python version_manager.py patch       # Bump the patch version
  python version_manager.py minor       # Bump the minor version
  python version_manager.py major       # Bump the major version
  python version_manager.py set 1.2.3   # Set to a specific version
  ```

## Supported File Types

The program only supports standard INI file format, with special optimizations for WanChai test specifications:

### Basic Info Section
```ini
[Info]
UnitCount=1
Export Date=2025/7/14 8:55:56
```

### Test Items Section
```ini
[38599-989-889]
Count=49
1=(Identifier,TestID,Description,Enabled,StringLimit,LowLimit,HighLimit,LimitType,Unit,Parameters) VALUES ('38599-989-889','999','Name',0,'Jabra Evolve3 85','0','0','0','Description','UC, Link390C, Black, WLC Chrg')
```

## Supported Hotkey

- **Ctrl+C**: Copy test item/items
- **Ctrl+V**: Paste test item/items
- **Ctrl+X**: Cut test item/items

## Reference
1. Icon site: https://feathericons.com/ or https://www.streamlinehq.com/
2. Convert svg to ico: https://www.aconvert.com/cn/icon/svg-to-ico/
3. A blog that introduce serval icon site: https://zhuanlan.zhihu.com/p/667510330

## 📞 Technical Support
- Dylan Zhang

## Changelog

### v1.0.0-beta.1
- Initial release.

### v1.0.0-beta.2
- Added basic INI file editing functionality.
- Implemented the first version of different types of "Apply Change To".
- Provided a modern GUI interface.
- Implemented search and filter functionality.

### v1.0.0-beta.3
- Resolve bug: Index chaos when copy SKU items.
- Resolve bug: Identifier field is missed.
- Resolve bug: Drage items will cause index chaos.
- Resolve bug: Some values of field are changed by program, like 00 is changed to 0.
- Resolve bug: Duplicate index numbers are showed when there have same SKU items.
- New feature: batch copy SKU items to all SKUs.
- New feature: update or batch update SKU name.
- New feature: Need a morden and more beautiful and more friendly UI.
- New feature: Need 5 different types of updating way(Apply Change To).
- New feature: Need a copy feature, like copy SKU item/items, support using ctrl+c and ctrl+v, etc.
- New feature: Make it able to package .exe file and using semver accordingly to do version control.

### v1.0.0-beta.4
- Added cut functionality(ctrl+x)
- Update README.md

### v1.0.0
- Update export file name to include [].
- Release first standard version of desktop version.
- Develop web version and release first standard version of it.