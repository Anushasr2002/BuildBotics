import pandas as pd
import json
import os
import traceback
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from config.llm_config import llm

template = """
You are an inventory assistant.
Check if the inventory is sufficient for the following features: {features}
Inventory data (sample): {inventory_data}
Respond ONLY with a valid JSON object containing:
- "status": either "sufficient" or "insufficient"
- "parts_needed": a dictionary of feature names and quantities from the {features} or "none" if no parts are needed 
- "action": either "Proceed" or "Hold"

Example:
{{ 
  "status": "sufficient", 
  "parts_needed": {{"engine_hybrid": 5, "tire_allseason": 10}}, 
  "action": "Proceed" 
}}

Important:
- Respond ONLY with a valid JSON object. Do not include any explanation, formatting, or extra characters. Do not use markdown or bullet points.
"""


prompt = PromptTemplate(template=template, input_variables=["features", "inventory_data"])
inventory_chain = LLMChain(prompt=prompt, llm=llm) if llm else None

class InventoryAgent:
    def extract_json(self, text):
        try:
            print("Raw LLM output before JSON extraction:\n", text)
            text = text.strip().replace("```json", "").replace("```", "")
            text = text.replace("“", "\"").replace("”", "\"")

            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1 and end > start:
                json_str = text[start:end].strip()
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    return parsed
                else:
                    print("Extracted content is not a dictionary.")
            else:
                print("No valid JSON object found.")
        except Exception as e:
            print("JSON extraction failed:", e)
        return None

    def check_inventory(self, config, output_path=os.path.join("backend", "data", "processed", "inventory_status.csv")):
        try:
            inventory_path = os.path.normpath(
                r"FILE_PATH_FOR_OnDemandProductionScheduling- Final PArt 1\backend\data\datasets\inventory.csv"
            )
            output_path = os.path.normpath(output_path)

            print("Current working directory:", os.getcwd())
            print("Looking for file at:", inventory_path)

            if not os.path.exists(inventory_path):
                raise FileNotFoundError(f"Inventory file not found: {inventory_path}")

            inventory_df = pd.read_csv(inventory_path).head(11)

            raw_features = config.get("features", "")
            print("Raw features from config:", raw_features)
            features = [f.strip() for f in raw_features.split(",") if f.strip()]
            if not features:
                raise ValueError("No valid features provided in config.")

            inventory_data = inventory_df.to_dict(orient="records")

            if inventory_chain:
                response = inventory_chain.invoke({
                    "features": features,
                    "inventory_data": inventory_data
                })
                print("Raw LLM response:", response)
                text = response.get("text", response) if isinstance(response, dict) else response
                result = self.extract_json(text)

                required_keys = {"status", "parts_needed", "action"}
                if result:
                    cleaned_keys = {k.strip('"').strip() for k in result.keys()}
                    print("Inventory response keys:", cleaned_keys)
                    if not required_keys.issubset(cleaned_keys):
                        raise ValueError(f"Missing required keys in LLM response: {result}")
                else:
                    raise ValueError("Invalid or empty LLM response")

            else:
                raise RuntimeError("No LLM available for inventory check.")

            status_df = pd.DataFrame([result])
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            status_df.to_csv(output_path, index=False)
            print(f"Saved to {output_path}")
            return result

        except Exception as e:
            print("Error checking inventory:")
            print(traceback.format_exc())
            return None
