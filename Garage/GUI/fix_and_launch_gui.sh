#!/bin/bash
# fix_and_launch_gui.sh - A comprehensive script to fix common issues and launch the Intake CFD Optimization Suite

# Print colored output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}       Intake CFD Optimization Suite - Launch Helper             ${NC}"
echo -e "${BLUE}=================================================================${NC}\n"

# Make sure we're in the correct directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || { echo -e "${RED}Error: Failed to change to script directory${NC}"; exit 1; }

echo -e "${GREEN}→ Working directory: ${SCRIPT_DIR}${NC}"

# Check for required packages
echo -e "\n${BLUE}[1/6] Checking for required packages...${NC}"
PACKAGES_TO_INSTALL=()

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to check if a Python package is installed
python_package_exists() {
  python3 -c "import $1" >/dev/null 2>&1
}

# Check for X11 utilities
if ! command_exists xdpyinfo; then
  echo -e "${YELLOW}→ xdpyinfo not found - adding x11-utils to install list${NC}"
  PACKAGES_TO_INSTALL+=("x11-utils")
fi

# Check for Python Tkinter
if ! python_package_exists tkinter; then
  echo -e "${YELLOW}→ tkinter not found - adding python3-tk to install list${NC}"
  PACKAGES_TO_INSTALL+=("python3-tk")
fi

# Check for Mesa GL libraries
if ! command_exists glxinfo; then
  echo -e "${YELLOW}→ glxinfo not found - adding mesa-utils to install list${NC}"
  PACKAGES_TO_INSTALL+=("mesa-utils")
fi

# Install missing packages if any
if [ ${#PACKAGES_TO_INSTALL[@]} -gt 0 ]; then
  echo -e "${YELLOW}→ Installing missing packages: ${PACKAGES_TO_INSTALL[*]}${NC}"
  sudo apt-get update && sudo apt-get install -y "${PACKAGES_TO_INSTALL[@]}"
  if [ $? -ne 0 ]; then
    echo -e "${RED}→ Failed to install some packages. Attempting to continue anyway.${NC}"
  else
    echo -e "${GREEN}→ Package installation completed successfully${NC}"
  fi
else
  echo -e "${GREEN}→ All required packages are already installed${NC}"
fi

# Check Python dependencies
echo -e "\n${BLUE}[2/6] Checking Python dependencies...${NC}"
PYTHON_PACKAGES=("numpy" "matplotlib" "pandas" "openmdao" "tkinter" "PIL")
MISSING_PY_PACKAGES=()

for package in "${PYTHON_PACKAGES[@]}"; do
  echo -n "→ Checking for $package... "
  if python3 -c "import $package" 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
  else
    echo -e "${YELLOW}Missing${NC}"
    MISSING_PY_PACKAGES+=("$package")
  fi
done

# Install missing Python packages if needed
if [ ${#MISSING_PY_PACKAGES[@]} -gt 0 ]; then
  echo -e "${YELLOW}→ Missing Python packages: ${MISSING_PY_PACKAGES[*]}${NC}"
  echo -e "${YELLOW}→ Attempting to install missing Python packages...${NC}"
  
  # Handle tkinter separately as it's a system package
  if [[ " ${MISSING_PY_PACKAGES[*]} " == *" tkinter "* ]]; then
    sudo apt-get install -y python3-tk
    MISSING_PY_PACKAGES=("${MISSING_PY_PACKAGES[@]/tkinter/}")
  fi
  
  # Handle PIL separately as it's named differently in pip
  if [[ " ${MISSING_PY_PACKAGES[*]} " == *" PIL "* ]]; then
    python3 -m pip install pillow
    MISSING_PY_PACKAGES=("${MISSING_PY_PACKAGES[@]/PIL/}")
  fi
  
  # Install remaining packages with pip
  if [ ${#MISSING_PY_PACKAGES[@]} -gt 0 ]; then
    python3 -m pip install "${MISSING_PY_PACKAGES[@]}"
  fi
else
  echo -e "${GREEN}→ All Python dependencies are installed${NC}"
fi

# Detect WSL and configure display
echo -e "\n${BLUE}[3/6] Configuring display for GUI...${NC}"
IS_WSL=false
if grep -q -i microsoft /proc/version || grep -q -i microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
  IS_WSL=true
  echo -e "${YELLOW}→ Windows Subsystem for Linux (WSL) detected${NC}"
else
  echo -e "${GREEN}→ Native Linux detected${NC}"
fi

if [ "$IS_WSL" = true ]; then
  echo -e "→ Configuring display for WSL environment"
  
  # Try multiple display configurations in order
  DISPLAY_CONFIGS=(
    "$(grep -m 1 nameserver /etc/resolv.conf | awk '{print $2}'):0.0"
    "$(hostname).local:0.0"
    "localhost:0.0"
    ":0.0"
    "127.0.0.1:0.0"
  )
  
  DISPLAY_WORKING=false
  for disp in "${DISPLAY_CONFIGS[@]}"; do
    echo -n "→ Trying DISPLAY=$disp... "
    export DISPLAY="$disp"
    export LIBGL_ALWAYS_INDIRECT=1
    
    # Test if X11 connection works
    if xdpyinfo >/dev/null 2>&1; then
      echo -e "${GREEN}Success!${NC}"
      DISPLAY_WORKING=true
      break
    else
      echo -e "${YELLOW}Failed${NC}"
    fi
  done
  
  if [ "$DISPLAY_WORKING" = false ]; then
    echo -e "${RED}→ All display configurations failed. Falling back to Windows launcher...${NC}"
    bash ./run_gui_wsl.sh
    exit
  fi
else
  # For native Linux, use the standard display
  echo -e "→ Using standard display configuration for native Linux"
  export DISPLAY=":0"
fi

# Fix common file permissions
echo -e "\n${BLUE}[4/6] Setting up correct permissions...${NC}"
echo -e "→ Making script files executable..."
chmod +x *.sh *.py 2>/dev/null

# Check if python or python3 command exists
echo -e "\n${BLUE}[5/6] Checking Python installation...${NC}"
if command_exists python3; then
  PYTHON_CMD="python3"
  echo -e "${GREEN}→ Found Python 3: $(python3 --version)${NC}"
elif command_exists python; then
  PYTHON_CMD="python"
  echo -e "${GREEN}→ Found Python: $(python --version)${NC}"
else
  echo -e "${RED}→ No Python installation found! Please install Python.${NC}"
  exit 1
fi

# Create mock executables for demo mode if they don't exist
echo -e "\n${BLUE}[6/6] Setting up environment for application...${NC}"
echo -e "→ Ensuring DEMO_MODE is enabled by setting up mock executables"
export DEMO_MODE=1

# Ensure mock executables are created
if [ ! -f "./gmsh_process" ] || [ ! -f "./cfd_solver" ] || [ ! -f "./process_results" ]; then
  echo -e "→ Creating mock executables for demo mode"
  $PYTHON_CMD -c 'import MDO; MDO.create_mock_executables()'
  
  # Check if the Python command failed
  if [ $? -ne 0 ]; then
    echo -e "${YELLOW}→ Failed to create mock executables through Python, creating manually...${NC}"
    
    # Create gmsh_process manually
    cat > ./gmsh_process << 'EOL'
#!/bin/bash
echo 'Mock gmsh_process running...'
echo "Processing $2 to $4"
echo 'Created mock mesh file'
touch $4
EOL
    chmod +x ./gmsh_process
    
    # Create cfd_solver manually
    cat > ./cfd_solver << 'EOL'
#!/bin/bash
echo 'Mock CFD solver running...'
echo "Processing $2"
echo 'Created mock result files'
mkdir -p cfd_results
echo '0.123' > cfd_results/pressure.dat
EOL
    chmod +x ./cfd_solver
    
    # Create process_results manually
    cat > ./process_results << 'EOL'
#!/bin/bash
echo 'Mock results processor running...'
echo "Processing results from $2 to $4"
echo '0.123' > $4
EOL
    chmod +x ./process_results
    
    echo -e "${GREEN}→ Mock executables created manually${NC}"
  else
    echo -e "${GREEN}→ Mock executables created successfully${NC}"
  fi
else
  echo -e "${GREEN}→ Mock executables already exist${NC}"
fi

# Final launch of the application
echo -e "\n${BLUE}=================================================================${NC}"
echo -e "${GREEN}All setup completed! Launching Intake CFD Optimization Suite...${NC}"
echo -e "${BLUE}=================================================================${NC}\n"

echo -e "If the application fails to launch, try these commands manually:"
echo -e "1. ${YELLOW}export DISPLAY=$(grep -m 1 nameserver /etc/resolv.conf | awk '{print $2}'):0${NC}"
echo -e "2. ${YELLOW}export LIBGL_ALWAYS_INDIRECT=1${NC}"
echo -e "3. ${YELLOW}$PYTHON_CMD MDO.py${NC}\n"

# Launch the application with DEMO_MODE enabled
DEMO_MODE=1 $PYTHON_CMD MDO.py

# Handle exit code
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
  echo -e "\n${RED}Application exited with error code $EXIT_CODE${NC}"
  echo -e "${YELLOW}→ Trying alternative launch method...${NC}\n"
  
  # Try with the WSL GUI helper as a fallback
  bash ./run_gui_wsl.sh
else
  echo -e "\n${GREEN}Application closed normally${NC}"
fi

exit $EXIT_CODE