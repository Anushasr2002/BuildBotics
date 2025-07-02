from fastapi import APIRouter
from fastapi.responses import JSONResponse
from agents.data_manipulation_agent import DataManipulationAgent
from agents.inventory_agent import InventoryAgent
from agents.scheduling_agent import generate_schedule
import os

router = APIRouter()

@router.post("/process_data")
async def process_data(csv_path: dict):
    print("Received request to /process_data with:", csv_path)

    agent = DataManipulationAgent()
    df = agent.process_data(csv_path.get("csv_path"))

    if df is not None:
        print("Data processed successfully. Rows:", len(df))
        return {"status": "processed", "rows": len(df)}
    else:
        print("Data processing failed.")
        return {"status": "error", "message": "Data processing failed."}

@router.post("/check_inventory")
async def check_inventory(request: dict):
    print("Received request to /check_inventory with config:", request)

    config = request.get("config", {})
    if "features" not in config or not config["features"].strip():
        return {
            "status": "error",
            "message": "Missing or empty 'features' in request body. Example: {'features': 'engine_hybrid, tire_allseason'}"
        }

    agent = InventoryAgent()
    result = agent.check_inventory(config)
    return result if result else {"status": "error"}

@router.post("/schedule")
async def get_schedule(data:dict):
    vehicle_type = data.get("vehicle_type")
    features = data.get("features", [])
    if not vehicle_type:
        return JSONResponse({"error": "vehicle_type is required"}, status_code=400)

    print("Received request to /schedule")

    schedule = generate_schedule(vehicle_type)
    if schedule:
        print("Schedule generated successfully.")
        return {"schedule": schedule}
    else:
        print("Schedule generation failed.")
        return {"status": "error"}
