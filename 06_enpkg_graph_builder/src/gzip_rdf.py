import gzip
import shutil
import os
import argparse
import textwrap


""" Argument parser """
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
        This script compress to gzip format .rdf files above 200Mb
         --------------------------------
            Arguments:
            - Path to the directory where samples folders are located
            - Minimal size in Mb to compress (default = 200 Mb)
        '''))

parser.add_argument('-p', '--sample_dir_path', required=True,
                    help='The path to the directory where samples folders to process are located')

parser.add_argument('-s', '--size', required=False, default=200,
                    help='The minimal size in Mb of the .ttl files to compress (default = 200 Mb)')

args = parser.parse_args()
sample_dir_path = os.path.normpath(args.sample_dir_path)
size = float(args.size)
path = os.path.join(sample_dir_path, '004_rdf')

for file in os.listdir(path):
    size_mo = os.path.getsize(os.path.join(path, file))/1e+6
    if size_mo >= size:
        with open(os.path.join(path, file), 'rb') as f_in:
            file_out = os.path.join(path, file) + '.gz'
            if not os.path.isfile(file_out):
                print(f'Compressing {f_in}')
                with gzip.open(file_out, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                print(f'{f_in} done')
            else:
                print(f'{file_out} already exists')
    elif size_mo < size:
        print(f'Not an heavy file ! You are OK to go.')
        continue
        
    