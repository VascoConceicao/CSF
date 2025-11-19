from argparse import ArgumentParser

def hide(input_file: str) -> str:
    try:
        # Read the file in binary mode
        with open(input_file, 'rb') as f:
            content = f.read()

        # Convert bytes to binary string
        binary = ''.join(format(byte, '08b') for byte in content)

        # Replace 0s with '.' and 1s with '-'
        converted = binary.replace('0', '.').replace('1', '-')

        return converted

    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-i", "--input", type=str, help="Input file path", required=True)
    parser.add_argument("-o", "--output", type=str, help="Output file path", required=True)
    args = parser.parse_args()

    result = hide(args.input)
    try:
        with open(args.output, "w", encoding="ascii") as f:
            f.write(result)
        print(f"Successful save in {args.output}")
    except Exception as e:
        print(f"Error saving file: {str(e)}")