#!/bin/bash

SCRIPT_DIR=`dirname $0`
source "${SCRIPT_DIR}/common_tools.sh"

# Upload PyPi package.
upload_pypi_package()
{
    exit_if_argc_ne $# 3
    local UPLOAD_BUILD_DIR="${1}"; shift
    local PYPI_DISTR_DIR="${1}"; shift
    local SWITCH_TEST_PYPI="${1}"; shift

    local UPLOAD_PYTHON_REQUIREMENTS=("twine")
    activate_python_virtualenv "${UPLOAD_BUILD_DIR}" UPLOAD_PYTHON_REQUIREMENTS[@]
    if [ $? -ne 0 ] ; then
        return 1
    fi

    local PYPI_REPOSITORY_OPTION=""
    if [[ ${SWITCH_TEST_PYPI} != 0 ]] ; then
        echo "Using test PyPi repository."
        echo
        PYPI_REPOSITORY_OPTION="--repository testpypi"
    fi

    python -m twine upload ${PYPI_REPOSITORY_OPTION} "${PYPI_DISTR_DIR}"/*
    local UPLOAD_RESULT=$?
    if [ ${UPLOAD_RESULT} -ne 0 ] ; then
        stderr_echo "PyPi package upload failed with result ${UPLOAD_RESULT}!"
        return 1
    fi

    return 0
}

# Print help message.
print_help()
{
    cat << EOF
Description:
    Uploads Zserio PyPi package to the public repository.

Usage:
    $0 [-h] [-e] [-t] [-o <dir>]

Arguments:
    -h, --help      Show this help.
    -e, --help-env  Show help for enviroment variables.
    -t, --test-pypi Use test PyPi repository instead of real PyPi repository.
    -o <dir>, --output-directory <dir>
                    Output directory where build and distr are located.

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
    local NUM_OF_ARGS=2
    exit_if_argc_lt $# ${NUM_OF_ARGS}
    local PARAM_OUT_DIR_OUT="$1"; shift
    local SWITCH_TEST_PYPI_OUT="$1"; shift

    eval ${SWITCH_TEST_PYPI_OUT}=0

    local NUM_PARAMS=0
    local PARAM_ARRAY=();
    local ARG="$1"
    while [ -n "${ARG}" ] ; do
        case "${ARG}" in
            "-h" | "--help")
                return 2
                ;;

            "-e" | "--help-env")
                return 3
                ;;

            "-t" | "--test-pypi")
                eval ${SWITCH_TEST_PYPI_OUT}=1
                shift
                ;;

            "-o" | "--output-directory")
                eval ${PARAM_OUT_DIR_OUT}="$2"
                shift 2
                ;;

            "-"*)
                stderr_echo "Invalid switch ${ARG}!"
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

    local PARAM
    for PARAM in "${PARAM_ARRAY[@]}" ; do
        case "${PARAM}" in
            *)
                stderr_echo "Invalid argument ${PARAM}!"
                echo
                return 1
        esac
    done

    return 0
}

main()
{
    # parse command line arguments
    local PYPI_PROJECT_ROOT="${SCRIPT_DIR}/.."
    local PARAM_OUT_DIR="${PYPI_PROJECT_ROOT}"
    local SWITCH_TEST_PYPI
    parse_arguments PARAM_OUT_DIR SWITCH_TEST_PYPI $@
    local PARSE_RESULT=$?
    if [ ${PARSE_RESULT} -eq 2 ] ; then
        print_help
        return 0
    elif [ ${PARSE_RESULT} -eq 3 ] ; then
        print_global_help_env
        return 0
    elif [ ${PARSE_RESULT} -ne 0 ] ; then
        return 1
    fi

    echo "Uploading Zserio PyPi package to the public repository."
    echo

    # set global variables
    set_global_variables
    if [ $? -ne 0 ] ; then
        return 1
    fi

    # upload PyPi package
    local PYPI_BUILD_DIR="${PARAM_OUT_DIR}/build"
    local UPLOAD_BUILD_DIR="${PYPI_BUILD_DIR}/upload"
    local PYPI_DISTR_DIR="${PARAM_OUT_DIR}/distr"
    upload_pypi_package "${UPLOAD_BUILD_DIR}" "${PYPI_DISTR_DIR}" ${SWITCH_TEST_PYPI}
    if [ $? -ne 0 ] ; then
        return 1
    fi

    return 0
}

# call main function
main "$@"
