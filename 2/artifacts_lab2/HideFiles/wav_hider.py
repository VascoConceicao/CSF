# script to hide and retrieve secret.pdf after the EOF of input.wav

# program is invoked as follows:
# python hide.py -h or -r <pdf_file> <wav_file>
# -h: hide the pdf file in the wav file
# -r: retrieve the pdf file from the wav file

import sys
import os
import wave 

# ...existing code...

def hide(db_file, wav_file, filename):
    f1 = open(wav_file, "rb")
    f1_data = f1.read()
    f1.close()

    f2 = open(db_file, "rb")
    f2_data = f2.read()
    f2.close()

    out_path = os.path.join(os.getcwd(), filename)
    with open(out_path, "wb") as out_file:
        out_file.write(f1_data)
        out_file.write(f2_data)

    print(f"HIDE: SQLite database hidden in {out_path}")

def show(wav_file):
    f1 = open(wav_file, "rb")
    f1_data = f1.read()
    f1.close()

    # SQLite 3.x magic number
    magic = b'SQLite format 3\x00'

    wav_data = bytearray(f1_data)
    db_index = wav_data.find(magic)
    if db_index == -1:
        print('RETRIEVE: SQLite magic number not found')
        return
    else:
        print('RETRIEVE: SQLite database found at index', db_index)

    # extract the database data from the wav data
    db_data = f1_data[db_index:]

    # write database data to output file
    with open('retrieved_parking.db', 'wb') as db_file:
        db_file.write(db_data)
    
    print('RETRIEVE: Database saved as retrieved_parking.db')

# Update main section to handle database operations
if __name__ == '__main__':
    if len(sys.argv) == 5:
        if sys.argv[1] == '-h':
            hide(sys.argv[2], sys.argv[3], sys.argv[4])
        elif sys.argv[1] == '-hdb':
            hide(sys.argv[2], sys.argv[3], sys.argv[4])
        else:
            print('Invalid option')
    elif len(sys.argv) == 3:    
        if sys.argv[1] == '-s':
            show(sys.argv[2])
        elif sys.argv[1] == '-sdb':
            show(sys.argv[2])
        else:
            print('Invalid option')
    else:
        print('Usage: python script.py -h/-hdb <file> <wav_file> or python script.py -s/-sdb <wav_file>')