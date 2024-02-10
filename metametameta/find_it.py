import os
import re
import importlib
import argparse
from pathlib import Path
from typing import Dict, List, Any

def find_metadata_in_file(file_path: Path) -> Dict[str, Any]:
    """
    Find metadata in a given Python file.
    """
    metadata = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        # Match all possible metadata fields, assuming they follow the format __key__ = value
        matches = re.findall(r"__(\w+)__\s*=\s*['\"]([^'\"]+)['\"]", content)
        for key, value in matches:
            metadata[key] = value
    return metadata

def find_metadata_in_module(module_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Traverse a module/package directory and find metadata in all submodules.
    """
    metadata_results = {}
    for root, dirs, files in os.walk(module_path):
        for file in files:
            if file.endswith('.py') and "about" in file:
                file_path = Path(root) / file
                metadata = find_metadata_in_file(file_path)
                if 'version' in metadata:  # Check if this file has metadata
                    module_name = file_path.relative_to(module_path).with_suffix('')
                    metadata_results[str(module_name).replace(os.sep, '.')] = metadata
    return metadata_results

def main(argv: List[str] = None) -> None:
    parser = argparse.ArgumentParser(description='Find metadata in a Python module/package.')
    parser.add_argument('module', type=str, help='The name of the module/package to inspect.')
    args = parser.parse_args(argv)

    module_name = args.module
    module = importlib.import_module(module_name)
    module_path = Path(module.__file__).parent

    metadata_results = find_metadata_in_module(module_path)
    for submodule, metadata in metadata_results.items():
        print(f'Metadata for {submodule}:')
        for key, value in metadata.items():
            print(f'  {key}: {value}')
        print()

if __name__ == '__main__':
    main(["metametameta"])