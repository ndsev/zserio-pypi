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
    completedProcess = zserio.runCompiler(sys.argv[1:], captureOutput = False)
    sys.exit(completedProcess.returncode)

if __name__ == "__main__":
    main()
