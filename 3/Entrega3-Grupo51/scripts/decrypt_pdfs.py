"""
PDF Deobfuscation and Recovery Script
-------------------------------------

This script is designed to recover obfuscated PDF files from intercepted HTTP POST requests
that contain Base64-encoded data (typically from a "file=" parameter in a POST body).
It uses known plaintext attacks and repeating XOR analysis to decrypt the file.

Workflow:
1. Reads an input `.txt` file containing the intercepted POST data.
2. Extracts the value of the `file=` parameter.
3. URL-decodes and Base64-decodes it to obtain the obfuscated binary data.
4. If a known original version of the PDF exists (known plaintext), computes a keystream by XORing
   the obfuscated data with the known PDF bytes.
5. Applies the keystream to decrypt the obfuscated file.
6. If the PDF header (“%PDF-”) is not found, tries to brute-force a repeating XOR key (up to 8 bytes).
7. Appends a valid PDF trailer (from the known original) if missing.
8. Saves the recovered PDF file.
9. Cleans up temporary intermediate files.

Configurable parameters:
- `which_one`: Selects between `pdf1.txt` (Financial Report) and `pdf2.txt` (Invoice).
- `MAX_REPXOR_KEYLEN`: Maximum key length to try in repeating XOR search.
- `MAX_REPXOR_OFFSET`: Maximum offset to search for the PDF header.

Outputs:
- A fully recovered and readable PDF file (named `_recovered.pdf`).
- JSON summary printed to stdout, showing input and output paths.

Example usage:
$ python3 recover_pdf.py

Dependencies:
- Python 3.6+
- Standard library modules only (no external dependencies)
"""

# config
which_one = 2  # 1 or 2

from pathlib import Path
from urllib.parse import unquote_plus
import re, base64, json

# Base directory (one level up from scripts/)
BASE_DIR = Path(__file__).resolve().parents[1]
DISCOVERIES_DIR = BASE_DIR / "discoveries" / "pdfs"

# Inputs
POST_TXT_PATH = DISCOVERIES_DIR / f"pdf{which_one}.txt"
if which_one == 1:
    KNOWN_PLAINTEXT_PDF = DISCOVERIES_DIR / "FinancialReport_original.pdf"
else:
    KNOWN_PLAINTEXT_PDF = DISCOVERIES_DIR / "Invoice_original.pdf"

# Output uses the original name automatically
OUT_DEOBF_PDF = DISCOVERIES_DIR / KNOWN_PLAINTEXT_PDF.name.replace("_original", "_recovered")

# Temporary files (auto-deleted later)
OUT_RAW_BIN = DISCOVERIES_DIR / f"pdf{which_one}_decoded.bin"
OUT_KEYSTREAM_BIN = DISCOVERIES_DIR / f"pdf{which_one}_keystream.bin"
OUT_REPXOR_KEY_HEX = DISCOVERIES_DIR / f"pdf{which_one}_repxor.hex"

MAX_REPXOR_KEYLEN = 8
MAX_REPXOR_OFFSET = 512
TRAILER_SOURCE_PDF = KNOWN_PLAINTEXT_PDF

def log(msg): print(msg)

# --- Core functions ---

def extract_file_param_from_txt(txtpath: Path):
    s = txtpath.read_text(errors="ignore")
    m = re.search(r'file=([^&\s]+)', s)
    if not m:
        raise SystemExit(f"No 'file=' parameter found in {txtpath}")
    return m.group(1)

def urldecode_and_b64decode(s: str):
    ud = unquote_plus(s)
    b = ud.encode('utf-8')
    b = b"".join(b.split())
    try:
        return base64.b64decode(b, validate=True)
    except Exception:
        pad = (-len(b)) % 4
        try:
            return base64.b64decode(b + b"=" * pad)
        except Exception:
            filtered = re.sub(rb'[^A-Za-z0-9+/=]', b'', b)
            pad = (-len(filtered)) % 4
            return base64.b64decode(filtered + b"=" * pad)

def write_recovered_bin():
    enc = extract_file_param_from_txt(POST_TXT_PATH)
    raw = urldecode_and_b64decode(enc)
    OUT_RAW_BIN.write_bytes(raw)
    log(f"[+] Decoded POST -> {OUT_RAW_BIN} ({len(raw)} bytes)")
    return OUT_RAW_BIN

def compute_keystream_known_plain(recovered_bin: Path, known_plain: Path):
    c = recovered_bin.read_bytes()
    p = known_plain.read_bytes()
    n = min(len(c), len(p))
    ks = bytes([c[i] ^ p[i] for i in range(n)])
    OUT_KEYSTREAM_BIN.write_bytes(ks)
    log(f"[+] Keystream computed -> {OUT_KEYSTREAM_BIN}")
    return OUT_KEYSTREAM_BIN

def repeating_xor_search(recovered_bin: Path, max_keylen=8, max_offset=512, target=b"%PDF-"):
    data = recovered_bin.read_bytes()
    n = len(data)
    for offset in range(0, min(max_offset, n - len(target)) + 1):
        for klen in range(1, max_keylen + 1):
            key = bytearray(klen)
            for j in range(len(target)):
                key[j % klen] = data[offset + j] ^ target[j]
            sample_len = min(4096, n)
            decoded_sample = bytearray(sample_len)
            for i in range(sample_len):
                decoded_sample[i] = data[i] ^ key[i % klen]
            if target in decoded_sample:
                OUT_REPXOR_KEY_HEX.write_text(key.hex())
                log(f"[+] Found repeating XOR key: {key.hex()} (len={klen}, offset={offset})")
                return key.hex()
    return None

def apply_xor(cipher: bytes, key: bytes) -> bytes:
    klen = len(key)
    return bytes([cipher[i] ^ key[i % klen] for i in range(len(cipher))])

def extract_trailer_bytes(pdf_path: Path):
    b = pdf_path.read_bytes()
    for marker in [b"startxref", b"%EOF"]:
        idx = b.rfind(marker)
        if idx != -1:
            return b[idx:]
    return None

def append_trailer(source_pdf: Path, target_bytes: bytes) -> bytes:
    trailer = extract_trailer_bytes(source_pdf)
    if trailer and b"%EOF" not in target_bytes[-1024:]:
        log("[+] Appended trailer from source PDF.")
        return target_bytes + trailer
    return target_bytes

def cleanup_temp_files():
    for f in [OUT_RAW_BIN, OUT_KEYSTREAM_BIN, OUT_REPXOR_KEY_HEX]:
        try:
            if f.exists():
                f.unlink()
                log(f"[-] Deleted temp file: {f.name}")
        except Exception:
            pass

# --- Main flow ---

def main():
    recovered_bin = write_recovered_bin()
    c_bytes = recovered_bin.read_bytes()

    ks_path = compute_keystream_known_plain(recovered_bin, KNOWN_PLAINTEXT_PDF)
    ks = ks_path.read_bytes()
    decrypted = apply_xor(c_bytes, ks)

    if b"%PDF-" not in decrypted[:1024]:
        log("[!] Keystream method didn’t reveal PDF header. Trying repeating-XOR search...")
        key_hex = repeating_xor_search(recovered_bin, MAX_REPXOR_KEYLEN, MAX_REPXOR_OFFSET)
        if key_hex:
            decrypted = apply_xor(c_bytes, bytes.fromhex(key_hex))

    decrypted = append_trailer(TRAILER_SOURCE_PDF, decrypted)
    OUT_DEOBF_PDF.write_bytes(decrypted)
    log(f"[+] Final recovered PDF written to {OUT_DEOBF_PDF}")

    cleanup_temp_files()

    summary = {
        "which_one": which_one,
        "input": str(POST_TXT_PATH),
        "original": str(KNOWN_PLAINTEXT_PDF),
        "output_pdf": str(OUT_DEOBF_PDF)
    }
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()