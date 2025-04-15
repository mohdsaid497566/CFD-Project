import NXOpen
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Imports expressions from a file into the work part."""
    logging.debug("Starting the import process.")
    
    session = NXOpen.Session.GetSession()
    work_part = session.Parts.Work
    logging.debug("Session and work part initialized.")

    try:
        session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Import Expressions")
        logging.debug("Undo mark set for 'Import Expressions'.")
        
        exp_modified, error_messages = work_part.Expressions.ImportFromFile(
            "C:\\Users\\Mohammed\\Desktop\\Intake-CFD-Project\\nx\\expressions.exp", 
            NXOpen.ExpressionCollection.ImportMode.Replace
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
        
        session.SetUndoMarkName(session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Import Expressions"), "Expressions")
        session.DeleteUndoMark(session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Import Expressions"), None)
        logging.debug("Final cleanup of undo marks completed.")

if __name__ == '__main__':
    main()