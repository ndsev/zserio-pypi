#!/bin/bash

SCRIPT_DIR=`dirname $0`
source "${SCRIPT_DIR}/common_tools.sh"

# Build PyPi package.
build_pypi_package()
{
    exit_if_argc_ne $# 3
    local PYPI_PROJECT_ROOT="${1}" ; shift
    local PYPI_BUILD_DIR="${1}"; shift
    local PYPI_DISTR_DIR="${1}"; shift

    local BUILD_PYTHON_REQUIREMENTS=("setuptools" "wheel")
    activate_python_virtualenv "${PYPI_BUILD_DIR}" BUILD_PYTHON_REQUIREMENTS[@]
    if [ $? -ne 0 ] ; then
        return 1
    fi

    pushd "${PYPI_PROJECT_ROOT}" > /dev/null
    # use host path for environment variable (Windows problem)
    posix_to_host_path "${PYPI_BUILD_DIR}" HOST_PYPI_BUILD_DIR
    PYPI_BUILD_DIR="${HOST_PYPI_BUILD_DIR}" python setup.py \
            build --build-base="${PYPI_BUILD_DIR}" \
            sdist --dist-dir="${PYPI_DISTR_DIR}" \
            bdist_wheel --dist-dir="${PYPI_DISTR_DIR}" \
            egg_info --egg-base="${PYPI_BUILD_DIR}"
    local BUILD_RESULT=$?
    popd > /dev/null

    if [ ${BUILD_RESULT} -ne 0 ] ; then
        stderr_echo "PyPi package build failed with result ${BUILD_RESULT}!"
        return 1
    fi

    return 0
}

# Print help message.
print_help()
{
    cat << EOF
Description:
    Builds Zserio wheel package into the distr directory.

Usage:
    $0 [-h] [-e] [-c] [-p] [-o <dir>]

Arguments:
    -h, --help      Show this help.
    -e, --help-env  Show help for enviroment variables.
    -c, --clean     Clean build and distr directories.
    -p, --purge     Purge build and distr directories before build.
    -o <dir>, --output-directory <dir>
                    Output directory where build and distr will be located.

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
    local NUM_OF_ARGS=3
    exit_if_argc_lt $# ${NUM_OF_ARGS}
    local PARAM_OUT_DIR_OUT="$1"; shift
    local SWITCH_CLEAN_OUT="$1"; shift
    local SWITCH_PURGE_OUT="$1"; shift

    eval ${SWITCH_PURGE_OUT}=0

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
    # get the project root, absolute path is necessary for python distutils
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
        print_global_help_env
        return 0
    elif [ ${PARSE_RESULT} -ne 0 ] ; then
        return 1
    fi

    echo "Building of Zserio PyPi package."
    echo

    # set global variables
    set_global_variables
    if [ $? -ne 0 ] ; then
        return 1
    fi

    # clean build and distr directories if requested
    local PYPI_BUILD_DIR="${PARAM_OUT_DIR}/build"
    local PYPI_DISTR_DIR="${PARAM_OUT_DIR}/distr"
    if [[ ${SWITCH_PURGE} == 1 || ${SWITCH_CLEAN} == 1 ]] ; then
        echo "Cleaning build and distr directories."
        echo
        rm -rf "${PYPI_BUILD_DIR}/"
        rm -rf "${PYPI_DISTR_DIR}/"
    fi

    # continue only if cleaning was not requested
    if [[ ${SWITCH_CLEAN} != 1 ]] ; then
        mkdir -p "${PYPI_BUILD_DIR}"
        mkdir -p "${PYPI_DISTR_DIR}"

        # build PyPi package
        build_pypi_package "${PYPI_PROJECT_ROOT}" "${PYPI_BUILD_DIR}" "${PYPI_DISTR_DIR}"
        if [ $? -ne 0 ] ; then
            return 1
        fi
    fi

    return 0
}

# call main function
main "$@"
