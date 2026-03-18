from pathlib import Path
from datetime import datetime
import traceback
import html

import opencc
from ebooklib import epub

# --- Config ---
INPUT_DIR_NAME = "input"
OUTPUT_DIR_NAME = "output"
INPUT_ENCODING = "gb2312"  # Your simplified text files
BOOK_AUTHOR = "Author Name"
EPUB_FILE_NAME = "content.xhtml"  # Internal file name inside the EPUB
AUDIT_FILE_NAME = "audit.txt"
LOG_FILE_NAME = "conversion.log"


def sanitize_filename(name: str) -> str:
    # Windows disallows: < > : " / \ | ? *
    illegal = set('<>:"/\\|?*')
    return "".join(ch for ch in name if ch not in illegal).strip()


def convert_one(
    input_path: Path,
    idx: int,
    opencc_converter: opencc.OpenCC,
    output_dir: Path,
) -> Path:
    simplified_stem = input_path.stem
    traditional_stem = opencc_converter.convert(simplified_stem)
    safe_stem = sanitize_filename(traditional_stem) or f"book_{idx:04d}"

    # Use converted filename as title/chapter title
    title = safe_stem

    # Step 1: Read simplified text
    try:
        with open(input_path, "r", encoding=INPUT_ENCODING) as f:
            simplified_text = f.read()
    except UnicodeDecodeError:
        # Fallback: GB18030 is a superset and can fix occasional mismatches.
        with open(input_path, "r", encoding="gb18030") as f:
            simplified_text = f.read()

    # Step 2: Convert Simplified -> Traditional
    traditional_text = opencc_converter.convert(simplified_text)

    # Step 3: Build the EPUB
    book = epub.EpubBook()
    book.set_identifier(f"id_{idx:04d}")
    book.set_title(title)
    book.set_language("zh-TW")
    book.add_author(BOOK_AUTHOR)

    # Convert plain text to HTML paragraphs (escape to keep valid XHTML)
    paragraphs = "".join(
        f"<p>{html.escape(line, quote=False)}</p>"
        for line in traditional_text.splitlines()
        if line.strip()
    )
    html_content = f"<html><body>{paragraphs}</body></html>"

    chapter = epub.EpubHtml(title=title, file_name=EPUB_FILE_NAME, lang="zh-TW")
    chapter.content = html_content
    book.add_item(chapter)

    # Navigation
    book.toc = (epub.Link(EPUB_FILE_NAME, title, "content"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Important: keep nav out of the spine to avoid a blank/short first page.
    book.spine = [chapter]

    # Save EPUB to output folder, named after converted filename
    output_path = output_dir / f"{safe_stem}.epub"
    counter = 1
    while output_path.exists():
        output_path = output_dir / f"{safe_stem}_{counter}.epub"
        counter += 1

    epub.write_epub(str(output_path), book)
    return output_path


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / INPUT_DIR_NAME
    output_dir = base_dir / OUTPUT_DIR_NAME
    output_dir.mkdir(parents=True, exist_ok=True)

    audit_path = base_dir / AUDIT_FILE_NAME
    log_path = base_dir / LOG_FILE_NAME

    opencc_converter = opencc.OpenCC("s2twp")  # Simplified -> Traditional (Taiwan)

    # On Windows, glob matching is effectively case-insensitive, so `*.txt` and `*.TXT`
    # can both match the same file. Deduplicate to avoid converting twice.
    txt_files_set = set(input_dir.glob("*.txt")) | set(input_dir.glob("*.TXT"))
    txt_files = sorted(txt_files_set, key=lambda p: p.name.lower())
    if not txt_files:
        print(f"No .txt files found in {input_dir}")
        raise SystemExit(0)

    audit_set: set[str] = set()
    if audit_path.exists():
        # Remember which output EPUB filenames were already generated successfully.
        with open(audit_path, "r", encoding="utf-8", errors="ignore") as audit_f_read:
            audit_set = {line.strip() for line in audit_f_read if line.strip()}

    with open(audit_path, "a", encoding="utf-8") as audit_f, open(log_path, "a", encoding="utf-8") as log_f:
        for idx, txt_path in enumerate(txt_files, start=1):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                print(f"[{timestamp}] Start converting: {txt_path.name}")
                simplified_stem = txt_path.stem
                traditional_stem = opencc_converter.convert(simplified_stem)
                safe_stem = sanitize_filename(traditional_stem) or f"book_{idx:04d}"

                # If audit already contains an output filename for this stem, skip.
                # (This covers cases where the original output became `*_1.epub`, `*_2.epub`, etc.)
                skip_candidates = [f"{safe_stem}.epub"] + [
                    f"{safe_stem}_{i}.epub" for i in range(1, 51)
                ]
                if any(name in audit_set for name in skip_candidates):
                    log_f.write(f"[{timestamp}] SKIP {txt_path.name} (already in audit)\n")
                    print(f"[{timestamp}] Skip: {txt_path.name} (already in audit)")
                    continue

                output_path = convert_one(txt_path, idx, opencc_converter, output_dir)
                audit_f.write(f"{output_path.name}\n")
                audit_set.add(output_path.name)
                log_f.write(f"[{timestamp}] SUCCESS {txt_path.name} -> {output_path.name}\n")
                print(f"[{timestamp}] Conversion completed: {txt_path.name} -> {output_path.name}")
            except Exception as e:
                # Keep failure info in the log so you can debug which files broke.
                err_msg = str(e) or e.__class__.__name__
                log_f.write(f"[{timestamp}] FAIL {txt_path.name} -> {err_msg}\n")
                # Optional: add stack trace for deeper debugging
                log_f.write(traceback.format_exc() + "\n")
                print(f"[{timestamp}] Conversion failed: {txt_path.name} -> {err_msg}")