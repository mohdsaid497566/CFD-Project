# Intake CFD Project Documentation

## Overview
This project implements Computational Fluid Dynamics (CFD) simulations for intake systems.

### Main Features
- Feature 1
- Feature 2
- Feature 3

## Getting Started
1. Installation instructions
2. Basic usage
3. Configuration

### Installing Doxygen

#### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install doxygen
sudo apt-get install graphviz  # For generating graphs
```

#### On macOS:
```bash
brew install doxygen
brew install graphviz  # For generating graphs
```

#### On Windows:
1. Download the Doxygen installer from [Doxygen Downloads](https://www.doxygen.nl/download.html)
2. Run the installer and follow the installation wizard
3. Add Doxygen to your system PATH
4. Download and install [Graphviz](https://graphviz.org/download/) for graph generation

#### Verify Installation:
```bash
doxygen --version
```

## Project Structure
- `src/` - Source code files
- `include/` - Header files
- `docs/` - Documentation
- `tests/` - Test files

## Building Documentation
To generate the documentation, run:
```bash
doxygen Doxyfile
```

The generated documentation will be available in the `docs_output/html` directory.
