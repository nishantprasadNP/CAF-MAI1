import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Keep tests offline and deterministic.
import app.utils.gemini_client as gemini_client  # noqa: E402

gemini_client._CLIENT = None


@pytest.fixture
def biased_df() -> pd.DataFrame:
    """Binary target where sex=M is favoured independent of income."""
    rng = np.random.default_rng(0)
    n = 400
    sex = rng.choice(["M", "F"], n)
    income = rng.normal(50, 10, n).round(1)
    score = income + (sex == "M") * 10 + rng.normal(0, 5, n)
    return pd.DataFrame({"sex": sex, "income": income, "approved": np.where(score > 57, "yes", "no")})


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)


def upload(client, df: pd.DataFrame, session: str = "test"):
    return client.post(
        "/upload",
        files={"file": ("data.csv", df.to_csv(index=False).encode(), "text/csv")},
        headers={"X-Session-ID": session},
    )
