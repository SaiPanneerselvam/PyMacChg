import json
import os

def print_section(title, data):
    print(f"\n=== {title} ===")
    if isinstance(data, dict):
        for k, v in data.items():
            print(f"{k}: {v}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                print("-" * 40)
                for k, v in item.items():
                    print(f"{k}: {v}")
            else:
                print(item)
    else:
        print(data)

def main():
    json_path = "hardware.json"
    if not os.path.exists(json_path):
        print("hardware.json not found.")
        return

    with open(json_path, "r") as f:
        hardware_data = json.load(f)

    print("===== CyMacZxC: Hardware Information Decompressor =====")
    for section, data in hardware_data.items():
        print_section(section, data)

if __name__ == "__main__":
    main()
