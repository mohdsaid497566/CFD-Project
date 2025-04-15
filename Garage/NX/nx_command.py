import NXOpen
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def import_expressions(session, work_part, expressions_file):
    """Imports expressions from a file into the work part."""
    logging.debug("Starting the import process.")
    try:
        session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Import Expressions")
        logging.debug("Undo mark set for 'Import Expressions'.")
        
        exp_modified, error_messages = work_part.Expressions.ImportFromFile(
            expressions_file, NXOpen.ExpressionCollection.ImportMode.Replace
        )
        logging.debug(f"Expressions modified: {exp_modified}")
        
        if error_messages:
            logging.warning("Errors during expression import:")
            for message in error_messages:
                logging.warning(message)
    except Exception as e:
        logging.error(f"Error importing expressions: {e}")
    finally:
        session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Update")
        logging.debug("Undo mark set for 'Update'.")
        nErrs = session.UpdateManager.DoUpdate(session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Update"))
        logging.debug(f"Number of errors during update: {nErrs}")
        session.DeleteUndoMark(session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Update"), None)
        logging.debug("Deleted undo mark for 'Update'.")

def export_to_step(session, input_file, output_file):
    """Exports the model to a STEP file."""
    logging.debug("Starting the export process.")
    try:
        work_part = session.Parts.Open(input_file)
        logging.debug(f"Opened part file: {input_file}")
    except NXOpen.NXException as ex:
        logging.error(f"Error opening part file: {ex}")
        return

    mark_id1 = session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Export STEP File")
    step_creator = session.DexManager.CreateStepCreator()

    # Configure STEP export options
    step_creator.ExportAs = NXOpen.StepCreator.ExportAsOption.Ap242ED2
    step_creator.ObjectTypes.Curves = True
    step_creator.ObjectTypes.Surfaces = True
    step_creator.ObjectTypes.Solids = True
    step_creator.ObjectTypes.FacetBodies = True
    step_creator.ObjectTypes.PmiData = True
    step_creator.InputFile = input_file
    step_creator.OutputFile = output_file
    step_creator.FileSaveFlag = False
    step_creator.LayerMask = "1-256"
    step_creator.ProcessHoldFlag = True

    try:
        step_creator.Commit()
        logging.info(f"STEP file exported successfully: {output_file}")
    except NXOpen.NXException as ex:
        logging.error(f"Error exporting STEP file: {ex}")
    finally:
        step_creator.Destroy()
        logging.debug("Destroyed STEP creator.")

def main():
    session = NXOpen.Session.GetSession()

    # Define file paths
    expressions_file = "C:\\Users\\Mohammed\\Desktop\\Intake-CFD-Project\\nx\\expressions.exp"
    input_file = "C:\\Users\\Mohammed\\Desktop\\Intake-CFD-Project\\nx\\INTAKE3D.prt"
    output_file = "C:\\Users\\Mohammed\\Desktop\\Intake-CFD-Project\\nx\\INTAKE3D.stp"

    # Import expressions
    work_part = session.Parts.Work
    import_expressions(session, work_part, expressions_file)

    # Export to STEP
    export_to_step(session, input_file, output_file)

if __name__ == '__main__':
    main()