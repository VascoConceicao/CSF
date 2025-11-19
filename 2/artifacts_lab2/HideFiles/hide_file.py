import os
import argparse

def merge_files(file_a, file_b, file_c):
    # Ensure the artifact directory exists (if any)
    artifact_dir = os.path.dirname(file_a)
    if artifact_dir and not os.path.exists(artifact_dir):
        os.makedirs(artifact_dir)

    # Ensure the output directory exists (if any)
    output_dir = os.path.dirname(file_b)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Ensure file B exists
    if not os.path.exists(file_b):
        with open(file_b, 'wb') as fb:
            pass

    try:
        # Read the first 64 bytes from file A
        with open(file_a, 'rb') as fa:
            a_data = fa.read(64)
        
        # Write the first 64 bytes to file B
        with open(file_b, 'ab') as fb:
            fb.write(a_data)
        
        # Read the contents of file C
        with open(file_c, 'rb') as fc:
            c_data = fc.read()
        
        # Write the contents of file C to file B, starting from the position after the first 64 bytes
        with open(file_b, 'ab') as fb:
            fb.write(c_data)
        
        print("Operation completed successfully.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except IOError as e:
        print(f"An error occurred while processing files: {e}")
    finally:
        print("File operations finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge first 64 bytes of file A with contents of file C into file B.")
    parser.add_argument("-a", "--file_a", required=True, help="Path to input file A (source of first 64 bytes).")
    parser.add_argument("-b", "--file_b", required=True, help="Path to output file B (result).")
    parser.add_argument("-c", "--file_c", required=True, help="Path to input file C (to append after 64 bytes).")

    args = parser.parse_args()

    merge_files(args.file_a, args.file_b, args.file_c)