import os
import json
import hashlib
import re
import argparse
import logging
from typing import List, Tuple, Dict
from tabulate import tabulate

# Setup logger
logging.basicConfig(level=logging.INFO, format='%(message)s')

# List of recognized tags in the proprietary .env archive format
PRIMARY_TAGS = [
    b'GUID/', b'FILENAME/', b'EXT/', b'TYPE/', b'SHA1/',
    b'DOCU/', b'_SIG/', b'DOCTYPE/', b'ENV_GUID/',
    b'FORM/', b'IMAGE/', b'OADI/', b'SUP/', b'XSL/', b'ID/', b'QU/'
]

def extract_all_tags(data: bytes) -> List[str]:
    # Extract all unique uppercase tags from the binary .env content, this is for reference and listing all tags in file.
    tag_pattern = re.compile(rb'([A-Z0-9_]{2,32}/)')
    return sorted(set(m.group().decode('utf-8') for m in tag_pattern.finditer(data)))

def find_tag_positions(data: bytes) -> List[Tuple[int, str]]:
    #Find positions of known tags in the binary stream.
    tag_pattern = re.compile(b'(' + b'|'.join(PRIMARY_TAGS) + b')')
    return [(m.start(), m.group().decode('utf-8')) for m in tag_pattern.finditer(data)]

def clean_filename(name: str) -> str:
    # Sanitize filenames to be filesystem safe.
    name = name.replace('\r', '').replace('\n', '')
    return re.sub(r'[\\/:"*?<>|]+', '_', name.strip())

def detect_file_type(blob: bytes, ext_or_type: str = "") -> Tuple[str, str]:
    # Extract file type based on extension or blob content.
    ext_or_type = ext_or_type.strip().lower()

    if ext_or_type in {'jpg', '.jpg', 'jpeg'}:
        return '.jpg', 'JPEG'
    if ext_or_type in {'png', '.png'}:
        return '.png', 'PNG'
    if ext_or_type in {'webp', '.webp'}:
        return '.webp', 'WEBP'
    if ext_or_type in {'xml', '.xml'}:
        return '.xml', 'XML'
    if ext_or_type in {'zip', '.zip'}:
        return '.zip', 'ZIP'
    if ext_or_type in {'txt', '.txt', 'text'}:
        return '.txt', 'TEXT'

    # I got this logic from git-hub
    if blob.startswith(b'\xFF\xD8\xFF'):
        return '.jpg', 'JPEG'
    if blob.startswith(b'\x89PNG'):
        return '.png', 'PNG'
    if blob.startswith(b'RIFF') and b'WEBP' in blob[:20]:
        return '.webp', 'WEBP'
    if blob.strip().startswith(b'<?xml') or b'</' in blob[:200]:
        return '.xml', 'XML'
    if blob.startswith(b'PK\x03\x04'):
        return '.zip', 'ZIP'
    if b'content' in blob[:300].lower():
        return '.txt', 'TEXT'

    return '.bin', 'Unknown'

def save_file(meta: Dict[str, str], blob: bytes, all_files: List[Dict], output_dir: str) -> None:
    #Write extracted binary content to disk and append metadata.
    ext = meta.get('EXT', '').strip().lower()
    file_type = meta.get('TYPE', '').strip()

    # If file extension is present, get file type or extract via file content
    if not ext and not file_type:
        detected_ext, detected_type = detect_file_type(blob)
        ext = ext or detected_ext.lstrip('.')
        file_type = file_type or detected_type
    else:
        ext, file_type = detect_file_type(blob, ext)

    raw_fname = meta.get('FILENAME') or meta.get('GUID') or f"file_{len(all_files)}"
    raw_fname = clean_filename(raw_fname)

    filename = raw_fname.rstrip('.')

    full_path = os.path.join(output_dir, filename)
    with open(full_path, 'wb') as f:
        f.write(blob)

    # Save the hash of file in meta-data json
    sha1 = hashlib.sha1(blob).hexdigest()
    all_files.append({
        'filename': filename,
        'type': file_type or 'Unknown',
        'guid': meta.get('GUID'),
        'size_bytes': len(blob),
        'sha1': sha1
    })

    logging.info(f" Saved {filename} ({len(blob)} bytes, type: {file_type or 'Unknown'})")

# Refactored helper: handles metadata tags like GUID/, FILENAME/, etc.
def process_metadata_tag(tag: str, value: bytes, current_meta: Dict[str, str], files: List[Dict], output_dir: str, current_blob: bytes) -> Tuple[Dict[str, str], bytes]:
    decoded = value.decode('utf-8', errors='replace')
    if tag == 'GUID/':
        if current_meta and current_blob:
            save_file(current_meta, current_blob, files, output_dir)
            current_blob = b''
        current_meta = {'GUID': decoded}
    else:
        current_meta[tag.strip('/')] = decoded
    return current_meta, current_blob

# Refactored helper: handles binary content tags like DOCU/, IMAGE/
def accumulate_blob(tag: str, raw: bytes, current_blob: bytes, current_meta: Dict[str, str], files: List[Dict]) -> Tuple[bytes, Dict[str, str]]:
    current_blob += raw
    if not current_meta:
        current_meta = {'GUID': f'unlabeled_{len(files)}'}
    return current_blob, current_meta

def parse_env_file(file_path: str, output_dir: str = "final_output", show_summary: bool = False) -> None:

    #Parse a proprietary HomeVision sample.env archive and extract embedded files
    with open(file_path, 'rb') as f:
        data = f.read()

    # Save all the tags extracted in all_tags.txt for analysis, later I extracted the primary set of tags as mentioned above. e.g
    # PRIMARY_TAGS = [
    #     b'GUID/', b'FILENAME/', b'EXT/', b'TYPE/', b'SHA1/',
    #     b'DOCU/', b'_SIG/', b'DOCTYPE/'........ ]
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, 'all_tags.txt'), 'w') as tf:
        tf.write('\n'.join(extract_all_tags(data)))

    # Find primary tag positions
    tag_positions = find_tag_positions(data)
    # Tag the end of file
    tag_positions.append((len(data), 'EOF'))

    files = []
    current_meta = {}
    current_blob = b''

    # Iterate through each pair of tag positions to extract structured sections
    for (start, tag), (next_start, _) in zip(tag_positions, tag_positions[1:]):
        raw = data[start + len(tag):next_start]
        value = raw.split(b'\r')[0].split(b'\n')[0][:1000].strip()

        if tag in {'GUID/', 'FILENAME/', 'EXT/', 'TYPE/', 'SHA1/', 'DOCTYPE/'}:
            current_meta, current_blob = process_metadata_tag(tag, value, current_meta, files, output_dir, current_blob)
        elif tag in {'DOCU/', '_SIG/', 'IMAGE/', 'OADI/'}:
            current_blob, current_meta = accumulate_blob(tag, raw, current_blob, current_meta, files)

    if current_meta and current_blob:
        save_file(current_meta, current_blob, files, output_dir)

    with open(os.path.join(output_dir, 'metadata.json'), 'w') as mf:
        json.dump(files, mf, indent=2)

    logging.info(f"\n Parsed {len(files)} files. Metadata saved to '{output_dir}/metadata.json'")

    if show_summary:
        logging.info("\n Summary:")
        logging.info(tabulate(
            [[f['filename'], f['type'], f['size_bytes']] for f in files],
            headers=["Filename", "Type", "Size (bytes)"],
            tablefmt="github"
        ))

def main():
    # CLI entrypoint for .env archive parsing
    parser = argparse.ArgumentParser(description="Parse proprietary HomeVision .env archive")
    parser.add_argument('--input', '-i', required=True, nargs='+', help="One or more .env files")
    parser.add_argument('--output', '-o', default='final_output', help="Output directory")
    parser.add_argument('--summary', action='store_true', help="Show summary table")
    args = parser.parse_args()

    # Test with few different .env files
    for input_file in args.input:
        parse_env_file(input_file, args.output, args.summary)

if __name__ == "__main__":
    main()
