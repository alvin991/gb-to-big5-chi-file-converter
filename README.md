# GB2312 TXT to zh-TW EPUB Batch Converter

This project converts a folder of **Simplified Chinese** `.txt` files (encoded as **GB2312**) into **Traditional Chinese (zh-TW)** EPUB files.

It also:
- Converts the **output EPUB filename** and **chapter title** from Simplified → Traditional.
- Writes `audit.txt` (successful outputs) and `conversion.log` (timestamped success/failure/skip).

## Requirements

- Python 3
- Dependencies listed in `requirements.txt`

## Install (recommended: virtual environment)

From the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Git Bash (optional)

If you're using Git Bash (bash on Windows), activate the venv like this:

```bash
source ./.venv/Scripts/activate
pip install -r requirements.txt
```

You can verify it with:

```bash
which python
python --version
pip --version
```

## Input / Output

Place files like this:

- `input/` contains your `.txt` files (GB2312, Simplified Chinese)
- `output/` will contain generated `.epub` files

## Run

```powershell
python converter.py
```

## How skipping works (audit.txt)

Before converting, the script loads `audit.txt` into memory.

If an output filename is already present in `audit.txt`, that input is skipped (so you can rerun safely).

## Logging

- `audit.txt`: one output EPUB filename per line (only successful conversions)
- `conversion.log`: timestamped lines including:
  - `SUCCESS input.txt -> output.epub`
  - `FAIL input.txt -> <error message>`
  - `SKIP input.txt (already in audit)`

## Notes

- The EPUB internal chapter file name is fixed as `content.xhtml`.
- The reader-facing chapter/TOC label is derived from the converted Traditional filename stem.

