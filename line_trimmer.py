#!/usr/bin/env python3
"""
Script to keep only the first 500 lines of a file.
Usage: python script.py input_file.txt [output_file.txt]
"""

import sys

def keep_first_500_lines(input_file, output_file=None):
    """
    Keep only the first 500 lines of a file.
    
    Args:
        input_file (str): Path to the input file
        output_file (str, optional): Path to output file. If None, overwrites input file.
    """
    try:
        # Read first 500 lines
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= 10000:
                    break
                lines.append(line)
        
        # Determine output file
        if output_file is None:
            output_file = input_file
        
        # Write the lines to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"Successfully kept first {len(lines)} lines")
        if output_file != input_file:
            print(f"Output saved to: {output_file}")
        else:
            print(f"File {input_file} has been updated")
            
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
    except Exception as e:
        print(f"Error: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py input_file.txt [output_file.txt]")
        print("If output_file is not provided, the input file will be overwritten")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    keep_first_500_lines(input_file, output_file)

if __name__ == "__main__":
    main()
