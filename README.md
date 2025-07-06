# PyMacChg
##### Searches and dumps excessive amount of hardware, firmware, and software info.

PyMacChg is a command-line python tool that searches the entire computer's hardware and finds all possible information about information such as:

1. **SMBIOS Information**
   - Model Identifier
   - Serial Number (system)
   - Hardware UUID
   - All other key-value pairs from `system_profiler SPHardwareDataType`

2. **macOS Version**
   - ProductName
   - ProductVersion
   - BuildVersion

3. **Uptime**
   - Output of the `uptime` command

4. **Memory**
   - Total memory in bytes
   - Total memory in GB

5. **CPU**
   - CPU brand string

6. **Disk Info**
   - All key-value pairs from `diskutil info /` (e.g., Device Identifier, Volume Name, etc.)

7. **Network Interfaces**
   - List of all network interfaces with:
     - Hardware Port
     - Device
     - Ethernet Address

8. **Running Processes (sample)**
   - First 10 running processes with columns:
     - USER
     - PID
     - %CPU
     - %MEM
     - VSZ
     - RSS
     - TT
     - STAT
     - STARTED
     - TIME
     - COMMAND

9. **Disks and Partitions**
   - List of all disks and their partitions from `diskutil list`
  
Followed by this, the program creates a hardware.json file that contains this information, which some tools can utilise for hardware sniffing.
