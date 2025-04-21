from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import RedirectResponse

from pydantic import BaseModel
import uuid
import random
from datetime import datetime
from typing import List, Optional
import math

app = FastAPI()

# Pydantic models (same as before)
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
    total: int
    page: int
    page_size: int
    response: List[Device]

# Function to generate random device data
def generate_device_list(num_devices: int) -> List[Device]:
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

# Total number of devices
TOTAL_DEVICES = 5
all_devices = generate_device_list(TOTAL_DEVICES)

@app.get("/devices", response_model=DevicesResponse)
async def get_devices(
    page: int = Query(1, ge=1, description="Page number to retrieve"),
    page_size: int = Query(10, ge=1, le=1000, description="Number of devices per page")
):
    """
    Retrieves a paginated list of random device data. If the requested page is beyond the last valid page,
    it redirects to the URL of the last valid page.
    """
    timestamp = datetime.now()
    message_id = str(random.randint(1000000000000000000000, 9999999999999999999999))

    last_page = math.ceil(TOTAL_DEVICES / page_size) if page_size > 0 else 1

    if page > last_page and last_page > 0:
        redirect_url = f"/devices?page={last_page}&page_size={page_size}"
        return RedirectResponse(redirect_url, status_code=302)
    elif page < 1:
        redirect_url = f"/devices?page=1&page_size={page_size}"
        return RedirectResponse(redirect_url, status_code=302)

    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paged_devices = all_devices[start_index:end_index]

    return DevicesResponse(
        messageId=message_id,
        timestamp=timestamp,
        total=len(all_devices),
        page=page,
        page_size=page_size,
        response=paged_devices
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)