import os

def split_file_into_chunks(file, num_chunks=2):
    with open(file, 'r', encoding='ascii') as f:
        content = f.read()
    chunk_size = len(content) // num_chunks
    chunks = [content[i*chunk_size:(i+1)*chunk_size] for i in range(num_chunks)]
    if len(content) % num_chunks != 0:
        chunks[-1] += content[num_chunks*chunk_size:]
    return chunks

def save_chunks_to_files(chunks, base_dir):
    # chunks dir inside the script folder
    chunks_dir = os.path.join(base_dir, "chunks")
    os.makedirs(chunks_dir, exist_ok=True)

    for i, chunk in enumerate(chunks, start=1):
        path = os.path.join(chunks_dir, f"chunk_{i}.txt")
        with open(path, 'w', encoding='ascii') as f:
            f.write(chunk)
        print(f"Chunk {i} saved to {path}.")

def main(input_file):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chunks = split_file_into_chunks(input_file, num_chunks=2)
    save_chunks_to_files(chunks, script_dir)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 createChunks.py <input_file>")
        sys.exit(1)
    main(sys.argv[1])