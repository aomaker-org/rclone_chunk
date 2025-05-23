# catclip: File Content to Clipboard Utility

`catclip` is a Python command-line utility designed to help you quickly copy the contents of one or more files to your system clipboard. It's particularly useful for pasting code, configuration files, or other text into applications like LLM chatbots, editors, or any context where you need to transfer file content via the paste buffer.

The script can process individual files or all non-hidden files directly within specified directories. For small files, it will display the content directly in the console before prompting for a copy.

## Features

  - **Copy File Contents:** Reads specified files and copies their text content to the clipboard.
  - **Process Multiple Files/Directories:** Accepts multiple file and/or directory paths as arguments.
  - **Directory Handling:** If a directory path is provided, `catclip` will iterate through and process all non-hidden files directly within that directory (it is not recursive).
  - **Small File Preview:** For files smaller than a defined threshold (default: 2KB), their content is printed to the console.
  - **Interactive Prompt:** For each file, it prompts the user whether to copy its content, skip it, or quit the script.
  - **WSL/Windows Focused:** Uses `clip.exe` for clipboard operations, making it suitable for Windows environments or Windows Subsystem for Linux (WSL) where `clip.exe` is accessible.
  - **UTF-8 Support:** Reads files as UTF-8 and handles encoding errors by replacing problematic characters.
  - **Graceful Exit:** Allows quitting the script mid-process and handles `Ctrl+C` interruptions.

## Requirements

  - **Python 3:** The script is written for Python 3.
  - **`clip.exe`:** This utility relies on `clip.exe` being available in your system's PATH. This is standard on Windows and typically accessible from WSL.

## How to Use

Run the script from your command line, providing one or more file paths or directory paths as arguments.

### Syntax

```bash
./catclip <file_or_dir1> [file_or_dir2...]
