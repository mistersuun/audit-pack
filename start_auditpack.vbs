Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\Auditeur\Documents\Projects\audit-pack"
WshShell.Run "python main.py", 0, False
