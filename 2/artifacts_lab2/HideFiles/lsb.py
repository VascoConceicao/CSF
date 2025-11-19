from PIL import Image, ImageColor
from bitstring import BitArray
from argparse import ArgumentParser
import os


def readable_size(value: int) -> str:
    if value < 1024:
        return f"{value}B"
    elif value < 1024**2:
        return f"{value/1024:.2f}KB"
    elif value < 1024**3:
        return f"{value/1024**2:.2f}MB"
    else:
        return f"{value/1024**3:.2f}GB"


def print_progress_bar(current: int, total: int):
    max_size = 80
    bar_size = round(max_size * current / total)
    print(f'[{"■"*bar_size}{"-"*(max_size-bar_size)}] ({readable_size(current)}/{readable_size(total)}){" "*10}', end="\r", flush=True)


def get_new_channel_value(red: int, payload_bits: BitArray, nlsb: int) -> int:
    new_channel = BitArray(red.to_bytes(1, "big"))
    new_channel.overwrite(payload_bits, 8 - nlsb)
    return new_channel.uint


def colors_equal(color1: tuple, color2: tuple) -> bool:
    for i in range(3):  # Ignore alpha channel
        if color1[i] != color2[i]:
            return False
    return True


def color_in_list(color: tuple, color_list: list) -> bool:
    for c in color_list:
        if colors_equal(color, c):
            return True
    return False


def hide_pixel(x: int, y: int, i: int, image: Image.Image, payload_bits: BitArray, nlsb: int, colormode: str, ignored_colors: list) -> int:
    pixel_color = image.getpixel((x, y))
    if color_in_list(pixel_color, ignored_colors):
        return i
    idxs = colormode_idxs(colormode)
    new_pixel_color = pixel_color
    for color_idx in idxs:
        new_channel_value = get_new_channel_value(pixel_color[color_idx], payload_bits[i : i + nlsb], nlsb)
        print_progress_bar(i // 8, payload_bits.length // 8)
        new_pixel_color = new_pixel_color[:color_idx] + (new_channel_value,) + new_pixel_color[color_idx + 1 :]
        i += nlsb
        if i >= len(payload_bits):
            break
    image.putpixel((x, y), new_pixel_color)
    return i


def hide(path_to_original: str, path_to_payload: str, colormode: str, direction: str, nlsb: int, ignored_colors: list):
    image = Image.open(path_to_original)
    output_path = os.path.splitext(path_to_original)[0] + f".png"
    with open(path_to_payload, mode="rb") as file:
        payload_bits = BitArray(file.read())

    max_payload_size = image.width * image.height * nlsb * len(colormode)

    if payload_bits.length > max_payload_size:
        exit(f"Impossible to hide payload ({readable_size(payload_bits.length//8)}) in given file with nlsb={nlsb}, maximum is {readable_size(max_payload_size//8)}")

    i = 0
    if direction in ["horizontal", "vertical"]:
        c1_max = image.width if direction == "vertical" else image.height
        c2_max = image.height if direction == "vertical" else image.width
        for c1 in range(c1_max):
            for c2 in range(c2_max):
                x = c1 if direction == "vertical" else c2
                y = c2 if direction == "vertical" else c1
                i = hide_pixel(x, y, i, image, payload_bits, nlsb, colormode, ignored_colors)
                if i >= len(payload_bits):
                    image.save(output_path)
                    image.close()
                    print("\nDone! Successfully encoded payload in image! See " + output_path)
                    return
    elif direction in ["diagonalup", "diagonaldown"]:
        c1_max = image.width if direction == "diagonalup" else image.height
        c2_max = image.height if direction == "diagonalup" else image.width
        for diag in range(image.width + image.height - 1):
            for c1 in range(c1_max):
                c2 = diag - c1
                if c2 < 0 or c2 >= c2_max:
                    continue
                x = c1 if direction == "diagonalup" else c2
                y = c2 if direction == "diagonalup" else c1
                i = hide_pixel(x, y, i, image, payload_bits, nlsb, colormode, ignored_colors)
                if i >= len(payload_bits):
                    image.save(output_path)
                    image.close()
                    print("\nDone! Successfully encoded payload in image! See " + output_path)
                    return

    print("\nUnable to encode full payload in image, saving what we can in " + output_path)
    image.save(output_path)
    image.close()


def extract_payload_bits(color_value: int, nlsb: int) -> BitArray:
    channel_bits = BitArray(color_value.to_bytes(1, "big"))
    return channel_bits[8 - nlsb :]


def solve_pixel(x: int, y: int, image: Image.Image, payload_bits: BitArray, nlsb: int, colormode: str, ignored_colors: list):
    pixel_color = image.getpixel((x, y))
    if color_in_list(pixel_color, ignored_colors):
        return
    idxs = colormode_idxs(colormode)
    for color_idx in idxs:
        payload_bits.append(extract_payload_bits(pixel_color[color_idx], nlsb))


def solve(path_to_stego: str, path_to_output: str, colormode: str, direction: str, file_ext: str, nlsb: int, ignored_colors: list):
    original = Image.open(path_to_stego)
    payload_bits = BitArray()

    total_bytes = original.height * original.width * nlsb * len(colormode) // 8

    if direction in ["horizontal", "vertical"]:
        c1_max = original.width if direction == "vertical" else original.height
        c2_max = original.height if direction == "vertical" else original.width
        for c1 in range(c1_max):
            for c2 in range(c2_max):
                x = c1 if direction == "vertical" else c2
                y = c2 if direction == "vertical" else c1
                solve_pixel(x, y, original, payload_bits, nlsb, colormode, ignored_colors)
                print_progress_bar(payload_bits.length // 8, total_bytes)
    elif direction in ["diagonalup", "diagonaldown"]:
        c1_max = original.width if direction == "diagonalup" else original.height
        c2_max = original.height if direction == "diagonalup" else original.width
        for diag in range(original.width + original.height - 1):
            for c1 in range(c1_max):
                c2 = diag - c1
                if c2 < 0 or c2 >= c2_max:
                    continue
                x = c1 if direction == "diagonalup" else c2
                y = c2 if direction == "diagonalup" else c1
                solve_pixel(x, y, original, payload_bits, nlsb, colormode, ignored_colors)
                print_progress_bar(payload_bits.length // 8, total_bytes)
    with open(path_to_output, mode="wb") as file:
        extra_bits = payload_bits.length % 8
        if extra_bits != 0:
            payload_bits = payload_bits[: payload_bits.length - extra_bits]

        if file_ext == "png":
            endidx = payload_bits.bytes.rfind(b"\x49\x45\x4E\x44") + 8
        elif file_ext in ["jpg", "jpeg"]:
            endidx = payload_bits.bytes.rfind(b"\xFF\xD9") + 2
        elif file_ext == "pdf":
            endidx = payload_bits.bytes.rfind(b"\x25\x25\x45\x4F\x46") + 5
        else:
            endidx = len(payload_bits.bytes)
        file.write(payload_bits.bytes[:endidx])


def colormode_idx(mode: str):
    if mode == "r":
        return 0
    elif mode == "g":
        return 1
    elif mode == "b":
        return 2
    else:
        exit("Invalid color")

def colormode_idxs(mode: str):
    idxs: list = []
    for c in mode:
        idxs.append(colormode_idx(c))
    return idxs

def parse_colors_csv(csv: str):
    colors = []
    for hex in csv.split(";"):
        if hex == "":
            continue
        if not hex.startswith("#"):
            hex = "#" + hex
        colors.append(ImageColor.getrgb(hex))
    return colors


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-m", "--mode", type=str, help="Mode to use (Default: hide)", choices=["hide", "solve"], default="hide")
    parser.add_argument("-d", "--direction", type=str, help="Direction to use", choices=["horizontal", "vertical", "diagonalup", "diagonaldown"], default="horizontal")
    parser.add_argument("-c", "--colormode", type=str, help="Color mode to use", required=True, choices=["r", "g", "b", "rg", "gr", "gb", "bg", "br", "rb", "rgb", "rbg", "grb", "gbr", "brg", "bgr"])
    parser.add_argument("-n", "--nlsb", type=int, help="Number of least significant bits to use", required=True)
    parser.add_argument("-i", "--ignore", type=str, help="Colors to ignore in CSV format: HEX;HEX;...", default="", required=False)
    parser.add_argument("-o", "--original", type=str, help="(h) Path to original image / (s) Path to stego image", required=True)
    parser.add_argument("-p", "--payload", type=str, help="(h) Path to payload / (s) Path to output payload", required=False, default="payload")
    parser.add_argument("-e", "--extension", type=str, help="(s) File extension of payload", required=False, default="")
    args = parser.parse_args()

    ignored_colors = parse_colors_csv(args.ignore)
    if args.mode == "hide":
        if args.original is None or args.payload is None or args.colormode is None or args.nlsb is None or args.ignore is None or args.direction is None:
            parser.print_help()
            print("Missing required arguments")
            exit(1)
        hide(args.original, args.payload, args.colormode, args.direction, args.nlsb, ignored_colors)
    else:
        if args.original is None or args.payload is None or args.colormode is None or args.nlsb is None or args.direction is None:
            parser.print_help()
            print("Missing required arguments")
            exit(1)
        solve(args.original, args.payload, args.colormode, args.direction, args.extension.lower(), args.nlsb, ignored_colors)
