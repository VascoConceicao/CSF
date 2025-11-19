import base64
import argparse

def encode_file_with_hex_and_base64(input_path, output_path):
    # Lê o ficheiro em binário
    with open(input_path, 'rb') as file:
        content = file.read()
    
    # Converte cada byte em hexadecimal (2 dígitos por byte)
    hex_encoded_content = ''.join([f'{b:02x}' for b in content])
    print("Hex encoded (first 200 chars):", hex_encoded_content[:200])  # preview
    
    # Converte a string hex para Base64
    base64_encoded_secret = base64.b64encode(hex_encoded_content.encode('utf-8')).decode('utf-8')

    print("\nBase64 encoded (first 200 chars):", base64_encoded_secret[:200])  # preview
    
    # Escreve o resultado para o ficheiro de saída
    with open(output_path, 'w') as file:
        file.write(base64_encoded_secret)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Encode a file into Hex + Base64 format.")
    parser.add_argument("-i", "--input", required=True, help="Path to the input file (original).")
    parser.add_argument("-o", "--output", required=True, help="Path to the output file (encoded result).")

    args = parser.parse_args()

    encode_file_with_hex_and_base64(args.input, args.output)