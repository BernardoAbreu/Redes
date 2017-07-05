import re

def read_input(input_file):
    pattern = re.compile(r'^\s*([^#\s][^\s]+)\s*([^\s].+[^\s])\s*$')
    with open(input_file, 'r') as file:
        return {line.group(1):line.group(2) for line in map(pattern.match,file) if line is not None}

