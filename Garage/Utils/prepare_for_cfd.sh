#!/bin/bash
set -e  # Exit on error

# Default input mesh file and settings
INPUT_MESH="${1:-INTAKE3D_mesh.msh}"
OUTPUT_DIR="${2:-../openfoam_case}"
SOLVER_TYPE="${3:-openfoam}"  # Options: openfoam, fluent, starccm

echo "======================================="
echo "PREPARE MESH FOR CFD SIMULATION"
echo "======================================="
echo "Input mesh: $INPUT_MESH"
echo "Output directory: $OUTPUT_DIR"
echo "Solver type: $SOLVER_TYPE"
echo

# Check if input mesh exists
if [ ! -f "$INPUT_MESH" ]; then
    echo "Error: Input mesh file $INPUT_MESH not found!"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Function to convert mesh to OpenFOAM format
convert_to_openfoam() {
    local input_mesh="$1"
    local output_dir="$2"
    
    echo "Converting mesh to OpenFOAM format..."
    
    # Create system directory and controlDict file
    mkdir -p "$output_dir/system"
    cat > "$output_dir/system/controlDict" << EOF
/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2212                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      controlDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

application     simpleFoam;

startFrom       startTime;

startTime       0;

stopAt          endTime;

endTime         1000;

deltaT          1;

writeControl    timeStep;

writeInterval   100;

purgeWrite      0;

writeFormat     ascii;

writePrecision  6;

writeCompression off;

timeFormat      general;

timePrecision   6;

runTimeModifiable true;

// ************************************************************************* //
EOF

    # Create fvSchemes file
    cat > "$output_dir/system/fvSchemes" << EOF
/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2212                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSchemes;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

ddtSchemes
{
    default         steadyState;
}

gradSchemes
{
    default         Gauss linear;
}

divSchemes
{
    default         none;
    div(phi,U)      bounded Gauss limitedLinearV 1;
    div(phi,k)      bounded Gauss limitedLinear 1;
    div(phi,epsilon) bounded Gauss limitedLinear 1;
    div(phi,omega)  bounded Gauss limitedLinear 1;
    div(phi,nuTilda) bounded Gauss limitedLinear 1;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
    div(nonlinearStress) Gauss linear;
}

laplacianSchemes
{
    default         Gauss linear corrected;
}

interpolationSchemes
{
    default         linear;
}

snGradSchemes
{
    default         corrected;
}

wallDist
{
    method meshWave;
}

// ************************************************************************* //
EOF

    # Create fvSolution file
    cat > "$output_dir/system/fvSolution" << EOF
/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2212                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSolution;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

solvers
{
    p
    {
        solver          GAMG;
        tolerance       1e-7;
        relTol          0.01;
        smoother        GaussSeidel;
    }

    "(U|k|epsilon|omega|nuTilda)"
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-8;
        relTol          0.1;
    }
}

SIMPLE
{
    nNonOrthogonalCorrectors 0;
    consistent      yes;

    residualControl
    {
        p               1e-5;
        U               1e-5;
        "(k|epsilon|omega|nuTilda)" 1e-5;
    }
}

relaxationFactors
{
    equations
    {
        U               0.9;
        "(k|epsilon|omega|nuTilda)" 0.7;
    }
}

// ************************************************************************* //
EOF

    # Create mesh conversion script
    cat > "$output_dir/system/foamConvertOptions" << EOF
/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2212                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      meshConvertOptions;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

convertToMeters 0.001;  // Convert mm to m

mergeSurfacePatches true;

// How to handle faces on the boundary
boundary
{
    inlet
    {
        type            patch;
        physicalType    inlet;
    }
    
    outlet
    {
        type            patch;
        physicalType    outlet;
    }
    
    walls
    {
        type            wall;
        physicalType    wall;
    }
    
    defaultFaces
    {
        type            wall;
        physicalType    wall;
    }
}

// ************************************************************************* //
EOF

    # Create initial field files directory
    mkdir -p "$output_dir/0"
    
    # Create U initial field
    cat > "$output_dir/0/U" << EOF
/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2212                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       volVectorField;
    object      U;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 1 -1 0 0 0 0];

internalField   uniform (0 0 0);

boundaryField
{
    inlet
    {
        type            fixedValue;
        value           uniform (10 0 0);
    }
    
    outlet
    {
        type            zeroGradient;
    }
    
    walls
    {
        type            noSlip;
    }
    
    defaultFaces
    {
        type            noSlip;
    }
}

// ************************************************************************* //
EOF

    # Create p initial field
    cat > "$output_dir/0/p" << EOF
/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2212                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      p;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform 0;

boundaryField
{
    inlet
    {
        type            zeroGradient;
    }
    
    outlet
    {
        type            fixedValue;
        value           uniform 0;
    }
    
    walls
    {
        type            zeroGradient;
    }
    
    defaultFaces
    {
        type            zeroGradient;
    }
}

// ************************************************************************* //
EOF

    # Create k initial field
    cat > "$output_dir/0/k" << EOF
/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2212                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      k;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform 0.1;

boundaryField
{
    inlet
    {
        type            fixedValue;
        value           uniform 0.1;
    }
    
    outlet
    {
        type            zeroGradient;
    }
    
    walls
    {
        type            kqRWallFunction;
        value           uniform 0.1;
    }
    
    defaultFaces
    {
        type            kqRWallFunction;
        value           uniform 0.1;
    }
}

// ************************************************************************* //
EOF

    # Create epsilon initial field
    cat > "$output_dir/0/epsilon" << EOF
/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2212                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      epsilon;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -3 0 0 0 0];

internalField   uniform 0.1;

boundaryField
{
    inlet
    {
        type            fixedValue;
        value           uniform 0.1;
    }
    
    outlet
    {
        type            zeroGradient;
    }
    
    walls
    {
        type            epsilonWallFunction;
        value           uniform 0.1;
    }
    
    defaultFaces
    {
        type            epsilonWallFunction;
        value           uniform 0.1;
    }
}

// ************************************************************************* //
EOF

    # Create viscosity field
    cat > "$output_dir/0/nut" << EOF
/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2212                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      nut;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -1 0 0 0 0];

internalField   uniform 0;

boundaryField
{
    inlet
    {
        type            calculated;
        value           uniform 0;
    }
    
    outlet
    {
        type            calculated;
        value           uniform 0;
    }
    
    walls
    {
        type            nutkWallFunction;
        value           uniform 0;
    }
    
    defaultFaces
    {
        type            nutkWallFunction;
        value           uniform 0;
    }
}

// ************************************************************************* //
EOF

    # Create transportProperties file
    mkdir -p "$output_dir/constant"
    cat > "$output_dir/constant/transportProperties" << EOF
/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2212                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      transportProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

transportModel  Newtonian;

nu              [0 2 -1 0 0 0 0] 1.5e-05;

// ************************************************************************* //
EOF

    # Create turbulence properties
    cat > "$output_dir/constant/turbulenceProperties" << EOF
/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2212                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      turbulenceProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

simulationType  RAS;

RAS
{
    RASModel        kEpsilon;

    turbulence      on;

    printCoeffs     on;
}

// ************************************************************************* //
EOF

    # Create a run script
    cat > "$output_dir/run.sh" << EOF
#!/bin/bash
set -e

# Check if OpenFOAM environment is sourced
if [ -z "\$WM_PROJECT" ]; then
    echo "Error: OpenFOAM environment not found!"
    echo "Please source the OpenFOAM environment file first. For example:"
    echo "  source /usr/lib/openfoam/openfoam2212/etc/bashrc"
    exit 1
fi

# Convert the mesh
if [ ! -d "constant/polyMesh" ]; then
    echo "Converting mesh from GMSH to OpenFOAM format..."
    gmshToFoam "$input_mesh"
    
    # Fix boundary conditions
    createPatch -overwrite
    
    # Check mesh quality
    checkMesh
fi

# Initialize fields
echo "Initializing fields..."
setFields

# Run the simulation
echo "Starting simulation with simpleFoam..."
simpleFoam

echo "Simulation completed!"
EOF
    chmod +x "$output_dir/run.sh"
    
    # Create an allrun script for convenience
    cat > "$output_dir/Allrun" << EOF
#!/bin/bash
cd \${0%/*} || exit 1

# Source OpenFOAM run functions
. \${WM_PROJECT_DIR:?}/bin/tools/RunFunctions

# Convert mesh if needed
if [ ! -d constant/polyMesh ]
then
    runApplication gmshToFoam "$input_mesh"
    runApplication createPatch -overwrite
fi

# Check mesh quality
runApplication checkMesh

# Run solver
runApplication $(getApplication)

# Post-processing
#runApplication postProcess -func vorticity

echo "Case complete!"
EOF
    chmod +x "$output_dir/Allrun"
    
    # Create view script for paraview
    cat > "$output_dir/view.sh" << EOF
#!/bin/bash
paraFoam -touch
paraview paraFoam.foam &
EOF
    chmod +x "$output_dir/view.sh"
    
    echo "OpenFOAM case setup complete!"
    echo "To run the simulation:"
    echo "  1. Source OpenFOAM environment: source /usr/lib/openfoam/openfoam2212/etc/bashrc"
    echo "  2. Navigate to $output_dir"
    echo "  3. Run: ./Allrun"
    echo "  4. For visualization: ./view.sh"
}

# Function to convert mesh to Fluent format
convert_to_fluent() {
    local input_mesh="$1"
    local output_dir="$2"
    
    echo "Converting mesh to ANSYS Fluent format..."
    
    # Create conversion script
    PYTHON_SCRIPT=$(mktemp --suffix=.py)
    cat <<EOT > "$PYTHON_SCRIPT"
#!/usr/bin/env python3
import gmsh
import sys

# Initialize Gmsh
gmsh.initialize()

# Open the mesh file
gmsh.open("$input_mesh")

# Save as Fluent mesh
gmsh.write("$output_dir/intake.msh")

# Finalize gmsh
gmsh.finalize()
print("Converted to Fluent mesh format: $output_dir/intake.msh")
EOT

    # Run the script
    python3 "$PYTHON_SCRIPT"
    rm "$PYTHON_SCRIPT"
    
    # Create Fluent journal file for setup
    cat > "$output_dir/setup.jou" << EOF
; Fluent Journal File for Intake Manifold Setup
; Run with: fluent 3d -g -i setup.jou

; Read the mesh
/file/read-case intake.msh

; Scale the mesh (convert mm to m)
/mesh/scale 0.001 0.001 0.001

; Set up the model - standard k-epsilon
/define/models/viscous/ke-standard yes

; Set material properties
/define/materials/change-create air air yes constant 1.225 yes constant 1.7894e-05 yes constant 0.0242 yes constant 1006.43 yes

; Set boundary conditions
; Wall boundaries
/define/boundary-conditions/wall walls () no 0 no 0 no 0 no 0 no no no
/define/boundary-conditions/wall defaultFaces () no 0 no 0 no 0 no 0 no no no

; Inlet boundary
/define/boundary-conditions/velocity-inlet inlet () no 0 yes yes no 10 no 0 no 0 yes 5 10 no no yes

; Outlet boundary
/define/boundary-conditions/pressure-outlet outlet () no 0 no 0 no no yes no

; Set solver parameters
/solve/set/p-v-coupling 24
/solve/set/gradient-scheme no yes
/solve/set/discretization-scheme/pressure 12
/solve/set/discretization-scheme/mom 1
/solve/set/discretization-scheme/k 1
/solve/set/discretization-scheme/epsilon 1
/solve/set/under-relaxation pressure 0.3
/solve/set/under-relaxation mom 0.7
/solve/set/under-relaxation k 0.8
/solve/set/under-relaxation epsilon 0.8
/solve/set/under-relaxation turb-viscosity 1.0

; Initialize the solution
/solve/initialize/compute-defaults/all-zones
/solve/initialize/initialize-flow

; Save the case
/file/write-case-data intake-setup.cas
/file/confirm-overwrite yes

; Exit
/exit
yes
EOF
    
    echo "Fluent case setup complete!"
    echo "To run the simulation:"
    echo "  1. Navigate to $output_dir"
    echo "  2. Run: fluent 3d -g -i setup.jou"
    echo "  3. Open intake-setup.cas in Fluent to continue the simulation"
}

# Function to convert mesh to Star-CCM+ format
convert_to_starccm() {
    local input_mesh="$1"
    local output_dir="$2"
    
    echo "Converting mesh to Star-CCM+ format..."
    
    # Create conversion script
    PYTHON_SCRIPT=$(mktemp --suffix=.py)
    cat <<EOT > "$PYTHON_SCRIPT"
#!/usr/bin/env python3
import gmsh
import sys

# Initialize Gmsh
gmsh.initialize()

# Open the mesh file
gmsh.open("$input_mesh")

# Save as CGNS format (which Star-CCM+ can import)
gmsh.write("$output_dir/intake.cgns")

# Finalize gmsh
gmsh.finalize()
print("Converted to CGNS format for Star-CCM+: $output_dir/intake.cgns")
EOT

    # Run the script
    python3 "$PYTHON_SCRIPT"
    rm "$PYTHON_SCRIPT"
    
    # Create a readme file with import instructions
    cat > "$output_dir/README.txt" << EOF
Star-CCM+ Import Instructions
============================

1. Launch Star-CCM+
2. Create a new simulation
3. Import the mesh:
   - File > Import > CGNS...
   - Select intake.cgns
   - In the import options:
     - Set length unit to millimeter
     - Check "Create boundaries from patch names"
     - Check "Create regions from zone names"
   - Click OK

4. Set up physics models:
   - Three-dimensional
   - Steady state
   - Single component gas
   - Segregated flow
   - Reynolds-Averaged Navier-Stokes
   - K-Epsilon turbulence
   - All y+ wall treatment

5. Create boundary conditions:
   - inlet: Velocity inlet (10 m/s in x-direction)
   - outlet: Pressure outlet (0 Pa gauge pressure)
   - walls: Wall (no-slip)
   - defaultFaces: Wall (no-slip)

6. Initialize and run the simulation
EOF
    
    echo "Star-CCM+ case setup complete!"
    echo "See $output_dir/README.txt for import and setup instructions"
}

# Convert based on selected solver type
case "$SOLVER_TYPE" in
    openfoam)
        convert_to_openfoam "$INPUT_MESH" "$OUTPUT_DIR"
        ;;
    fluent)
        convert_to_fluent "$INPUT_MESH" "$OUTPUT_DIR"
        ;;
    starccm)
        convert_to_starccm "$INPUT_MESH" "$OUTPUT_DIR"
        ;;
    *)
        echo "Error: Unsupported solver type: $SOLVER_TYPE"
        echo "Supported solvers: openfoam, fluent, starccm"
        exit 1
        ;;
esac

echo "Done! All files prepared for CFD simulation."
