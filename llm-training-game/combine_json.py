#!/usr/bin/env python
import json
import sys

def combine_json_files(input_files, output_file):
    """Combine JSON array files into a single JSON array file."""
    combined_data = []
    
    for file_path in input_files:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                combined_data.extend(data)
            else:
                print(f"Warning: {file_path} does not contain a JSON array")
    
    with open(output_file, 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print(f"Combined {len(input_files)} files into {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python combine_json.py output_file.json input1.json input2.json [input3.json ...]")
        sys.exit(1)
    
    output_file = sys.argv[1]
    input_files = sys.argv[2:]
    
    combine_json_files(input_files, output_file)