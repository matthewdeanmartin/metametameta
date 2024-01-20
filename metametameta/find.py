"""
Find metadata in a module file.
"""
import inspect
import os
import re


def get_module_file(module):
    """Get the file associated with a module."""
    return inspect.getfile(module)


def is_package(module):
    """Check if a module is a package."""
    module_file = get_module_file(module)
    return os.path.basename(module_file) == "__init__.py"


def get_meta(module_file):
    """Extract metadata from the module file."""
    metadata = {}
    if module_file and os.path.isfile(module_file):
        with open(module_file, encoding="utf-8") as file:
            content = file.read()

        # Define a regex pattern to match metadata variables
        pattern = r"__(\w+)__\s*=\s*['\"]([^'\"]+)['\"]"
        matches = re.findall(pattern, content)

        for key, value in matches:
            metadata[key] = value
    return metadata


# # Usage example:
# try:
#     # ... some code that raises CustomError ...
#     raise CustomError("An error occurred")
# except CustomError as ce:
#     module = get_module(ce)
#     module_file = get_module_file(module)
#     metadata = get_meta(module_file)
#     print(metadata)
