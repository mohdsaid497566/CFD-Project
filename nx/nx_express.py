import NXOpen

def main():
    """Exports expressions from the work part to a text file."""
    
    session = NXOpen.Session.GetSession()
    work_part = session.Parts.Work

    # Export expressions to the specified file
    try:
        session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Expressions Export")
        work_part.Expressions.ExportToFile(NXOpen.ExpressionCollection.ExportMode.WorkPart, 
                                            "C:\\Users\\Mohammed\\Desktop\\nx\\expressions", 
                                            NXOpen.ExpressionCollection.SortType.AlphaNum)
    except Exception as e:
        print(f"Error exporting expressions: {e}")
    finally:
        session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Update")
        nErrs = session.UpdateManager.DoUpdate(session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Update"))
        session.DeleteUndoMark(session.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Update"), None)

        session.SetUndoMarkName(session.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Expressions Export"), "Expressions Export")
        
if __name__ == '__main__':
    main()