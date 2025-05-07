
---

# HomeVision `sample.env` File Parser

A reverse-engineering Python tool for parsing proprietary binary `.env` archive files used internally at **HomeVision**. These archives store embedded files (e.g. images, XMLs, text blobs) in an undocumented tagged format, similar in intent to `.tar` archives but with custom metadata headers.

---

## Key Features

* Detects all tags in the binary using pattern recognition
*  Reverse engineers `.env` format with no schema documentation
* Extracts embedded files with correct file types and extensions
* Builds `metadata.json` with SHA1 hashes and metadata per file
* Optional CLI summary with GitHub-style table display
* Supports multi-file input with robust parsing logic

---

## Strategy Overview

The tool follows this process:

1. **Tag Discovery**: Extracts all unique tags in the binary using regex.
2. **Primary Tag Scanning**: Uses a list of known tags (like `GUID/`, `FILENAME/`, `DOCU/`) to track metadata and file contents.
3. **File Boundary Detection**: Identifies where each file starts and ends using tag positions.
4. **Metadata Assembly**: Gathers filename, GUID, extension, and type from tagged headers.
5. **File Type Detection**: Infers missing file types using magic numbers (e.g., PNG, JPG headers).
6. **Export**: Writes the extracted binary content and builds a final summary and metadata file.

---

## CLI Usage

### Example

```bash
python main.py --input sample.env test1.env --output final_output --summary
```

### Arguments

| Argument         | Description                        | Required | Default        |
| ---------------- | ---------------------------------- | ---- | -------------- |
| `--input`, `-i`  | One or more `.env` files to parse  | Yes  | N/A            |
| `--output`, `-o` | Directory to save extracted files  |  No  | `final_output` |
| `--summary`      | Display file summary after parsing |  No  | Disabled       |

---

## 📁 Output Files

*  **Extracted Files** — written to the `--output` folder
* **metadata.json** — contains per-file metadata (filename, size, SHA1, GUID, type)
* **all\_tags.txt** — list of all tags found in the `.env` binary
* **Terminal Summary (optional)** — GitHub-style table

---

##  Example Output

### Console Output

```text
 Saved C000117E-88C4-41E4-ABC6-C476419D1AFF (20 bytes, type: Unknown)
 Saved homer-simpson.jpg (40 bytes, type: JPEG)
 Saved 0-INC2.xml (36078 bytes, type: XML)
 Saved 1004UADMISMOUAD2.6GSE.xml (142 bytes, type: XML)
 Saved 1-REO2.xml (16387 bytes, type: XML)
 Saved 2-1004UAD.xml (164 bytes, type: XML)
 Saved content.txt (201 bytes, type: TEXT)
 Saved 94CEAC98-E4FC-4BB7-ADED-B71242DCEF4F (719 bytes, type: Unknown)

 Parsed 8 files. Metadata saved to 'final_output/metadata.json'
```

### Summary Table

| Filename                             | Type    | Size (bytes) |
| ------------------------------------ | ------- | ------------ |
| C000117E-88C4-41E4-ABC6-C476419D1AFF | Unknown | 20           |
| homer-simpson.jpg                    | JPEG    | 40           |
| 0-INC2.xml                           | XML     | 36078        |
| 1004UADMISMOUAD2.6GSE.xml            | XML     | 142          |
| 1-REO2.xml                           | XML     | 16387        |
| 2-1004UAD.xml                        | XML     | 164          |
| content.txt                          | TEXT    | 201          |
| 94CEAC98-E4FC-4BB7-ADED-B71242DCEF4F | Unknown | 719          |

---

## Developer Notes

*  Python 3.7+
* No external dependencies required, except for `tabulate` (install via `pip install tabulate`)
*  Modular design — utility functions and core logic are separated
* Easily extendable — add more `PRIMARY_TAGS` or new content detectors

---


