# Zserio PyPi package

Zserio PyPi package contains Zserio compiler and Zserio Python runtime. Zserio is serialization framework
available at [GitHub](http://zserio.org).

## Installation

To install Zserio compiler together with Zserio Python runtime, just run

```
pip install zserio
```

## Usage from command line

Consider the following zserio schema which is stored to the source `appl.zs`:

```
package appl;

struct TestStructure
{
    int32 value;
};
```

To compile the schema by compiler and generate Python sources to the directory `gen`, you can run Zserio
compiler directly from command line by the following command:

```
zserio appl.zs -python gen
```

Then, if you run the python by the command

```
PYTHONPATH="gen" python
```

you will be able to use the generated Python sources by the following python commands

```py
import appl.api as api
test_structure = api.TestStructure()
```

## Usage from Python

Consider the following zserio schema which is stored to the source `appl.zs`:

```
package appl;

struct TestStructure
{
    int32 value;
};
```

To compile the schema by compiler and generate Python sources to the directory `gen`, you can run the
following python commands:

```py
import zserio
api = zserio.generate("appl.zs", gen_dir = "gen")
test_structure = api.TestStructure()
```

For convenience, the method `generate` returns imported API for generated top level package.

Alternatively, you can run zserio compiler directly by the following python commands:

```py
import sys
import importlib
import zserio
completed_process = zserio.run_compiler(["appl.zs", "-python", "gen"])
if completed_process.returncode == 0:
    sys.path.append("gen")
    api = importlib.import_module("appl.api")
    test_structure = api.TestStructure()
```

## Building

The easiest way how to build Zserio PyPi package is by using Bash script `build.sh` located in the project's
folder `scripts`:

```
scripts/build.sh
```

## Testing

Testing is available by using Bash script `test.sh` located in the project's folder `scripts`:

```
PYLINT_ENABLED=1 MYPY_ENABLED=1 scripts/test.sh
```
