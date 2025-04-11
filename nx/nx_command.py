import subprocess
import time
import os

def run_nx_commands():
    try:
        nx_desktop_path = r"C:\Users\Mohammed\Desktop\nx" #added raw string
        ugii_path = r"C:\Program Files\Siemens\NX2406\UGII" #added raw string

        os.chdir(ugii_path)
        time.sleep(2)

        command = rf'nxcommand.bat && run_journal "{nx_desktop_path}" "nx_express2.py" -args "{nx_desktop_path}" "INSTAKE3D.prt" && run_journal "{nx_desktop_path}" "nx_export.py" -args "{nx_desktop_path}" "INSTAKE3D.prt && EXIT"'

        subprocess.run(["cmd.exe", "/c", command], check=True, shell=True)

        print("NX operations completed successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error running NX commands: {e}")
    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

run_nx_commands()