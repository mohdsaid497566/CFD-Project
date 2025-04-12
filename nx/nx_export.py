import NXOpen
import sys

def main():
    the_session = NXOpen.Session.GetSession()

    # Get the input file path from arguments or use the default
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "C:\\Users\\Mohammed\\Desktop\\Intake-CFD-Project\\nx\\INTAKE3D.prt"  # Default path

    # Ensure the input file exists
    try:
        work_part = the_session.Parts.Open(input_file)  # Explicitly open the part file
    except NXOpen.NXException as ex:
        print(f"Error opening part file: {ex}")
        return

    # Set undo mark for exporting the STEP file
    mark_id1 = the_session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Export STEP File")

    step_creator = the_session.DexManager.CreateStepCreator()

    # Configure STEP export options
    step_creator.ExportAs = NXOpen.StepCreator.ExportAsOption.Ap242ED2  # Final Export Type
    step_creator.ObjectTypes.Curves = True
    step_creator.ObjectTypes.Surfaces = True
    step_creator.ObjectTypes.Solids = True
    step_creator.ObjectTypes.FacetBodies = True
    step_creator.ObjectTypes.PmiData = True

    # Get the output file path from arguments or use the default
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = "C:\\Users\\Mohammed\\Desktop\\Intake-CFD-Project\\nx\\INTAKE3D.stp"  # Default output path

    step_creator.InputFile = input_file
    step_creator.OutputFile = output_file

    step_creator.FileSaveFlag = False
    step_creator.LayerMask = "1-256"
    step_creator.ProcessHoldFlag = True

    # Commit the STEP export
    try:
        step_creator.Commit()
        print(f"STEP file exported successfully: {output_file}")
    except NXOpen.NXException as ex:
        print(f"Error exporting STEP file: {ex}")
    finally:
        step_creator.Destroy()  # Clean up the step creator

if __name__ == '__main__':
    main()