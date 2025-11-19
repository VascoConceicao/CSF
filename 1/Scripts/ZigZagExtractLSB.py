from PIL import Image
import numpy as np
from pathlib import Path
import sys


def diagonal_topfirst_bottomstart_indices(rows, cols):
    """
    Diagonals ordered from top-left (top row left→right, then right column top→bottom),
    but within each diagonal start at its bottom-left and move up-right.
    """
    idx = []
    total_diagonals = rows + cols - 1
    for s in range(total_diagonals):
        r = min(s, rows - 1)  # bottom-most row on this diagonal
        c = s - r  # corresponding col
        while r >= 0 and c < cols:
            idx.append((r, c))
            r -= 1
            c += 1
    return np.array(idx, dtype=np.int64)


def extract_lsb4_stream(img_array, channel_order="RGB", nibble_pair="highfirst"):
    """Return bytes packed from 4 LSBs of each channel in zig-zag pixel order."""
    h, w, *_ = img_array.shape  # Fixed: was img*array.shape
    order_map = {"R": 0, "G": 1, "B": 2}
    ch_idx = [order_map[c] for c in channel_order]

    # Zig-zag pixel order
    coords = diagonal_topfirst_bottomstart_indices(h, w)

    # Reorder pixels and channels to a (N_pixels*3,) flat array
    zz = img_array[coords[:, 0], coords[:, 1]][:, ch_idx].reshape(-1).astype(np.uint8)

    # Keep only low 4 bits (nibbles)
    nibs = zz & 0x0F

    # Pack two nibbles -> one byte
    if len(nibs) % 2 == 1:
        nibs = nibs[:-1]

    if nibble_pair == "highfirst":
        by = (nibs[0::2] << 4) | nibs[1::2]
    else:
        by = (nibs[1::2] << 4) | nibs[0::2]

    return by.tobytes()


def main():
    default_path = "../zyra.csf.syssec.dpss.inesc-id.pt/resources/RaceCar.png"
    img_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(default_path)

    # optional crop size (square from top-left)
    crop = None
    if len(sys.argv) > 2:
        try:
            crop = int(sys.argv[2])
            if crop <= 0:
                crop = None
        except ValueError:
            crop = None

    img = Image.open(img_path).convert("RGB")
    arr = np.array(img, dtype=np.uint8)

    if crop is not None:
        arr = arr[:crop, :crop, :]

    data = extract_lsb4_stream(arr, channel_order="RGB", nibble_pair="highfirst")

    out_dir = Path("../Outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    Path(out_dir / "RaceCar_hidden.bin").write_bytes(data)

    print(f"Wrote {len(data)} bytes to {out_dir / 'RaceCar_hidden.bin'} (crop={crop})")


if __name__ == "__main__":
    main()
3
