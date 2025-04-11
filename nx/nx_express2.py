import NXOpen

def main():
    """Imports expressions from a file into the work part."""
    
    session = NXOpen.Session.GetSession()
    work_part = session.Parts.Work

    try:
        session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Import Expressions")
        exp_modified, error_messages = work_part.Expressions.ImportFromFile(
            "C:\\Users\\Mohammed\\Desktop\\nx\\expressions.exp", 
            NXOpen.ExpressionCollection.ImportMode.Replace
        )
        if error_messages:
            print("Errors during expression import:")
            for message in error_messages:
                print(message)

    except Exception as e:
        print(f"Error importing expressions: {e}")
    finally:
        session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Update")
        nErrs = session.UpdateManager.DoUpdate(session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Update"))
        session.DeleteUndoMark(session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Update"), None)

        session.SetUndoMarkName(session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Import Expressions"), "Expressions")
        session.DeleteUndoMark(session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Import Expressions"), None)

if __name__ == '__main__':
    main()