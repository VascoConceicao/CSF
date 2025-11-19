import struct, os

WAV = "/Users/vasco/Library/CloudStorage/OneDrive-UniversidadedeLisboa/Universidade/4ºAno/1ºSemestre/CiberSegurancaForense/Projeto/Lab1/zyra.csf.syssec.dpss.inesc-id.pt/resources/MingleGame.wav"         # change if needed
OUT_CHUNK = "../Outputs/MingleGame_SQLi_chunk.bin"
OUT_DB    = "../Outputs/MingleGame_hidden.db"

CANONICAL_HDR = b"SQLite format 3\x00"  # 16 bytes

def extract_sql_chunk(wav_path):
    data = open(wav_path, "rb").read()
    if data[:4] != b"RIFF":
        raise SystemExit("Not a RIFF file")
    # skip RIFF header (12 bytes)
    offset = 12
    while offset + 8 <= len(data):
        fourcc = data[offset:offset+4]
        size = struct.unpack("<I", data[offset+4:offset+8])[0]
        start = offset + 8
        end = start + size
        if fourcc == b"SQLi":
            return data[start:end]
        # move to next chunk (chunks are word-aligned)
        offset = end + (size & 1)  # pad if size odd
    return None

def repair_and_write(chunk_bytes, out_db_path):
    # Try to find the substring "format 3\x00" inside the chunk.
    needle = b"format 3\x00"
    pos = chunk_bytes.find(needle)
    if pos != -1:
        # the chunk already contains "format 3\0" starting at pos, so
        # header prefix should be CANONICAL_HDR[:pos]
        prefix_needed = CANONICAL_HDR[:pos]
        print(f"Found 'format 3\\x00' at offset {pos} inside chunk; will prepend {len(prefix_needed)} byte(s).")
        repaired = prefix_needed + chunk_bytes
    else:
        # fallback: if chunk already begins with 'ormat 3' (shifted)
        if chunk_bytes.startswith(b"ormat 3"):
            # e.g., our case. 'SQLite f' length is len("SQLite f") == 8
            prefix_needed = CANONICAL_HDR[:8]  # "SQLite f"
            print("Chunk starts with 'ormat 3' — will prepend first 8 bytes of canonical header ('SQLite f').")
            repaired = prefix_needed + chunk_bytes
        else:
            # If detection fails, prepend the entire canonical header (may duplicate if present)
            print("No obvious 'format 3' found. Prepending full canonical header (may produce invalid DB if wrong).")
            repaired = CANONICAL_HDR + chunk_bytes

    with open(out_db_path, "wb") as f:
        f.write(repaired)
    print(f"Wrote repaired DB to: {out_db_path}")
    return out_db_path

def main():
    if not os.path.exists(WAV):
        raise SystemExit(f"{WAV} not found.")
    chunk = extract_sql_chunk(WAV)
    if not chunk:
        raise SystemExit("No SQLi chunk found in WAV.")
    print("Extracted SQLi chunk length:", len(chunk))
    with open(OUT_CHUNK, "wb") as f:
        f.write(chunk)
    print("Saved raw chunk to", OUT_CHUNK)
    repair_and_write(chunk, OUT_DB)

if __name__ == "__main__":
    main()
