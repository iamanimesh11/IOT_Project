import requests,sys,os,random


AIRFLOW_HOME = os.getenv("AIRFLOW_HOME", "/opt/airflow")  # Default to Airflow's path

if AIRFLOW_HOME != "/opt/airflow":
    BASE_DIR = os.path.abspath(os.path.join(AIRFLOW_HOME, ".."))  
    print("BASE_DIR:", BASE_DIR) 
    AIRFLOW_HOME = BASE_DIR


CREDENTIALS_PATH = os.path.join(AIRFLOW_HOME, "common", "credentials")
COMMON_PATH = os.path.join(AIRFLOW_HOME, "common", "logging_and_monitoring")
sys.path.append(COMMON_PATH)
COMMON_PATH = os.path.join(AIRFLOW_HOME, "common","logging_and_monitoring","logs") 
sys.path.append(COMMON_PATH)

from utils.firebase_db_api_track_util import ApiMonitor
from centralized_logging import setup_logger

Script_logs_path=os.path.join(COMMON_PATH, "api_utils.log")

road_logger = setup_logger("Road_Data_ETL", "api_utils", "python", Script_logs_path)

traffic_logger = setup_logger("Traffic_Data_ETL", "api_utils", "python", Script_logs_path)

monitor = ApiMonitor()
Wmonitor = ApiMonitor()

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import uuid
import random
from datetime import datetime
from typing import List, Optional

app = FastAPI()


# Pydantic models
class DeviceInfo(BaseModel):
    deviceType: str
    modelName: str
    alias: str
    reportable: bool


class Device(BaseModel):
    deviceId: uuid.UUID
    deviceInfo: DeviceInfo


class DevicesResponse(BaseModel):
    messageId: str
    timestamp: datetime
    response: List[Device]


# Function to generate random device data (now returns a list of Device objects)
def generate_device_list(num_devices: int = 100) -> List[Device]:
    device_list = []
    device_types = ["Refrigerator", "WashingMachine", "AirPurifier", "Oven", "AirConditioner", "Television"]
    model_options = {
        "Refrigerator": ["GL-T432APZY", "GL-B221ASCY", "LRFGC2706S"],
        "WashingMachine": ["T70VBMB1Z", "FHB1207Z2W", "FH0B8NDL2"],
        "AirPurifier": ["AS60GHWG0", "AS95GDWV0", "AP551AWFA"],
        "Oven": ["MJEN326SFW", "WSED7665B", "MA3884VC"],
        "AirConditioner": ["LS-Q18YNZA", "MS-Q12UVXA", "TS-Q19YNZE1"],
        "Television": ["OLED55C46LA", "43UQ7500PSF", "32LM560BPTC"]
    }

    for _ in range(num_devices):
        device_type = random.choice(device_types)
        device = Device(
            deviceId=uuid.uuid4(),
            deviceInfo=DeviceInfo(
                deviceType=device_type,
                modelName=random.choice(model_options[device_type]),
                alias=f"nickname_{random.randint(1, 100)}",
                reportable=random.choice([True, False])
            )
        )
        device_list.append(device)
    return device_list


@app.get("/devices", response_model=DevicesResponse)
async def get_devices(count: Optional[int] = Query(None, description="Number of devices to retrieve")):
    """
    Generates and retrieves a list of random device data with a single message ID and timestamp for the entire response.
    You can specify the number of devices to return using the 'count' query parameter.
    """
    timestamp = datetime.now()
    message_id = str(random.randint(1000000000000000000000, 9999999999999999999999))

    if count is None:
        devices = generate_device_list()
    elif count >= 0:
        devices = generate_device_list(count)
    else:
        raise HTTPException(status_code=400, detail="Requested count must be a non-negative integer.")

    return DevicesResponse(messageId=message_id, timestamp=timestamp, response=devices)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
