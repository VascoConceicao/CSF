import hashlib
from typing import Dict


seed0 = "TheByteOf78"
seed76 = "6b508266ad2ab9fd7fef0ecfca4b9d874ed3e0362bbf92cf2b269b0f632f452b"


timestamp_map = {
    75: "1758588601",
    74: "1758589201",
    73: "1758588001",
    72: "1758587401",
    71: "1758586801",
    70: "1758586202",
    69: "1758585623",
    68: "1758495226",
}

n_zip = tuple(timestamp_map.keys())


def main() -> None:
    s = seed0

    out_path = "passwordsZips.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        for i in range(1, 77):
            s = hashlib.sha256(s.encode("utf-8")).hexdigest()
            if i in n_zip:
                ts = timestamp_map[i]
                pw = hashlib.sha256((s + ts).encode("utf-8")).hexdigest()
                print(f"i={i} pw: {pw}")
                f.write(f"i={i} {pw}\n")

    print("seed_76 matches target?", s == seed76)


if __name__ == "__main__":
    main()
