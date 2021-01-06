#!/bin/bash

# Source build-env.sh if found.
SCRIPT_DIR=`dirname $0`
if [ -e "${SCRIPT_DIR}/build-env.sh" ] ; then
    source "${SCRIPT_DIR}/build-env.sh"
fi

# Set and check global variables for tests.
set_global_variables()
{
    PYTHON_VIRTUALENV="${PYTHON_VIRTUALENV:-""}"

    if [ -z "${PYTHON_VIRTUALENV}" ] ; then
        # python to use, defaults to "python3" if not set
        PYTHON="${PYTHON:-python3}"
        if [ ! -f "`which "${PYTHON}"`" ] ; then
            stderr_echo "Cannot find Python! Set PYTHON environment variable."
            return 1
        fi

        # check python version
        check_python_version ${PYTHON}
        if [ $? -ne 0 ] ; then
            return 1
        fi

        # check that python pip and virtualenv modules are installed
        local PYTHON_REQUIREMENTS=("virtualenv" "pip")
        check_python_requirements "${PYTHON}" PYTHON_REQUIREMENTS[@]
        if [ $? -ne 0 ] ; then
            return 1
        fi
    fi

    return 0
}

# Print help on the environment variables used for tests.
print_global_help_env()
{
    cat << EOF
Uses the following environment variables:
    PYTHON_VIRTUALENV  Custom python virtualenv to use. Default is empty string.
    PYTHON             Python 3.5+ executable. Default is "python".

    Either set these directly, or create 'scripts/build-env.sh' that sets
    these. It's sourced automatically if it exists.

EOF
}

# Check python version.
check_python_version()
{
    exit_if_argc_ne $# 1
    local PYTHON_BIN="$1"; shift

    local PYTHON_VERSION=$(${PYTHON_BIN} -V 2>&1 | cut -d\  -f 2)
    PYTHON_VERSION=(${PYTHON_VERSION//./ }) # python version as an array
    if [[ ${#PYTHON_VERSION[@]} -lt 2 || ${PYTHON_VERSION[0]} -lt 3 ]] ||
       [[ ${PYTHON_VERSION[0]} -eq 3 && ${PYTHON_VERSION[1]} -lt 5 ]] ; then
        stderr_echo "Python 3.5+ is required! Current Python is '$(${PYTHON_BIN} -V 2>&1)'"
        return 1
    fi

    return 0
}

# Check python requirements.
check_python_requirements()
{
    exit_if_argc_ne $# 2
    local PYTHON_BIN="$1"; shift
    local MSYS_WORKAROUND_TEMP=("${!1}"); shift
    local PYTHON_REQUIREMENTS=("${MSYS_WORKAROUND_TEMP[@]}")

    "${PYTHON_BIN}" << EOF
try:
    import sys
    import pkg_resources
    reqs = "${PYTHON_REQUIREMENTS[@]}".split()
    pkg_resources.require(reqs)
except Exception as e:
    print(e, file=sys.stderr)
    exit(1)
EOF
    if [ $? -ne 0 ] ; then
        stderr_echo "Required python packages are not installed!"
        return 1
    fi
}

# Detect path to python virtualenv activate scripts which differs on Linux and Windows.
detect_python_virtualenv_activate()
{
    exit_if_argc_ne $# 2
    local PYTHON_VIRTUALENV_ROOT="$1"; shift
    local PYTHON_VIRTUALENV_ACTIVATE_OUT="$1"; shift

    local ACTIVATE=
    if [ -f "${PYTHON_VIRTUALENV_ROOT}/bin/activate" ] ; then
        ACTIVATE="${PYTHON_VIRTUALENV_ROOT}/bin/activate"
    elif [ -f "${PYTHON_VIRTUALENV_ROOT}/Scripts/activate" ] ; then
        ACTIVATE="${PYTHON_VIRTUALENV_ROOT}/Scripts/activate"
    fi

    eval ${PYTHON_VIRTUALENV_ACTIVATE_OUT}="'${ACTIVATE}'"
}

# Activate python virtualenv.
#
# When PYTHON_VIRTUALENV is set, just try to use it and check that it fullfils all given requirements.
# When PYTHON_VIRTUALENV is not set, try to create new python virtualenv and install all required packages.
activate_python_virtualenv()
{
    exit_if_argc_ne $# 2
    local BUILD_DIR="$1"; shift
    local MSYS_WORKAROUND_TEMP=("${!1}"); shift
    local PYTHON_REQUIREMENTS=("${MSYS_WORKAROUND_TEMP[@]}")

    local PYTHON_VIRTUALENV_ROOT="${PYTHON_VIRTUALENV:-"${BUILD_DIR}/pyenv"}"
    echo "Activating python virtualenv '${PYTHON_VIRTUALENV_ROOT}'."

    local PYTHON_VIRTUALENV_ACTIVATE
    detect_python_virtualenv_activate "${PYTHON_VIRTUALENV_ROOT}" PYTHON_VIRTUALENV_ACTIVATE

    if [ ! -z "${PYTHON_VIRTUALENV}" ] ; then # forced python virtualenv
        if [ -z "${PYTHON_VIRTUALENV_ACTIVATE}" ] ; then
            stderr_echo "Failed to find virtualenv activate script in '${PYTHON_VIRTUALENV_ROOT}'!"
            return 1
        fi
    else
        if [ -z "${PYTHON_VIRTUALENV_ACTIVATE}" ] ; then
            "${PYTHON}" -m virtualenv -p "${PYTHON}" "${PYTHON_VIRTUALENV_ROOT}"
            if [ $? -ne 0 ] ; then
                stderr_echo "Failed to create virtualenv!"
                return 1
            fi

            detect_python_virtualenv_activate "${PYTHON_VIRTUALENV_ROOT}" PYTHON_VIRTUALENV_ACTIVATE
            if [ -z "${PYTHON_VIRTUALENV_ACTIVATE}" ] ; then
                stderr_echo "Failed to find virtualenv activate script in '${PYTHON_VIRTUALENV_ROOT}'!"
                return 1
            fi
        fi
    fi

    source "${PYTHON_VIRTUALENV_ACTIVATE}"
    if [ $? -ne 0 ] ; then
        stderr_echo "Failed to activate virtualenv!"
        return 1
    fi

    check_python_version python
    if [ $? -ne 0 ] ; then
        return 1
    fi

    if [ ! -z "${PYTHON_VIRTUALENV}" ] ; then  # forced python virtualenv
        check_python_requirements python PYTHON_REQUIREMENTS[@]
        if [ $? -ne 0 ] ; then
            return 1
        fi
    else
        check_python_requirements python PYTHON_REQUIREMENTS[@] 2> /dev/null
        if [ $? -ne 0 ] ; then
            # don't use only pip because it doesn't support spaces in path (https://github.com/pypa/pip/issues/923)
            python -m pip install ${PYTHON_REQUIREMENTS[@]}
            if [ $? -ne 0 ] ; then
                stderr_echo "Failed to install python requirements!"
                return 1
            fi
        fi
    fi

    return 0
}

# Deactivate python virtualenv.
deactivate_python_virtualenv()
{
    exit_if_argc_ne $# 1
    local BUILD_DIR="$1"; shift

    local PYTHON_VIRTUALENV_ROOT="${PYTHON_VIRTUALENV:-"${BUILD_DIR}/pyenv"}"
    echo "Deactivating python virtualenv '${PYTHON_VIRTUALENV_ROOT}'."
    deactivate
}

# Print a message to stderr.
stderr_echo()
{
    echo "FATAL ERROR - $@" 1>&2
}

# Exit if number of input arguments is not equal to number required by function.
#
# Usage:
# ------
# exit_if_argc_ne $# 2
#
# Return codes:
# -------------
# 0 - Always success. In case of failure, function exits with error code 3.
exit_if_argc_ne()
{
    local NUM_OF_ARGS=2
    if [ $# -ne ${NUM_OF_ARGS} ] ; then
        stderr_echo "${FUNCNAME[0]}() called with $# arguments but ${NUM_OF_ARGS} is required."
        exit 3
    fi

    local NUM_OF_CALLER_ARGS=$1; shift
    local REQUIRED_NUM_OF_CALLED_ARGS=$1; shift
    if [ ${NUM_OF_CALLER_ARGS} -ne ${REQUIRED_NUM_OF_CALLED_ARGS} ] ; then
        stderr_echo "${FUNCNAME[1]}() called with ${NUM_OF_CALLER_ARGS} arguments but ${REQUIRED_NUM_OF_CALLED_ARGS} is required."
        exit 3
    fi
}

# Exit if number of input arguments is less than number required by function.
#
# Usage:
# ------
# exit_if_argc_lt $# 2
#
# Return codes:
# -------------
# 0 - Always success. In case of failure, function exits with error code 3.
exit_if_argc_lt()
{
    local NUM_OF_ARGS=2
    if [ $# -ne ${NUM_OF_ARGS} ] ; then
        stderr_echo "${FUNCNAME[0]}() called with $# arguments but ${NUM_OF_ARGS} is required."
        exit 3
    fi

    local NUM_OF_CALLER_ARGS=$1; shift
    local REQUIRED_NUM_OF_CALLED_ARGS=$1; shift
    if [ ${NUM_OF_CALLER_ARGS} -lt ${REQUIRED_NUM_OF_CALLED_ARGS} ] ; then
        stderr_echo "${FUNCNAME[1]}() called with ${NUM_OF_CALLER_ARGS} arguments but ${REQUIRED_NUM_OF_CALLED_ARGS} is required."
        exit 3
    fi
}

# Convert input argument to absolute path.
convert_to_absolute_path()
{
    exit_if_argc_ne $# 2
    local PATH_TO_CONVERT="$1"; shift
    local ABSOLUTE_PATH_OUT="$1"; shift

    local DIR_TO_CONVERT="${PATH_TO_CONVERT}"
    local FILE_TO_CONVERT=""
    if [ ! -d "${DIR_TO_CONVERT}" ] ; then
        DIR_TO_CONVERT="${PATH_TO_CONVERT%/*}"
        FILE_TO_CONVERT="${PATH_TO_CONVERT##*/}"
        if [[ "${DIR_TO_CONVERT}" == "${FILE_TO_CONVERT}" ]] ; then
            DIR_TO_CONVERT="."
        else
            if [ ! -d "${DIR_TO_CONVERT}" ] ; then
                stderr_echo "${FUNCNAME[0]}() called with a non-existing directory ${DIR_TO_CONVERT}!"
                return 1
            fi
        fi
    fi

    pushd "${DIR_TO_CONVERT}" > /dev/null
    # don't use "`pwd`" here because it does not work if path contains spaces
    local ABSOLUTE_PATH="'`pwd`'"
    popd > /dev/null

    if [ -n "${FILE_TO_CONVERT}" ] ; then
        ABSOLUTE_PATH="${ABSOLUTE_PATH}/${FILE_TO_CONVERT}"
    fi

    eval ${ABSOLUTE_PATH_OUT}="${ABSOLUTE_PATH}"

    return 0
}

# Run pylint on given python sources.
run_pylint()
{
    if [[ ${PYLINT_ENABLED} != 1 ]] ; then
        echo "Pylint is disabled."
        echo
        return 0
    fi

    exit_if_argc_lt $# 3
    local PYLINT_RCFILE="$1"; shift
    local MSYS_WORKAROUND_TEMP=("${!1}"); shift
    local PYLINT_ARGS=("${MSYS_WORKAROUND_TEMP[@]}")
    local SOURCES=("$@")

    python -m pylint --init-hook="import sys; sys.setrecursionlimit(5000)" ${PYLINT_EXTRA_ARGS} \
                     --rcfile "${PYLINT_RCFILE}" --persistent=n --score=n "${PYLINT_ARGS[@]}" \
                     "${SOURCES[@]}"
    local PYLINT_RESULT=$?
    if [ ${PYLINT_RESULT} -ne 0 ] ; then
        stderr_echo "Running pylint failed with return code ${PYLINT_RESULT}!"
        return 1
    fi

    echo "Pylint done."
    echo

    return 0
}

# Run mypy on given python sources.
run_mypy()
{
    if [[ ${MYPY_ENABLED} != 1 ]] ; then
        echo "Mypy is disabled."
        echo
        return 0
    fi

    exit_if_argc_lt $# 3
    local BUILD_DIR="$1"; shift
    local MYPY_CONFIG_FILE="$1"; shift
    local MSYS_WORKAROUND_TEMP=("${!1}"); shift
    local MYPY_ARGS=("${MSYS_WORKAROUND_TEMP[@]}")
    local SOURCES=("$@")

    python -m mypy ${MYPY_EXTRA_ARGS} "${MYPY_ARGS[@]}" --cache-dir="${BUILD_DIR}/.mypy_cache" \
            --config-file "${MYPY_CONFIG_FILE}" "${SOURCES[@]}"
    local MYPY_RESULT=$?
    if [ ${MYPY_RESULT} -ne 0 ] ; then
        stderr_echo "Running mypy failed with return code ${MYPY_RESULT}!"
        return 1
    fi

    echo "Mypy done."
    echo

    return 0
}
