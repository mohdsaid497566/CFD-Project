import NXOpen

def main():
    the_session = NXOpen.Session.GetSession()
    work_part = the_session.Parts.Work  # Consider adding a check here if needed
    # display_part = the_session.Parts.Display # Not used, so commented out

    mark_id1 = the_session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Export STEP File")

    step_creator = the_session.DexManager.CreateStepCreator()

    step_creator.ExportAs = NXOpen.StepCreator.ExportAsOption.Ap242ED2  # Final Export Type

    # Common Object Types
    step_creator.ObjectTypes.Curves = True
    step_creator.ObjectTypes.Surfaces = True
    step_creator.ObjectTypes.Solids = True
    step_creator.ObjectTypes.FacetBodies = True
    step_creator.ObjectTypes.PmiData = True

    # Input and Output File Paths
    input_file = "C:\\Users\\Mohammed\\Desktop\\nx\\INTAKE3D.prt"
    # Get the output file name from the arguments
    if len(sys.argv) > 1:
        output_file = "C:\\Users\\Mohammed\\Desktop\\nx\\" + sys.argv[1]  # Get the first argument
    else:
        output_file = "C:\\Users\\Mohammed\\Desktop\\nx\\INTAKE3D.stp"  # Default name

    step_creator.InputFile = input_file
    step_creator.OutputFile = output_file

    step_creator.FileSaveFlag = False
    step_creator.LayerMask = "1-256"
    step_creator.ProcessHoldFlag = True

    try:
        step_creator.Commit()  # Export the STEP file
    except NXOpen.NXException as ex:
        print(f"Error exporting STEP file: {ex}")
    finally:
        step_creator.Destroy()  # Clean up the step creator


if __name__ == '__main__':
    main()