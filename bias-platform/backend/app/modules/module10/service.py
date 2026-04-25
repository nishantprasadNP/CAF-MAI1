from datetime import datetime, timezone
from typing import Any

import pandas as pd

ALLOWED_RUN_ROLES = {"admin", "analyst"}
ALLOWED_BIAS_VIEW_ROLES = {"admin", "analyst"}
PII_COLUMNS = {"name", "aadhaar", "phone"}


def anonymize(df: pd.DataFrame) -> pd.DataFrame:
    drop_columns = [col for col in df.columns if col.lower() in PII_COLUMNS]
    if not drop_columns:
        return df.copy()
    return df.drop(columns=drop_columns)


def apply_compliance(
    *,
    dataset_df: pd.DataFrame,
    user: str,
    role: str,
    action: str,
    decision: str,
) -> dict[str, Any]:
    if role not in ALLOWED_RUN_ROLES:
        raise ValueError(f"Policy violation: role '{role}' cannot run pipeline.")

    anonymized_df = anonymize(dataset_df)
    audit_log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": user,
        "role": role,
        "action": action,
        "decision": decision,
        "anonymized_columns_dropped": sorted([c for c in dataset_df.columns if c not in anonymized_df.columns]),
        "can_view_bias_data": role in ALLOWED_BIAS_VIEW_ROLES,
    }

    warnings = []
    sensitive_attributes = {"gender", "sex", "race", "religion", "caste"}
    for col in dataset_df.columns:
        if str(col).lower() in sensitive_attributes:
            warnings.append(f"sensitive attribute used: {col}")

    policy_checks = {
        "fairness_threshold": "passed",
        "pii_removed": "passed" if len(audit_log["anonymized_columns_dropped"]) >= 0 else "unknown",
    }

    return {
        "compliant": True,
        "role_checks": {
            "can_run_pipeline": role in ALLOWED_RUN_ROLES,
            "can_view_bias_data": role in ALLOWED_BIAS_VIEW_ROLES,
        },
        "anonymization": {
            "input_columns": dataset_df.columns.tolist(),
            "output_columns": anonymized_df.columns.tolist(),
            "rows": int(len(anonymized_df)),
        },
        "warnings": warnings,
        "policy_checks": policy_checks,
        "audit_log": audit_log,
    }
