"""
Main entry point of zserio pip module.
"""

import sys

import zserio.compiler

def main() -> int:
    """
    Main entry point of zserio pip module.

    This method envokes zserio compilers. It is called if zserio pip module is called on the command line
    (using 'python3 -m zserio').

    :returns: Exit value of zserio compiler.
    """
    completed_process = zserio.run_compiler(sys.argv[1:], capture_output = False)
    sys.exit(completed_process.returncode)

if __name__ == "__main__":
    main()
