import json

def read_from_json_file():
    input_file = "device_models.json"
    try:
        with open(input_file, 'r') as f:
            loaded_data = json.load(f)
            return loaded_data
            # Now you can access the device types and model names from the loaded_data dictionary
            for device, model in loaded_data.items():
                print(f"Device Type: {device}, Model: {model}")
    except FileNotFoundError:
        print(f"Error: '{input_file}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{input_file}'.")
    except IOError as e:
        print(f"Error reading from '{input_file}': {e}")
        

x =read_from_json_file()
for device_type, model_name in x.items():
    print(device_type)
    print(model_name)
