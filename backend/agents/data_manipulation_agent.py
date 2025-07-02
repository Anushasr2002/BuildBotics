import os
import json
import re
import traceback
import pandas as pd
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from config.llm_config import llm

# Prompt template
template = """
You are a data cleaning assistant.

Return ONLY a valid JSON object with two keys:
"cleaning_steps" and "transformations".

Choose only from these options:

cleaning_steps:
- drop_rows_with_null
- remove_duplicates
- strip_whitespace
- fill_null_with_zero

transformations:
- normalize_quantity_sold
- convert_dates

Input:
Dataset info: {dataset_info}
Columns: {columns}
Sample rows: {sample_data}

Respond ONLY with a valid JSON object. Do NOT include any text, explanation, or formatting.

Example:
{{
  "cleaning_steps": ["drop_rows_with_null"],
  "transformations": ["normalize_quantity_sold"]
}}
"""

prompt = PromptTemplate(template=template, input_variables=["dataset_info", "columns", "sample_data"])
data_manipulation_chain = LLMChain(prompt=prompt, llm=llm) if llm else None

class DataManipulationAgent:
    def extract_json(self, text):
        try:
            print("Raw LLM output before JSON extraction:\n", text)

            # Remove markdown formatting and fix quotes
            text = text.strip().replace("```json", "").replace("```", "")
            text = text.replace("“", "\"").replace("”", "\"")

            # Extract JSON using regex
            start = text.find('{')
            end = text.find('}')
            if start !=-1 and end !=-1 and end>start:
                json_str=text[start:end+1].strip() 
            #match = re.search(r'\{(?:[^{}]|(?R))*\}', text, re.DOTALL)
            #if match:
                #json_str = match.group(0).strip()

                # Handle if JSON is returned as a string
                if json_str.startswith('"') and json_str.endswith('"'):
                    json_str = json_str[1:-1].replace('\\"', '"')

                print("Extracted JSON string:\n", json_str)
                parsed = json.loads(json_str)

                if "cleaning_steps" in parsed and "transformations" in parsed:
                    return parsed
                else:
                    print("Missing required keys in extracted JSON.")
            else:
                print("No JSON object found in LLM response.")
        except Exception as e:
            print("JSON extraction failed:", e)
        return None

    def apply_cleaning_steps(self, df, steps):
        for step in steps:
            if step == "drop_rows_with_null":
                df = df.dropna()
            elif step == "remove_duplicates":
                df = df.drop_duplicates()
            elif step == "strip_whitespace":
                df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            elif step == "fill_null_with_zero":
                df = df.fillna(0)
        return df

    def apply_transformations(self, df, transformations):
        for transform in transformations:
            if transform == "normalize_quantity_sold" and "quantity_sold" in df.columns:
                min_val = df["quantity_sold"].min()
                max_val = df["quantity_sold"].max()
                if max_val != min_val:
                    df["quantity_sold"] = (df["quantity_sold"] - min_val) / (max_val - min_val)
            elif transform == "convert_dates":
                for col in df.columns:
                    if "date" in col.lower():
                        df[col] = pd.to_datetime(df[col], errors='coerce')
        return df

    def process_data(self, input_path, output_path=os.path.join("backend", "data", "processed", "processed_demand.csv")):
        try:
            if not input_path:
                input_path = os.path.join("backend", "data", "datasets", "market_demand.csv")

            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if not os.path.isabs(input_path):
                input_path = os.path.abspath(os.path.join(project_root, input_path))

            output_path = os.path.abspath(output_path)

            print("Looking for file at:", input_path)
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")

            df = pd.read_csv(input_path)

            dataset_info = f"Dataset from {input_path}, shape: {df.shape}"
            columns = df.columns.tolist()
            sample_data = df.head(1).to_dict(orient="records")  # Limit to 1 row for prompt brevity

            if data_manipulation_chain:
                try:
                    response = data_manipulation_chain.invoke({
                        "dataset_info": dataset_info,
                        "columns": columns,
                        "sample_data": sample_data
                    })
                    print("Raw LLM response:", response)
                    text = response.get("text", response) if isinstance(response, dict) else response
                    plan = self.extract_json(text)
                    if not plan:
                        raise ValueError("Invalid or missing keys in LLM response")
                except Exception as e:
                    print(f"LLM plan failed: {e}; using default plan")
                    plan = {
                        "cleaning_steps": ["drop_rows_with_null"],
                        "transformations": ["normalize_quantity_sold"]
                    }
            else:
                print("No LLM available; using default plan")
                plan = {
                    "cleaning_steps": ["drop_rows_with_null"],
                    "transformations": ["normalize_quantity_sold"]
                }

            df = self.apply_cleaning_steps(df, plan.get("cleaning_steps", []))
            df = self.apply_transformations(df, plan.get("transformations", []))

            if "features" in df.columns:
                df["features"] = df["features"].astype(str).str.split(",").apply(
                    lambda x: ",".join(x[:5]) if isinstance(x, list) else x
                )

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            df.to_csv(output_path, index=False)
            print(f"Saved to {output_path}")
            return df

        except Exception as e:
            print("Error processing data:")
            print(traceback.format_exc())
            return None
