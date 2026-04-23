from io import StringIO
from datetime import datetime
import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from utils.data_contract import DataContract
from utils.drive_upload import DRIVE_FOLDER_ID, DriveUploadError, upload_to_drive

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

    # Generate unique file names per request so every upload is a new Drive file.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    source_stem = Path(file.filename).stem or "uploaded_data"
    safe_stem = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in source_stem)
    csv_name = f"{safe_stem}_{timestamp}.csv"
    json_name = f"{safe_stem}_{timestamp}_output.json"

    with open(csv_name, "wb") as f:
        f.write(raw_bytes)

    with open(json_name, "w", encoding="utf-8") as f:
        json.dump(output_data, f)

    csv_id = None
    json_id = None
    upload_error = None

    try:
        csv_id = upload_to_drive(csv_name, csv_name)
        json_id = upload_to_drive(json_name, json_name)
    except (DriveUploadError, Exception) as exc:
        # Do not fail data processing if Drive upload is unavailable.
        upload_error = str(exc)
        print("Drive upload failed:", upload_error)

    return {
        "message": "Data processed",
        "drive_folder_id": DRIVE_FOLDER_ID,
        "uploaded_file_names": {
            "csv": csv_name,
            "json": json_name,
        },
        "drive_file_ids": {
            "csv": csv_id,
            "json": json_id,
        },
        "drive_file_links": {
            "csv": f"https://drive.google.com/file/d/{csv_id}/view" if csv_id else None,
            "json": f"https://drive.google.com/file/d/{json_id}/view" if json_id else None,
        },
        "upload_error": upload_error,
    }
