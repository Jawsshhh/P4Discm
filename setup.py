from cx_Freeze import setup, Executable
import sys

# Dependencies
build_exe_options = {
    "packages": ["grpc", "flask", "flask_cors", "numpy", "PIL"],
    "include_files": [
        ("templates/", "templates/"),
        ("generated/", "generated/")
    ],
    "excludes": ["tkinter"]
}

# Base for hiding console on Windows
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="TrainingDashboard",
    version="1.0",
    description="ML Training Dashboard",
    options={"build_exe": build_exe_options},
    executables=[
        Executable("client/web_dashboard.py", base=base, target_name="dashboard.exe"),
        Executable("server/training_server.py", target_name="server.exe")
    ]
)