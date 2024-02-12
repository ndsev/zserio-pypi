#!/bin/bash

SCRIPT_DIR=`dirname $0`
source "${SCRIPT_DIR}/common_tools.sh"

# Run PyPi tests.
test()
{
    exit_if_argc_ne $# 4
    local PYPI_PROJECT_ROOT="$1"; shift
    local TEST_BUILD_DIR="$1"; shift
    local PYPI_DISTR_DIR="$1"; shift
    local TEST_PACKAGE_EXTENSION="$1"; shift

    local TEST_PYTHON_REQUIREMENTS=("coverage==6.5.0" "pylint==3.0.3" "mypy==0.931")
    activate_python_virtualenv "${TEST_BUILD_DIR}" TEST_PYTHON_REQUIREMENTS[@]
    if [ $? -ne 0 ] ; then
        return 1
    fi
    install_zserio_package "${PYPI_DISTR_DIR}" "${TEST_PACKAGE_EXTENSION}"
    if [ $? -ne 0 ] ; then
        return 1
    fi

    echo
    echo "Running PyPi tests."
    echo

    test_zserio_command
    if [ $? -ne 0 ] ; then
        return 1
    fi

    mkdir -p "${TEST_BUILD_DIR}"
    pushd "${TEST_BUILD_DIR}" > /dev/null

    local SOURCES_DIR="${PYPI_PROJECT_ROOT}/src"
    local TESTS_DIR="${PYPI_PROJECT_ROOT}/test"
    local TEST_COVERAGE_PATTERN_SOURCES="*zserio?compiler.py"
    python -m coverage run --include="${TEST_COVERAGE_PATTERN_SOURCES}" --omit="*test_*" -m unittest discover \
        -s "${TESTS_DIR}" -v
    local PYTHON_RESULT=$?
    if [ ${PYTHON_RESULT} -ne 0 ] ; then
        stderr_echo "Running PyPi tests failed with return code ${PYTHON_RESULT}!"
        popd > /dev/null
        return 1
    fi
    echo

    echo "Running PyPi test coverage report."
    echo

    python -m coverage report -m --fail-under=100
    local COVERAGE_RESULT=$?
    if [ ${COVERAGE_RESULT} -ne 0 ] ; then
        stderr_echo "Running PyPi test coverage report failed with return code ${COVERAGE_RESULT}!"
        popd > /dev/null
        return 1
    fi

    popd > /dev/null
    echo

    echo "Running pylint on PyPi sources."

    local PYLINT_RCFILE="${SOURCES_DIR}/pylintrc.txt"
    local PYLINT_ARGS=()
    run_pylint "${PYLINT_RCFILE}" PYLINT_ARGS[@] "${SOURCES_DIR}"/zserio/*
    if [ $? -ne 0 ] ; then
        return 1
    fi

    echo "Running pylint on PyPi test sources."

    PYLINT_ARGS+=("--disable=missing-docstring")
    PYTHONPATH="${SOURCES_DIR}" run_pylint "${PYLINT_RCFILE}" PYLINT_ARGS[@] "${TESTS_DIR}"/*.py
    if [ $? -ne 0 ] ; then
        return 1
    fi

    echo "Running mypy on PyPi sources."

    local MYPY_CONFIG_FILE="${SOURCES_DIR}/mypy.ini"
    local MYPY_ARGS=()
    run_mypy "${TEST_BUILD_DIR}" "${MYPY_CONFIG_FILE}" MYPY_ARGS[@] "${SOURCES_DIR}"/zserio/*
    if [ $? -ne 0 ] ; then
        return 1
    fi

    deactivate_python_virtualenv "${TEST_BUILD_DIR}"

    return 0
}

# Run zserio command after PyPi package installation.
test_zserio_command()
{
    echo -ne "Checking 'python -m zserio --version' ... "
    local ZSERIO_VERSION # one-liner local will destroy $? from command substitution
    ZSERIO_VERSION=$(python -m zserio --version 2>&1)
    local PYTHON_RESULT=$?
    if [ ${PYTHON_RESULT} -ne 0 ] ; then
        stderr_echo "'python -m zserio --version' failed with return code ${PYTHON_RESULT}!"
        return 1
    fi
    echo "ok (" ${ZSERIO_VERSION} ")"

    echo -ne "Checking 'zserio --version'... "
    ZSERIO_VERSION=$(zserio --version 2>&1)
    local ZSERIO_RESULT=$?
    if [ ${ZSERIO_RESULT} -ne 0 ] ; then
        stderr_echo "'zserio --version' failed with return code ${ZSERIO_RESULT}!"
        return 1
    fi
    echo "ok (" ${ZSERIO_VERSION} ")"
    echo

    return 0
}

# Install zserio package to the actual python virtual envinroment.
install_zserio_package()
{
    exit_if_argc_ne $# 2
    local PYPI_DISTR_DIR="$1"; shift
    local TEST_PACKAGE_EXTENSION="$1"; shift

    local ZSERIO_PYTHON_REQUIREMENTS=("zserio")
    if [ ! -z "${PYTHON_VIRTUALENV}" ] ; then  # forced python virtualenv
        check_python_requirements python ZSERIO_PYTHON_REQUIREMENTS[@]
        if [ $? -ne 0 ] ; then
            return 1
        fi
    else
        check_python_requirements python ZSERIO_PYTHON_REQUIREMENTS[@] 2> /dev/null
        if [ $? -ne 0 ] ; then
            python -m pip install "${PYPI_DISTR_DIR}"/zserio*."${TEST_PACKAGE_EXTENSION}"
            if [ $? -ne 0 ] ; then
                return 1
            fi
        fi
    fi

    return 0
}

# Set and check global variables for tests.
set_test_global_variables()
{
    # prevent __pycache__ and *.pyc being created in sources directory
    export PYTHONDONTWRITEBYTECODE=1

    # Pylint configuration - pylint disabled by default
    PYLINT_ENABLED="${PYLINT_ENABLED:-0}"

    # Pylint extra arguments are empty by default
    PYLINT_EXTRA_ARGS="${PYLINT_EXTRA_ARGS:-""}"

    # Mypy configuration - mypy disabled by default
    MYPY_ENABLED="${MYPY_ENABLED:-0}"

    # Mypy extra arguments are empty by default
    MYPY_EXTRA_ARGS="${MYPY_EXTRA_ARGS:-""}"
}

# Print help on the environment variables used for tests.
print_test_help_env()
{
    cat << EOF
Uses the following environment variables for testing:
    PYLINT_ENABLED     Defines whether to run pylint. Default is 0 (disabled).
    PYLINT_EXTRA_ARGS  Extra arguments to pylint. Default is empty string.
    MYPY_ENABLED       Defines whether to run mypy. Default is 0 (disabled).
    MYPY_EXTRA_ARGS    Extra arguments to mypy. Default is empty string.

EOF
}

# Print help message.
print_help()
{
    cat << EOF
Description:
    Runs PyPi tests on wheel package built in distr directory.

Usage:
    $0 [-h] [-e] [-c] [-p] [-o <dir>]

Arguments:
    -h, --help      Show this help.
    -e, --help-env  Show help for enviroment variables.
    -c, --clean     Clean test build directory.
    -p, --purge     Purge test build directory before tests.
    -o <dir>, --output-directory <dir>
                    Output directory where test build are located.

EOF
}

# Parse all command line arguments.
#
# Return codes:
# -------------
# 0 - Success. Arguments have been successfully parsed.
# 1 - Failure. Some arguments are wrong or missing.
# 2 - Help switch is present. Arguments after help switch have not been checked.
parse_arguments()
{
    exit_if_argc_lt $# 3
    local PARAM_OUT_DIR_OUT="$1"; shift
    local SWITCH_CLEAN_OUT="$1"; shift
    local SWITCH_PURGE_OUT="$1"; shift

    eval ${SWITCH_CLEAN_OUT}=0
    eval ${SWITCH_PURGE_OUT}=0

    local NUM_PARAMS=0
    local PARAM_ARRAY=()
    local ARG="$1"
    while [ $# -ne 0 ] ; do
        case "${ARG}" in
            "-h" | "--help")
                return 2
                ;;

            "-e" | "--help-env")
                return 3
                ;;

            "-c" | "--clean")
                eval ${SWITCH_CLEAN_OUT}=1
                shift
                ;;

            "-p" | "--purge")
                eval ${SWITCH_PURGE_OUT}=1
                shift
                ;;

            "-o" | "--output-directory")
                eval ${PARAM_OUT_DIR_OUT}="$2"
                shift 2
                ;;

            "-"*)
                stderr_echo "Invalid switch '${ARG}'!"
                echo
                return 1
                ;;

            *)
                PARAM_ARRAY[NUM_PARAMS]=${ARG}
                NUM_PARAMS=$((NUM_PARAMS + 1))
                shift
                ;;
        esac
        ARG="$1"
    done

    local NUM_CPP_TARGETS=0
    local PARAM
    for PARAM in "${PARAM_ARRAY[@]}" ; do
        case "${PARAM}" in
            *)
                stderr_echo "Invalid argument '${PARAM}'!"
                echo
                return 1
        esac
    done

    return 0
}

main()
{
    # get the project root, absolute path is necessary for python test coverage report
    local PYPI_PROJECT_ROOT
    convert_to_absolute_path "${SCRIPT_DIR}/.." PYPI_PROJECT_ROOT

    # parse command line arguments
    local PARAM_OUT_DIR="${PYPI_PROJECT_ROOT}"
    local SWITCH_CLEAN
    local SWITCH_PURGE
    parse_arguments PARAM_OUT_DIR SWITCH_CLEAN SWITCH_PURGE $@
    local PARSE_RESULT=$?
    if [ ${PARSE_RESULT} -eq 2 ] ; then
        print_help
        return 0
    elif [ ${PARSE_RESULT} -eq 3 ] ; then
        print_test_help_env
        print_global_help_env
        return 0
    elif [ ${PARSE_RESULT} -ne 0 ] ; then
        return 1
    fi

    echo "Testing of Zserio PyPi package."
    echo

    # set global variables
    set_global_variables
    if [ $? -ne 0 ] ; then
        return 1
    fi
    set_test_global_variables
    if [ $? -ne 0 ] ; then
        return 1
    fi

    # clean test build directory if requested
    local PYPI_BUILD_DIR="${PARAM_OUT_DIR}/build"
    local PYPI_DISTR_DIR="${PARAM_OUT_DIR}/distr"
    local TEST_BUILD_DIR="${PYPI_BUILD_DIR}/test"
    if [[ ${SWITCH_PURGE} == 1 || ${SWITCH_CLEAN} == 1 ]] ; then
        echo "Cleaning test build directory."
        echo
        rm -rf "${TEST_BUILD_DIR}/"
    fi

    # continue only if cleaning was not requested
    if [[ ${SWITCH_CLEAN} != 1 ]] ; then
        mkdir -p "${TEST_BUILD_DIR}"

        # run test using wheel package
        test "${PYPI_PROJECT_ROOT}" "${TEST_BUILD_DIR}/wheel" "${PYPI_DISTR_DIR}" "whl"
        if [ $? -ne 0 ] ; then
            return 1
        fi

        # run test using sdist package
        test "${PYPI_PROJECT_ROOT}" "${TEST_BUILD_DIR}/sdist" "${PYPI_DISTR_DIR}" "tar.gz"
        if [ $? -ne 0 ] ; then
            return 1
        fi
    fi

    return 0
}

main "$@"
