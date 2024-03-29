#!/usr/bin/env bash
# shellcheck disable=SC2155
TERM="xterm-256color"

PROGRAM_NAME="dock_title"
VERSION_FILE="_version_.txt"
PROGRAM_TITLE="DockTitle"

##################################################
# DEFAULTS
##################################################
DRY_RUN="0"
BUILD_EXE="1"
REINSTALL="0"
DEBUG="0"

##################################################
# Commands
##################################################
export READLINK="$(command -v greadlink || command -v readlink)"
export REALPATH="$(command -v grealpath || command -v realpath)"
export BASENAME="$(command -v gbasename || command -v basename)"
export DIRNAME="$(command -v gdirname || command -v dirname)"
export GETOPTS="$(command -v ggetopts || command -v getopts)"
export GETOPT="$(command -v ggetopt || command -v getopt)"
export PRINTF="$(command -v gprintf || command -v printf)"
export CHMOD="$(command -v gchmod || command -v chmod)"
export TOUCH="$(command -v gtouch || command -v touch)"
export UNAME="$(command -v guname || command -v uname)"
export XARGS="$(command -v gxargs || command -v xargs)"
export DATE="$(command -v gdate || command -v date)"
export GREP="$(command -v ggrep || command -v grep)"
export READ="$(command -v gread || command -v read)"
export ECHO="$(command -v gecho || command -v echo)"
export EVAL="$(command -v eval)"
export TYPE="$(command -v type)"
export TPUT="$(command -v tput)"
export TPUT+=" -T${TERM}"
export CURL="$(command -v gcurl || command -v curl)"
export AWK="$(command -v gawk || command -v awk)"
export SED="$(command -v gsed || command -v sed)"
export CUT="$(command -v gcut || command -v cut)"
export TEE="$(command -v gtee || command -v tee)"
export CAT="$(command -v gcat || command -v cat)"
export CP="$(command -v gcp || command -v cp)"
export CD="$(command -v gcd || command -v cd)"
export MV="$(command -v gmv || command -v mv)"
export RM="$(command -v grm || command -v rm)"
export LN="$(command -v gln || command -v ln)"
PYTHON3="$(command -v python3)"

PROGRAM_VERSION="$(${CAT} "${VERSION_FILE}" | ${XARGS})"

##################################################
# Colors
##################################################
RED=$(${TPUT} setaf 1)
GREEN=$(${TPUT} setaf 2)
YELLOW=$(${TPUT} setaf 3)
BLUE=$(${TPUT} setaf 4)
MAGENTA=$(${TPUT} setaf 5)
CYAN=$(${TPUT} setaf 6)
WHITE="$(${TPUT} setaf 7)"
GREY="$(${TPUT} setaf 8)"
ORANGE=$(${TPUT} setaf 9)
BRIGHTGREEN=$(${TPUT} setaf 10)
BRIGHTYELLOW=$(${TPUT} setaf 11)
POWDERBLUE=$(${TPUT} setaf 153)
BOLD=$(${TPUT} bold)
DEBOLD="$(${TPUT} rmso)"
UL=$(${TPUT} smul)
DEUL=$(${TPUT} rmul)
NC="$(${TPUT} sgr0)"

##################################################
# Local variables
##################################################
CALL_DIR="${PWD}"
MYNAME="${0}"
INSTALL_SCRIPT="$(${BASENAME} "${MYNAME}")"
MYPATH="$(${REALPATH} ${MYNAME})"
BASE_DIR="$(${DIRNAME} ${MYPATH})"
VENV_HOME="${BASE_DIR}/venv"
VENV_SCRIPT="${VENV_HOME}/bin/activate"
DEPS_FILE="requirements.txt"
DEPS_PATH="${BASE_DIR}/${DEPS_FILE}"
RESOURCES_DIR_NAME="resources"
RESOURCES_DIR="${BASE_DIR}/${RESOURCES_DIR_NAME}"
ICON_NAME="${PROGRAM_NAME}.icns"
ICON="${RESOURCES_DIR}/${ICON_NAME}"
WRAPPER_NAME="${PROGRAM_NAME}.sh"
SYMLINK_NAME="${PROGRAM_NAME}"
SCRIPT_NAME="${PROGRAM_NAME}.py"
WRAPPER="${BASE_DIR}/${WRAPPER_NAME}"
SCRIPT="${BASE_DIR}/${SCRIPT_NAME}"
SYMLINK="${BASE_DIR}/${SYMLINK_NAME}"
COMPILED_NAME="${PROGRAM_NAME}"
COMPILED_DIR_NAME="dist"
COMPILED_DIR="${BASE_DIR}/${COMPILED_DIR_NAME}"
COMPILED_RESULT="${COMPILED_DIR}/${COMPILED_NAME}"
COMPILED="${BASE_DIR}/${COMPILED_NAME}"

##################################################
# Utility functions
##################################################
function log() {
  # Log to stderr in case we need to use stdout output for something
  ${PRINTF} "%s" "${POWDERBLUE}" > /dev/stderr
  ${PRINTF} "${*}" > /dev/stderr
  ${PRINTF} "%s\n" "${NC}"
}

function logTitle() {
  # Log to stderr in case we need to use stdout output for something
  ${PRINTF} "%s" "${BOLD}${POWDERBLUE}" > /dev/stderr
  ${PRINTF} "${*}" > /dev/stderr
  ${PRINTF} "%s\n" "${NC}"
}

function logSuccess() {
  # Log to stderr in case we need to use stdout output for something
  ${PRINTF} "%s" "${GREEN}" > /dev/stderr
  ${PRINTF} "[SUCCESS] ${*}" > /dev/stderr
  ${PRINTF} "%s\n" "${NC}"
}

function logErr() {
  # Log to stderr in case we need to use stdout output for something
  ${PRINTF} "%s" "${RED}" > /dev/stderr
  ${PRINTF} "[ERROR] ${*}" > /dev/stderr
  ${PRINTF} "%s\n" "${NC}" > /dev/stderr
}

function logWarn() {
  # Log to stderr in case we need to use stdout output for something
  ${PRINTF} "%s" "${YELLOW}" > /dev/stderr
  ${PRINTF} "[WARNING] ${*}" > /dev/stderr
  ${PRINTF} "%s\n" "${NC}" > /dev/stderr
}

function logDbg() {
  # Log to stderr in case we need to use stdout output for something
  if [[ -n "${DEBUG}" && "${DEBUG}" == "1" ]]; then
    ${PRINTF} "%s" "${MAGENTA}" > /dev/stderr
    ${PRINTF} "[DEBUG] ${*}" > /dev/stderr
    ${PRINTF} "%s\n" "${NC}" > /dev/stderr
  fi
}

function titleCase() {
  set ${*,,}
  ${ECHO} ${*^}
}

function check_package() {
  # Check if a single package is installed
  local PKG
  local CMD1
  local CMD2
  local PKG_STATUS=0
  PKG="${1}"
  if [[ -z "${PKG}" ]]; then
    logErr "check_package: must provide name of a Python package to check"
    exit 1
  fi
  CMD1="python3 -c \"import ${PKG}\" 2>/dev/null"
  CMD2="python3 -c \"import subprocess ; available = not(subprocess.run(['pip', 'show', '${PKG}'], capture_output=True, check=True))\" 2>/dev/null"
  logDbg "check_package: checking for package ${PKG} with command: ${CMD1}"
  python3 -c "import ${PKG}" 2>/dev/null
  PKG_STATUS="${?}"
  logDbg "check_package: ${PKG} import returned error code ${PKG_STATUS}"
  if [[ "${PKG_STATUS}" -ne 0 ]]; then
    logDbg "check_package: checking if ${PKG} is non-module with command: ${CMD2}"
    python -c "import subprocess ; available = not(subprocess.run(['pip', 'show', '${PKG}'], capture_output=True, check=True))" 2>/dev/null
    PKG_STATUS="${?}"
    logDbg "check_package: ${PKG} pip check returned error code ${PKG_STATUS}"
    if [[ "${PKG_STATUS}" -ne 0 ]]; then
      logDbg "check_package: ${PKG} is not installed"
      return 1
    fi
  fi
  logDbg "check_package: ${PKG} found"
  return 0
}

function check_packages() {
  # Check for required Python packages
  local REQUIREMENTS_FILE
  local -a PACKAGES=()
  local CMD1
  local PKG_STATUS=0
  local IDX=0

  REQUIREMENTS_FILE="${1}"
  if [[ -z "${REQUIREMENTS_FILE}" ]]; then
    logErr "check_packages: must provide a file containing list of packages"
    exit 1
  fi
  if [[ ! -s "${REQUIREMENTS_FILE}" ]]; then
    logErr "check_packages: cannot find packages file '${REQUIREMENTS_FILE}'"
    exit 1
  fi
  mapfile -t TMP_PACKAGES < "${REQUIREMENTS_FILE}"
  for line in "${TMP_PACKAGES[@]}"; do
    # Easiest way to trim leading or trailing whitespace is to pipe through xargs
    TRIMMED="$(${ECHO} "${line}" | ${XARGS})"
    if [[ "${TRIMMED}" == "" || "${TRIMMED}" =~ ^# ]]; then
      # Blank line or comment, ignore it
      continue
    else
      # Not a blank line or a comment, process it
      PACKAGES+=( "${TRIMMED}" )
    fi
  done

  for pkg in "${PACKAGES[@]}"; do
    IDX="$(( IDX + 1))"
    logDbg "check_packages: checking for package ${IDX} (${pkg}) ..."
    check_package "${pkg}"
    PKG_STATUS="${?}"
    logDbg "check_packages: package check command for package ${IDX} (${pkg}) returned status ${PKG_STATUS}"
    if [[ "${PKG_STATUS}" -ne 0 ]]; then
      logWarn "  * Package #${IDX} '${pkg}' not installed"
      return 1
    fi
  done
  return 0
}

function install_packages() {
  # Packages need to be installed
  # WARNING: Assumes virtual environment has been activated!
  local REQUIREMENTS_FILE
  local REQUIREMENTS_PATH
  local CMD1
  local CMD2
  local PIP
  local PIP_STATUS

  REQUIREMENTS_FILE="${DEPS_FILE}"
  REQUIREMENTS_PATH="${BASE_DIR}/${DEPS_FILE}"
  if [[ -n "${1}" ]]; then
    REQUIREMENTS_FILE="${1}"
    REQUIREMENTS_PATH="$(${REALPATH} "${REQUIREMENTS_FILE}")"
  fi
  cd "${BASE_DIR}" || { logErr "install_packages: could not change to install directory '${BASE_DIR}'" ; exit 1 ; }
  if [[ -z "${REQUIREMENTS_FILE}" ]]; then
    logErr "install_packages: no packages file found"
    exit 1
  fi
  if [[ ! -s "${REQUIREMENTS_PATH}" ]]; then
    logErr "install_packages: could not find packages in file '${REQUIREMENTS_PATH}'"
    exit 1
  fi

  # PIP="${PYTHON3_HOME}/bin/pip3"
  PIP="$(command -v pip)"
  if [[ ! -x "${PIP}" ]]; then
    logErr "ERROR: Python virtual environment does not have the pip command: '${PIP}'"
    exit 1
  fi
  CMD1="${PIP} install --upgrade pip 2>/dev/null"
  logDbg "install_packages: updating pip with command ${CMD1}"
  ${PIP} install --upgrade pip 2>/dev/null
  PIP_STATUS="${?}"
  logDbg "install_packages: pip update command returned status ${PIP_STATUS}"
  if [[ "${PIP_STATUS}" -ne 0 ]]; then
    logErr "ERROR: Could not upgrade pip before installing required packages from: '${DEPS_PATH}'"
    exit 1
  fi
  CMD2="${PIP} install -r \"${REQUIREMENTS_PATH}\""
  logDbg "install_packages: installing with command ${CMD2}"
  ${PIP} install -r "${REQUIREMENTS_PATH}"
  PIP_STATUS="${?}"
  logDbg "install_packages: package install command returned status ${PIP_STATUS}"
  if [[ "${PIP_STATUS}" -ne 0 ]]; then
    logErr "ERROR: Could not install required packages from: '${DEPS_PATH}'"
    exit 1
  fi
  return 0
}

##################################################
# Usage
##################################################
PROGRAM_NAME_TITLE="$(titleCase "${PROGRAM_NAME}")"
PROGRAM_NAME_UPPER="${PROGRAM_NAME^^}"
PROGRAM_NAME_LOWER="${PROGRAM_NAME,,}"

${READ} -r -d '' DOCS <<DOCS
${BOLD}${UL}${PROGRAM_NAME_UPPER} installer${NC}

${YELLOW}This script will install ${BOLD}${PROGRAM_NAME} v${PROGRAM_VERSION}${NC}

${BLUE}${UL}USAGE:${NC}

${BOLD}${INSTALL_SCRIPT}${NC} ${MAGENTA}[options]${NC}

${BLUE}${UL}OPTIONS:${NC}
    ${BOLD}${BRIGHTYELLOW}-p${NC}   ${BLUE}[optional]${NC}  ${YELLOW}Path to Python executable to use. Defaults to first 'python' command in PATH${NC}
    ${BOLD}${BRIGHTYELLOW}-r${NC}   ${BLUE}[optional]${NC}  ${YELLOW}Reinstall (delete and re-create Python virtual environment, binary, wrapper script, etc.)${NC}
    ${BOLD}${BRIGHTYELLOW}-x${NC}   ${BLUE}[optional]${NC}  ${YELLOW}Do not build single executable file (will try creating a symlink to wrapper script instead)${NC}
    ${BOLD}${BRIGHTYELLOW}-D${NC}   ${BLUE}[optional]${NC}  ${YELLOW}Dry run: show where files would be installed, wrapper script contents, etc.${NC}
    ${BOLD}${BRIGHTYELLOW}-d${NC}   ${BLUE}[optional]${NC}  ${YELLOW}Show debugging and intermediate info while running this script${NC}
    ${BOLD}${BRIGHTYELLOW}-h${NC}   ${BLUE}[optional]${NC}  ${YELLOW}Help (show this message)${NC}

${BLUE}${UL}EXAMPLES:${NC}
    ${GREY}# Install ${PROGRAM_NAME}${NC}
    ${POWDERBLUE}${INSTALL_SCRIPT}${NC}

    ${GREY}# Reinstall (delete any existing Python virtual environment and entry points before install)${NC}
    ${POWDERBLUE}${INSTALL_SCRIPT} -r${NC}

    ${GREY}# Install using a specific Python interpreter${NC}
    ${POWDERBLUE}${INSTALL_SCRIPT} -p /usr/local/bin/python/3.11.4/bin/python${NC}

    ${GREY}# Do not build a single executable binary file; use symlink to wrapper script instead${NC}
    ${POWDERBLUE}${INSTALL_SCRIPT} -x${NC}

    ${GREY}# Install ${PROGRAM_NAME} with debugging output${NC}
    ${POWDERBLUE}${INSTALL_SCRIPT} -d${NC}

    ${GREY}# Do a dry-run installation${NC}
    ${POWDERBLUE}${INSTALL_SCRIPT} -D${NC}

DOCS
#

function usage() {
  ${PRINTF} "%s\n\n" "${DOCS}"
}

##################################################
# PARSE INPUT
##################################################
OPT_PYTHON=""
while ${GETOPTS} "p:rxDdh" OPTION
do
    case $OPTION in
        p) OPT_PYTHON="${OPTARG}" ;;
        r) REINSTALL="1" ;;
        x) BUILD_EXE="0" ;;
        D) DRY_RUN="1" ;;
        d) DEBUG="1" ;;
        h) usage ; exit 0 ;;
        ?) ${PRINTF} "%sInvalid option: '-%s'%s\n\n" "${BOLD}${RED}" "${OPTION}" "${NC}" ; usage ; exit 1 ;;
    esac
done

##################################################
# VALIDATE INPUT
##################################################

if [[ -n "${OPT_PYTHON}" ]]; then
  if [[ ! -x "${OPT_PYTHON}" ]]; then
    logErr "ERROR: Could not find specified Python interpreter: '${OPT_PYTHON}'"
    exit 1
  fi
  PYTHON3="${OPT_PYTHON}"
fi

logTitle "Installing ${PROGRAM_TITLE}"

log "Checking for 'python' command ..."

if [[ -n "${PYTHON3}" ]]; then
  if [[ -x "${PYTHON3}" ]]; then
    logDbg "Found valid python command: '${PYTHON3}'"
  else
    logErr "Could not find valid Python command at: '${PYTHON3}'"
    exit 1
  fi
else
  logErr "Valid Python command not found"
  exit 1
fi

if [[ "${PYTHON3}" =~ asdf ]]; then
  # Account for asdf shims
  log "Python appears to be installed using asdf, checking for install location ..."
  ASDF="$(command -v asdf)"
  if [[ -z "${ASDF}" ]]; then
    logErr "ERROR: Python appears to be installed using asdf, but 'asdf' command could not be found."
    exit 1
  fi
  PYTHON_BIN="$(${ASDF} which python3)"
  if [[ -z "${PYTHON_BIN}" ]]; then
    logErr "ERROR: Python appears to be installed using asdf, but 'asdf which python3' command could not be found."
    exit 1
  else
    logDbg "Found asdf python install: '${PYTHON_BIN}'"
  fi
  PYTHON3="$(${REALPATH} "${PYTHON_BIN}")"
  logDbg "Real location of asdf python install: '${PYTHON3}'\n"
  if [[ -z "${PYTHON_HOME}" ]]; then
    logDbg "PYTHON_HOME not set, guessing based on Python binary location ..."
    PYTHON_HOME="$(${DIRNAME} "$(${DIRNAME} "${PYTHON3}")")"
    logDbg "PYTHON_HOME appears to be: '${PYTHON_HOME}'"
  else
    logDbg "PYTHON_HOME=\"${PYTHON_HOME}\""
  fi
fi

if [[ -z "${PYTHON3}" ]]; then
  logErr "ERROR: Could not find 'python3' command in path. Please add it to the path."
  exit 1
fi

PYTHON3_HOME=""

if [[ -n "${PYTHON_HOME}" ]]; then
  PYTHON3_HOME="${PYTHON_HOME}"
else
  PYTHON3_HOME="$(dirname "$(dirname "${PYTHON3}")")"
fi

if [[ ! -d "${PYTHON3_HOME}" || ! -x "${PYTHON3_HOME}/bin/python3" ]]; then
  logErr "ERROR: Could not find 'python3' command in PYTHON_HOME=\"${PYTHON3_HOME}\". Please add it to the path."
  exit 1
else
  logDbg "Python command found in PYTHON_HOME=\"${PYTHON3_HOME}\""
fi

PYTHON_HOME="${PYTHON3_HOME}"

if [[ "${REINSTALL}" -eq 1 ]]; then
  log "REINSTALL: removing any existing virtual environment and wrapper script(s) ..."

  logDbg "Checking for virtual environment at '${VENV_HOME}' ..."
  if [[ -d "${VENV_HOME}" ]]; then
    CMD1="${RM} -rf \"${VENV_HOME:-safety}\""
    if [[ "${DRY_RUN}" -eq 1 ]]; then
      log "DRY RUN: Not actually removing virtual environment at '${VENV_HOME}'"
      logDbg "Command to remove virtual environment would be: ${CMD1}"
    else
      logDbg "Virtual environment exists, removing with command: ${CMD1}"
      ${RM} -rf "${VENV_HOME:-safety}"
      logDbg "Virtual environment removed"
    fi
  else
    logDbg "Virtual environment does not exist, so it will not be removed"
  fi

  logDbg "Checking for symlink to wrapper script ${SYMLINK_NAME} => ${WRAPPER_NAME} ..."
  if [[ -L "${SYMLINK_NAME}" ]]; then
    CMD1="${RM} -f \"${SYMLINK_NAME:-safety}\""
    if [[ "${DRY_RUN}" -eq 1 ]]; then
      log "DRY RUN: Not actually removing symlink to wrapper script at '${SYMLINK}'"
      logDbg "Command to remove symlink to wrapper script would be: ${CMD1}"
    else
      logDbg "Symlink to wrapper script exists, removing with command: ${CMD1}"
      ${RM} -f "${SYMLINK_NAME:-safety}"
      logDbg "Symlink to wrapper script removed"
    fi
  else
    logDbg "Symlink to wrapper script does not exist, so it will not be removed"
  fi

  logDbg "Checking for compiled single executable file ${COMPILED_NAME} ..."
  if [[ -x "${COMPILED}" ]]; then
    CMD1="${RM} -f \"${COMPILED:-safety}\""
    if [[ "${DRY_RUN}" -eq 1 ]]; then
      log "DRY RUN: Not actually removing compiled executable at '${COMPILED}'"
      logDbg "Command to remove compiled executable would be: ${CMD1}"
    else
      logDbg "Compiled single executable exists, removing with command: ${CMD1}"
      ${RM} -f "${COMPILED:-safety}"
      logDbg "Compiled single executable removed"
    fi
  else
    logDbg "Compiled binary executable does not exist, so it will not be removed"
  fi

  logDbg "Checking for existing build directory ${COMPILED_DIR} ..."
  if [[ -d "${COMPILED_DIR}" ]]; then
    CMD1="${RM} -rf \"${COMPILED_DIR:-safety}\""
    if [[ "${DRY_RUN}" -eq 1 ]]; then
      log "DRY RUN: Not actually removing existing build direcotry at '${COMPILED_DIR}'"
      logDbg "Command to remove existing build directory would be: ${CMD1}"
    else
      logDbg "Build directory exists, removing with command: ${CMD1}"
      ${RM} -rf "${COMPILED_DIR:-safety}"
      logDbg "Existing build directory removed"
    fi
  else
    logDbg "Build directory does not exist, so it will not be removed"
  fi

  logDbg "Checking for wrapper script '${WRAPPER}' ..."
  if [[ -e "${WRAPPER}" ]]; then
    CMD1="${RM} -f \"${WRAPPER:-safety}\""
    if [[ "${DRY_RUN}" -eq 1 ]]; then
      log "DRY RUN: Not actually removing wrapper script at '${WRAPPER}'"
      logDbg "Command to remove wrapper script would be: ${CMD1}"
    else
      logDbg "Wrapper script exists, removing with command: ${CMD1}"
      ${RM} -f "${WRAPPER:-safety}"
      logDbg "Wrapper script removed"
    fi
  else
    logDbg "Wrapper script does not exist, so it will not be removed"
  fi
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    log "DRY RUN: skipped removal of existing virtual environment and wrapper script(s)"
  else
    log "REINSTALL: existing virtual environment and wrapper script(s) have been removed"
  fi
fi



log "Checking existence of Python virtual environment ..."
if [[ -d "${BASE_DIR}" && ! -e "${VENV_SCRIPT}" && -e "${DEPS_PATH}" ]]; then
  cd "${BASE_DIR}"
  log "Python virtual environment not found, creating ..."
  CMD1="${PYTHON3} -m venv venv"
  logDbg "Installing Python virtual environment with command: ${CMD1}"
  if [[ "${DRY_RUN}" -ne 1 ]]; then
    ${PYTHON3} -m venv venv
    STATUS="${?}"
    if [[ "${STATUS}" -ne 0 ]]; then
      logErr "ERROR: Setting up the Python virtual environment failed with error code ${STATUS}"
      exit ${STATUS}
    else
      logDbg "Python virtual environment created via command: ${CMD1}"
    fi
  else
    log "DRY RUN: Not creating virtual environment"
  fi
else
  log "Python virtual environment already exists"
fi

if [[ ! -e "${VENV_SCRIPT}" ]]; then
  logErr "ERROR: Could not find or create Python virtual environment at: '${VENV_HOME}'"
  exit 1
else
  log "Python virtual environment created successfully at '${VENV_HOME}'"
fi

logDbg "Now changing directory to \"${BASE_DIR}\""

cd "${BASE_DIR}" || { logErr "ERROR: Could not go to base directory '${BASE_DIR}'" ; exit 1 ; }

if [[ "${DRY_RUN}" -ne 1 ]]; then
  log "Activating Python virtual environment ..."
  CMD1="source \"${VENV_SCRIPT}\""
  logDbg "Python virtual environment activating via command: ${CMD1}"
  source "${VENV_SCRIPT}"
  log "Python virtual environment activated successfully"

  log "Checking existence of required Python packages ..."
  check_packages "${DEPS_PATH}"
  STATUS="${?}"
  if [[ "${STATUS}" -ne 0 ]]; then
    # Packages need to be installed
    log "Required packages not installed, installing them ..."
    install_packages "${DEPS_PATH}"
    STATUS="${?}"
    if [[ "${STATUS}" -ne 0 ]]; then
      logErr "ERROR: Python package installation failed"
      exit 1
    else
      log "Required Python packages installed successfully into virtual environment"
    fi
  else
    log "Packages are already installed, no need to reinstall"
  fi

  logDbg "Re-checking existence of required Python packages ..."
  check_packages "${DEPS_PATH}"
  STATUS="${?}"
  if [[ "${STATUS}" -ne 0 ]]; then
    logErr "ERROR: Python package installation succeeded, but packages still cannot be imported."
    exit 1
  else
    logDbg "Required Python packages exist"
  fi

  log "\nPython environment and packages installed successfully"
else
  log "DRY RUN: Not checking existence of required Python packages"
fi

# Prepare wrapper header data
DEPLOY_TIME="$(${DATE} -Isecond)"
DEPLOY_USER="$(${ECHO} "${USER}")"

if [[ "${DRY_RUN}" -ne 1 ]]; then
  log "\nCreating wrapper script at '${WRAPPER}' ..."
fi

${READ} -r -d '' WRAPPER_CONTENTS <<EOF
#!/usr/bin/env bash

# ${PROGRAM_NAME} wrapper
# Created as: "${WRAPPER}"
# Creation time: ${DEPLOY_TIME}
# Created by user: ${DEPLOY_USER}

TERM="${TERM}"
TPUT="${TPUT}"
PRINTF="${PRINTF}"
RED="\$(\${TPUT} setaf 1)"
NC="\$(\${TPUT} sgr0)"
PYTHON3="${PYTHON3}"

VENV_SCRIPT="${VENV_SCRIPT}"

if [[ ! -x "\${PYTHON3}" ]]; then
  \${PRINTF} "%sERROR: Could not find Python executable at '%s'%s\n" "\${RED}" "\${PYTHON3}" "\${NC}"
  exit 1
fi

if [[ ! -e "\${VENV_SCRIPT}" ]]; then
  \${PRINTF} "%sERROR: Could not find Python virtual environment at '%s', please run install script%s\n" "\${RED}" "\${VENV_SCRIPT}" "\${NC}"
  exit 1
fi

source "\${VENV_SCRIPT}"

python3 "${SCRIPT}" "\${@}"

EOF

if [[ "${DRY_RUN}" -eq 1 ]]; then
  log "DRY RUN: Wrapper file will be: \"${WRAPPER}\""
  logDbg "DRY RUN: Wrapper contents:\n${WRAPPER_CONTENTS}"
  if [[ "${BUILD_EXE}" -ne 1 ]]; then
    log "DRY RUN: Symlink to wrapper script will be: \"${SYMLINK}\""
  else
    log "DRY RUN: Compiled single executable will be: \"${COMPILED}\""
  fi
  log "DRY RUN: finished"
else
  ${PRINTF} "%s\n" "${WRAPPER_CONTENTS}" > "${WRAPPER}"
  ${CHMOD} +x "${SCRIPT}"
  ${CHMOD} +x "${WRAPPER}"
  log "Wrapper script created at '${WRAPPER}'"

  if [[ "${BUILD_EXE}" -ne 1 ]]; then
    log "\nCreating symlink to wrapper script at '${SYMLINK}' ..."
    if [[ -e "${SYMLINK}" ]]; then
      log "Removing existing file '${SYMLINK}' ..."
      ${RM} -f "${SYMLINK}"
      if [[ -e "${SYMLINK}" ]]; then
        logErr "Could not remove existing file '${SYMLINK}'"
        exit 1
      else
        log "Existing file removed: '${SYMLINK}'"
      fi
    fi
    ${LN} -sf "${WRAPPER_NAME}" "${SYMLINK_NAME}"
    if [[ -e "${SYMLINK}" && -L "${SYMLINK}" ]]; then
      log "Symlink to wrapper script created at '${SYMLINK}'"
    else
      logErr "Symlink to wrapper script was not created successfully at '${SYMLINK}'"
      exit 1
    fi
  else
    SYSTEM="Linux"
    if [[ -n "${UNAME}" ]]; then
      SYSTEM="$(${UNAME})"
    fi
    SYSTEM="${SYSTEM,,}"
    if [[ -n "${ICON}" && -s "${ICON}" && "${SYSTEM}" == "darwin" ]]; then
      # Build using an icon if we're on macOS and there is an icon available
      log "\nBuilding executable (with icon) for destination '${COMPILED}' ..."
      pyinstaller -i "${ICON}" -F "${SCRIPT}"
      STATUS="${?}"
      if [[ "${STATUS}" -ne 0 ]]; then
        logErr "Building executable (with icon) threw error ${STATUS}"
        exit ${STATUS}
      fi
    else
      # Don't build using an icon if we're not on macOS or there is no icon available
      log "\nBuilding executable for destination '${COMPILED}' ..."
      pyinstaller -F "${SCRIPT}"
      STATUS="${?}"
      if [[ "${STATUS}" -ne 0 ]]; then
        logErr "Building executable file threw error ${STATUS}"
        exit ${STATUS}
      fi
    fi
    if [[ -x "${COMPILED_RESULT}" ]]; then
      log "Executable built successfully, copying to '${COMPILED}'"
      ${CP} -af "${COMPILED_RESULT}" "${COMPILED}"
      if [[ -x "${COMPILED}" ]]; then
        log "Executable file created at '${COMPILED}'"
      else
        logErr "Executable file built successfully, but failure occurred while copying to final destination '${COMPILED}'"
        exit 1
      fi
    else
      logErr "Building executable apparently succeeded, but the result was not found: '${COMPILED_RESULT}'"
      exit 1
    fi
  fi

  log ""  # Blank line
  logSuccess "${PROGRAM_TITLE} installed in '${BASE_DIR}'"
  logSuccess "${PROGRAM_TITLE} wrapper script created at: '${WRAPPER}'"
  if [[ "${BUILD_EXE}" -ne 1 ]]; then
    logSuccess "${PROGRAM_TITLE} symlink to wrapper script created at: '${SYMLINK}'"
    logSuccess "Run ${PROGRAM_TITLE} with command '${SYMLINK}' or '${WRAPPER}'"
    logSuccess "Or add current directory to PATH to run from anywhere: '${BASE_DIR}'"
    logSuccess "For usage or help: '${SYMLINK_NAME} -h'\n"
  else
    logSuccess "${PROGRAM_TITLE} executable built at: '${COMPILED}'"
    logSuccess "Run ${PROGRAM_TITLE} with command '${COMPILED}' or '${WRAPPER}'"
    logSuccess "Or add current directory to PATH to run from anywhere: '${BASE_DIR}'"
    logSuccess "For usage or help: '${COMPILED_NAME} -h'\n"
  fi
fi
