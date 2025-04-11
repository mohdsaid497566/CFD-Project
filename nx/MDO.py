## First, function that takes the inputs then exports the model into STEP,
## Second, function that takes the exported STEP file and processes it with GMSH to create a mesh.
## Third, function that passes the mesh to a CFD solver.
## Fourth , function that takes the CFD solver results and processes them for visualization.
## Fifth, function that visualizes the results in a suitable format.

import sys
import os
import time
import subprocess
from Expressions import format_exp, write_exp_file

# This module handles the creation and writing of expressions for NX.
# It formats expressions and writes them to an .exp file.

def exp(L4, L5, alpha1, alpha2, alpha3):
    expressions_list = list ()
    L4_expression  = format_exp('L4', 'number', L4, unit='Meter')
    L5_expression  = format_exp('L5', 'number', L5, unit='Meter')
    alpha1_expression = format_exp('alpha1', 'number', alpha1, unit='Degrees')
    alpha2_expression = format_exp('alpha2', 'number', alpha2, unit='Degrees')
    alpha3_expression = format_exp('alpha3', 'number', alpha3, unit='Degrees')
    expressions_list.append(L4_expression)
    expressions_list.append(L5_expression)
    expressions_list.append(alpha1_expression)
    expressions_list.append(alpha2_expression)
    expressions_list.append(alpha3_expression)
    # Write the expressions to an .exp file
    write_exp_file(expressions_list, "expression")  # Save the expressions to exp.exp
    # Return the list of expressions for further use if needed
    
    
## the following should be implemented in the terminal using python somehow
## first run go to the following directory C:\Program Files\Siemens\NX2406\UGII and run cmd.exe /c nxcommand.bat
## after that it should import the expressions files and export the CAD with a new name
## run_journal C:\Users\Mohammed\Desktop\nx\nx_express2.py -args C:\Users\Mohammed\Desktop\nx\INSTAKE3D.prt
## run_journal C:\Users\Mohammed\Desktop\nx\nx_export.py -args C:\Users\Mohammed\Desktop\nx\INSTAKE3D.prt
    
import subprocess
import os

def run_nx_from_bash():
    """
    Calls the Bash script to run Siemens NX commands.
    """        
    # Run the Bash script with the required arguments
    print("Running NX commands via Bash script...")
    subprocess.run(["bash", "run_nx_commmands.sh"],
        check=True,
        capture_output=True,
        text=True
    )
    print("NX operations completed successfully via Bash script.")
# Example usage

run_nx_from_bash