import win32com.client  # Python ActiveX Client
Input1 = 700  # First Number to Add
Input2 = 200  # Second Number to Add
LabVIEW = win32com.client.Dispatch("Labview.Application")
VI = LabVIEW.getvireference('C:\\Friedrich KH\\python.vi')  # Path to LabVIEW VI
VI._FlagAsMethod("Call")  # Flag "Call" as Method
VI.setcontrolvalue('Input 1', str(Input1))  # Set Input 1
VI.setcontrolvalue('Input 2', str(Input2))  # Set Input 2
VI.Call()  # Run the VI
result = VI.getcontrolvalue('Sum')  # Get return value
print(result)  # Print value to console