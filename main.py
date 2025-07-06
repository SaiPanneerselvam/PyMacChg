import sys
import time
import os
import subprocess
import plistlib
import json
import re

def parse_key_value_block(text):
    """Parse blocks of 'Key: Value' lines into a dict."""
    info = {}
    for line in text.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            info[key.strip()] = value.strip()
    return info

def parse_system_profiler(text):
    """Parse system_profiler output into a dict."""
    info = {}
    for line in text.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            info[key.strip()] = value.strip()
    return info

def parse_networksetup(text):
    """Parse networksetup output into a list of interfaces."""
    interfaces = []
    current = {}
    for line in text.splitlines():
        if line.startswith("Hardware Port:"):
            if current:
                interfaces.append(current)
            current = {"Hardware Port": line.split(":", 1)[1].strip()}
        elif line.startswith("Device:"):
            current["Device"] = line.split(":", 1)[1].strip()
        elif line.startswith("Ethernet Address:"):
            current["Ethernet Address"] = line.split(":", 1)[1].strip()
    if current:
        interfaces.append(current)
    return interfaces

def parse_diskutil_info(text):
    """Parse diskutil info output into a dict."""
    return parse_key_value_block(text)

def parse_diskutil_list(text):
    """Parse diskutil list output into a list of disks and partitions."""
    disks = []
    disk = None
    for line in text.splitlines():
        if line.startswith("/dev/"):
            if disk:
                disks.append(disk)
            disk = {"Device": line.strip(), "Partitions": []}
        elif line.strip().startswith("0:") or line.strip().startswith("1:") or line.strip().startswith("2:"):
            if disk is not None:
                disk["Partitions"].append(line.strip())
    if disk:
        disks.append(disk)
    return disks

def main():
    hardware_data = {}

    if sys.platform == "darwin":
        print("Detected platform as Darwin Operating System.")
        print("Starting system delay cooldown...")
        cooldown(1)
        print("====================== Welcome to PyMacCharge ======================")
        print()
        print("PyMacCharge automatically scans and finds all of the information about your computer")
        print("Fetching SMBIOS information...")

        # --- SMBIOS ---
        try:
            result = subprocess.run(
                ["system_profiler", "SPHardwareDataType"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                smbios = parse_system_profiler(result.stdout)
                print("Model Identifier:", smbios.get("Model Identifier"))
                print("Serial Number (system):", smbios.get("Serial Number (system)"))
                print("Hardware UUID:", smbios.get("Hardware UUID"))
                hardware_data["SMBIOS"] = smbios
            else:
                print("Failed to fetch SMBIOS information. Error:", result.stderr)
                hardware_data["SMBIOS"] = {"error": result.stderr}
        except Exception as e:
            print("An error occurred while fetching SMBIOS information:", e)
            hardware_data["SMBIOS"] = {"error": str(e)}

        print("\nFetching additional system information...\n")

        # --- OS Version ---
        try:
            result = subprocess.run(
                ["sw_vers"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                os_info = parse_key_value_block(result.stdout)
                print("macOS Version:", os_info.get("ProductVersion"))
                hardware_data["macOS"] = os_info
            else:
                hardware_data["macOS"] = {"error": result.stderr}
        except Exception as e:
            hardware_data["macOS"] = {"error": str(e)}

        # --- Uptime ---
        try:
            result = subprocess.run(
                ["uptime"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                print("Uptime:", result.stdout.strip())
                hardware_data["Uptime"] = result.stdout.strip()
            else:
                hardware_data["Uptime"] = {"error": result.stderr}
        except Exception as e:
            hardware_data["Uptime"] = {"error": str(e)}

        # --- Memory ---
        try:
            result = subprocess.run(
                ["sysctl", "hw.memsize"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                mem_bytes = int(result.stdout.strip().split(":")[1])
                mem_gb = mem_bytes / (1024 ** 3)
                print(f"Memory: {mem_gb:.2f} GB")
                hardware_data["Memory"] = {"Bytes": mem_bytes, "GB": round(mem_gb, 2)}
            else:
                hardware_data["Memory"] = {"error": result.stderr}
        except Exception as e:
            hardware_data["Memory"] = {"error": str(e)}

        # --- CPU ---
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                print("CPU:", result.stdout.strip())
                hardware_data["CPU"] = result.stdout.strip()
            else:
                hardware_data["CPU"] = {"error": result.stderr}
        except Exception as e:
            hardware_data["CPU"] = {"error": str(e)}

        # --- Disk Info ---
        try:
            result = subprocess.run(
                ["diskutil", "info", "/"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                disk_info = parse_diskutil_info(result.stdout)
                print("Disk Info:", disk_info.get("Device Identifier"), disk_info.get("Volume Name"))
                hardware_data["Disk Info"] = disk_info
            else:
                hardware_data["Disk Info"] = {"error": result.stderr}
        except Exception as e:
            hardware_data["Disk Info"] = {"error": str(e)}

        # --- Network Info ---
        try:
            result = subprocess.run(
                ["networksetup", "-listallhardwareports"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                network_info = parse_networksetup(result.stdout)
                print("Network Interfaces:")
                for iface in network_info:
                    print(iface)
                hardware_data["Network Interfaces"] = network_info
            else:
                hardware_data["Network Interfaces"] = {"error": result.stderr}
        except Exception as e:
            hardware_data["Network Interfaces"] = {"error": str(e)}

        # --- Running Processes ---
        try:
            result = subprocess.run(
                ["ps", "aux"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                # Only keep the first 10 processes for brevity in JSON
                processes = result.stdout.strip().splitlines()
                header = processes[0]
                proc_list = [dict(zip(header.split(), re.split(r'\s+', p, maxsplit=10))) for p in processes[1:11]]
                hardware_data["Running Processes (sample)"] = proc_list
            else:
                hardware_data["Running Processes (sample)"] = {"error": result.stderr}
        except Exception as e:
            hardware_data["Running Processes (sample)"] = {"error": str(e)}

        # --- Disks and Partitions ---
        try:
            result = subprocess.run(
                ["diskutil", "list"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                disks = parse_diskutil_list(result.stdout)
                hardware_data["Disks and Partitions"] = disks
            else:
                hardware_data["Disks and Partitions"] = {"error": result.stderr}
        except Exception as e:
            hardware_data["Disks and Partitions"] = {"error": str(e)}

        # --- Save to hardware.json (organized) ---
        try:
            with open("hardware.json", "w") as f:
                json.dump(hardware_data, f, indent=2)
        except Exception as e:
            print("Failed to write hardware.json:", e)

    else:
        print("This Program is for macOS. Please check your platform number and BIOS ID.")
        print("Press <RETURN> to exit.")
        input()

def cooldown(s):
    timevar = 0
    print("Verbose Logging Cooldown Status.")
    time.sleep(0.01)
    print("[001] ALERT: Function cooldown() called.")
    time.sleep(0.01)
    print("[002] INFO: Libraries used for function cooldown() time, sys, os.")
    time.sleep(0.0091)
    print("[003] INFO: Function cooldown() started.")
    print("[004] STATUS: Receiving variable condition of cooldown time. If not set, default to 1 seconds.")
    if s is None:
        print("[005] ERROR: No time set in function setup. Defaulting to 1 second.")
        time.sleep(1)
        timevar = 5
    else:
        print(f"[005] INFO: Cooldown time set to {s} seconds.")
        print("[006] INFO: Executing cooldown time...")
        timevar = 6
    print(f"[00{timevar}] STATUS: Finished.")
    time.sleep(0.1)
    print("[00" + str(timevar) + "] INFO: Utilising OS library to clear terminal verbose logging.")
    print("[00" + str(timevar) + "] STATUS: Starting preboot_execute_cause_post_clear for post logclear commands.")
    time.sleep(0.6)
    print("[0" + str(timevar) + "] STATUS: Clearing screen and disabling verbose logging...")
    os.system('clear')

if __name__ == "__main__":
    main()
