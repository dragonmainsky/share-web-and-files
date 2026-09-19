# Share Web and Files - Version Update Report

## What's New
- **Browse Start File:** Added a "Browse File..." button next to the "Start file" input field. You can now easily pick an `index.html` (or any other starting file) from the selected folder without typing the path manually.
- **Zip Files Option:** When sharing multiple files, a new "Zip files before sharing" checkbox will automatically appear. 
  - If checked, all selected files will be automatically compressed into a single `.zip` archive for easy downloading.
  - If unchecked, the files will be shared as a directory listing, allowing the receiver to download individual files.

## Technical Details
- Updated `ui.py` to include the new Browse button and Zip Checkbox logic.
- Updated `core.py` to handle the conditional zipping process and raw file serving.
- Compiled the latest version into a standalone executable (`ShareWebAndFiles.exe`).
