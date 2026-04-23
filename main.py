from io import StringIO
import json

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from utils.data_contract import DataContract
from utils.drive_upload import DriveUploadError, upload_to_drive

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/process-data")
async def process_data(
    file: UploadFile = File(...),
    target_column: str = Form(...),
    bias_columns: str = Form(...),
) -> dict:
    print("==== REQUEST RECEIVED ====")
    print("Target Column:", target_column)
    print("Bias Columns (raw):", bias_columns)

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    try:
        raw_bytes = await file.read()
        csv_text = raw_bytes.decode("utf-8")
        df = pd.read_csv(StringIO(csv_text))
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded.") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {exc}") from exc

    if df.shape[1] == 0:
        raise HTTPException(status_code=400, detail="CSV has no columns.")

    print("Data shape:", df.shape)
    print("Columns:", df.columns.tolist())

    try:
        bias_list = json.loads(bias_columns)
        print("Parsed Bias Columns:", bias_list)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="bias_columns must be a valid JSON array.") from exc

    if not isinstance(bias_list, list):
        raise HTTPException(status_code=400, detail="bias_columns must be a JSON array.")

    try:
        contract = DataContract(
            df=df,
            target_column=target_column,
            bias_columns=bias_list,
        )
        data = contract.get_data()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    x_preview = data["X"].head(5).where(pd.notna(data["X"].head(5)), None).to_dict(orient="records")
    y_preview = data["Y"].head(5).where(pd.notna(data["Y"].head(5)), None).tolist()

    output_data = {
        "X": x_preview,
        "Y": y_preview,
        "B_user": list(data.get("B_user", [])),
        "B_suggested": list(data.get("B_suggested", [])),
        "B_hidden": list(data.get("B_hidden", [])),
        "metadata": {
            "column_types": dict(data.get("metadata", {}).get("column_types", {})),
            "target_type": str(data.get("metadata", {}).get("target_type", "")),
        },
    }

    with open("temp_data.csv", "wb") as f:
        f.write(raw_bytes)

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f)

    try:
        csv_id = upload_to_drive("temp_data.csv", "temp_data.csv")
        json_id = upload_to_drive("output.json", "output.json")
    except DriveUploadError as exc:
        raise HTTPException(status_code=500, detail=f"Drive upload failed: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Drive upload failed: {exc}") from exc

    return {
        "message": "Files uploaded to Drive",
        "drive_file_ids": {
            "csv": csv_id,
            "json": json_id,
        },
    }
