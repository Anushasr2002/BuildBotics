import pandas as pd
import json
import os
import re
import traceback
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from config.llm_config import llm

def extract_json_array(text):
    """Extract the first valid JSON array from a string using regex."""
    try:
        print("Raw LLM output before JSON extraction:\n", text)
        text = text.strip().replace("```json", "").replace("```", "")
        text = text.replace("“", "\"").replace("”", "\"")

        match = re.search(r'\[\s*{.*?}\s*\]', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            json_str = json_str.replace(',\n]', '\n]').replace(',]', ']')
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                print("Successfully extracted JSON array.")
                return parsed
            else:
                print("Extracted content is not a list.")
        else:
            print("No valid JSON array found in response.")
    except Exception as e:
        print("JSON array extraction failed:", e)
    return None

def generate_schedule(vehicle_type, output_path=os.path.join("backend", "data", "processed", "schedule.csv")):
    try:
        demand_path = r"FILE_PATH_FOR_OnDemandProductionScheduling- Final PArt 2 (1)\\OnDemandProductionScheduling- Final PArt 1\\backend\\data\\processed\\processed_demand.csv"
        inventory_path = r"FILE_PATH_FOR_OnDemandProductionScheduling- Final PArt 2 (1)\\OnDemandProductionScheduling- Final PArt 1\\backend\\data\\datasets\\inventory.csv"
        inventory_status_path = r"FILE_PATH_FOR_OnDemandProductionScheduling- Final PArt 2 (1)\\OnDemandProductionScheduling- Final PArt 1\\backend\\data\\processed\\inventory_status.csv"
        output_path = os.path.normpath(output_path)

        if not os.path.exists(demand_path):
            raise FileNotFoundError(f"Demand file not found: {demand_path}")
        if not os.path.exists(inventory_path):
            raise FileNotFoundError(f"Inventory file not found: {inventory_path}")
        if not os.path.exists(inventory_status_path):
            raise FileNotFoundError(f"Inventory status file not found: {inventory_status_path}")

        demand_df = pd.read_csv(demand_path).head(60)
        inventory_df = pd.read_csv(inventory_path).head(11)
        inventory_status_df = pd.read_csv(inventory_status_path).head(11)

        demand_data = demand_df.to_dict(orient="records")
        inventory_data = inventory_df.to_dict(orient="records")
        inventory_status_data = inventory_status_df.to_dict(orient="records")

        #allowed_vehicle_types = [vehicle_type] #sorted(set(d['vehicle_type'] for d in demand_data if 'vehicle_type' in d))
        allowed_features = sorted(set(
            feature.strip()
            for d in demand_data if 'features' in d
            for feature in str(d['features']).split(',')
        ))

        allowed_values_text = (
            f"Allowed vehicle types: {vehicle_type}\n"
            f"Allowed features: {', '.join(allowed_features)}\n"
            "Use the allowed features to populate in the 'features' field.\n"
            "Use ONLY these values. Do NOT invent new types or features.\n"
        )

        template = f"""
You are a production scheduler.

Given demand data: {{demand_data}}
And inventory data: {{inventory_data}}
And inventory status data: {{inventory_status_data}}

{allowed_values_text}

Generate a 15-day production schedule. Each item must include:
- "day" (1 to 15)
- "vehicle_type" (must be one of the vehicle_type value from the {allowed_values_text})
- "features" (must be a combination of features from the allowed features listed in {allowed_values_text})
- "quantity" (integer, based on quantity_sold trends in the demand data)

Guidelines:
- Use only vehicle types that appear in the demand data.
- Use only features listed in the allowed features section of {allowed_values_text}. Do NOT use features from demand data or invent new ones.
- Analyze the quantity_sold values to identify trends (e.g., average, seasonal spikes, or fluctuations).
- Vary the features and quantities across days based on those trends.
- Do NOT use simple patterns like increasing or repeating numbers.
- Introduce realistic fluctuations in quantity (e.g., 10, 14, 9, 13...) that reflect demand behavior.
- Do NOT HALLUCINATE with the data and output.
- If ANY item in {{inventory_status_data}} has "status": "insufficient", STOP and return this exact error message: "The components are not available".

Respond ONLY with a valid JSON array. No explanation.

"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["demand_data", "inventory_data","inventory_status_data","allowed_values_text"]
        )
        scheduling_chain = LLMChain(prompt=prompt, llm=llm) if llm else None

        if scheduling_chain:
            try:
                response = scheduling_chain.invoke({
                    "demand_data": demand_data,
                    "inventory_data": inventory_data,
                    "inventory_status_data": inventory_status_data,
                    "allowed_values_text": allowed_values_text
                })
                print("Raw LLM response:", response)
                text = response.get("text", response) if isinstance(response, dict) else response

                with open("llm_raw_response.txt", "w", encoding="utf-8") as f:
                    f.write(text)

                schedule = extract_json_array(text)
                if not schedule:
                    raise ValueError("No valid JSON array found in response")

                with open("parsed_schedule_debug.json", "w", encoding="utf-8") as f:
                    json.dump(schedule, f, indent=2)

                required_keys = {"day", "vehicle_type", "features", "quantity"}
                for i, item in enumerate(schedule):
                    if not isinstance(item, dict):
                        raise ValueError(f"Schedule item at index {i} is not a dictionary: {item}")
                    if item["vehicle_type"] != "SUV" and item["vehicle_type"] != "Sedan":
                        raise ValueError(f"Invalid vehicle_type : {item['vehicle_type']}")
                    for feature in item["features"].split(','):
                        if feature.strip() not in allowed_features:
                            raise ValueError(f"Invalid feature at index {i}: {feature}")
                    cleaned_keys = {k.strip('"').strip() for k in item.keys()}
                    if not required_keys.issubset(cleaned_keys):
                        raise ValueError(f"Missing required keys in item {i}: {item}")

            except Exception as e:
                print(f"LLM scheduling failed: {e}")
                return None
        else:
            print("No LLM available; cannot generate schedule.")
            return None

        schedule_df = pd.DataFrame(schedule)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        schedule_df.to_csv(output_path, index=False)
        print(f"Saved to {output_path}")
        return schedule

    except Exception as e:
        print("Error generating schedule:")
        print(traceback.format_exc())
        return None
