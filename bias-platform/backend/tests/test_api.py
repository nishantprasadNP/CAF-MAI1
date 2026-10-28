import pandas as pd

from conftest import upload

H = {"X-Session-ID": "test"}


def _setup(client, df, target="approved", bias=("sex",), session="test"):
    headers = {"X-Session-ID": session}
    assert upload(client, df, session).status_code == 200
    assert client.post("/init_contract", json={"target_column": target}, headers=headers).status_code == 200
    r = client.post("/select_bias", json={"bias_columns": list(bias)}, headers=headers)
    assert r.status_code == 200, r.text


def test_run_before_upload_gives_clear_error(client):
    r = client.post("/run_pipeline", headers={"X-Session-ID": "fresh"})
    assert r.status_code == 400
    assert "Upload a CSV" in r.json()["detail"]


def test_full_pipeline(client, biased_df):
    _setup(client, biased_df)
    r = client.post("/run_pipeline", json={"row_index": 3, "available_resources": 8}, headers=H)
    assert r.status_code == 200, r.text
    res = r.json()

    fairness = res["fairness"]
    assert fairness["evaluated_rows"] == 80  # 20% held-out split of 400
    assert fairness["outcome_distribution"]["actual"]
    effect = res["module6"]["debiasing_effect"]
    assert effect["after"] < effect["before"]

    decision = res["decision"]
    assert decision["row_index"] == 3
    assert decision["n_rows"] == 400
    assert decision["predicted_class"] in ("yes", "no")
    assert decision["probabilities"] != decision["original_probabilities"]
    features = [f["feature"] for f in decision["top_features"]]
    assert features, "top features should be extracted from the model"
    assert not any(f.startswith(("numeric__", "categorical__")) for f in features)
    assert 0 < decision["probabilities"][1] < 1

    assert res["monitoring"]["trend"] == "baseline"
    assert res["class_labels"] == {"0": "no", "1": "yes"}


def test_decision_endpoint_rescoring(client, biased_df):
    _setup(client, biased_df)
    client.post("/run_pipeline", headers=H)

    r = client.post("/decision", json={"row_index": 10, "available_resources": 3}, headers=H)
    assert r.status_code == 200
    assert r.json()["decision"]["row_index"] == 10
    assert client.get("/results", headers=H).json()["decision"]["row_index"] == 10

    r = client.post("/decision", json={"row_index": 400}, headers=H)
    assert r.status_code == 400


def test_rerun_tracks_bias_trend(client, biased_df):
    _setup(client, biased_df)
    client.post("/run_pipeline", headers=H)
    second = client.post("/run_pipeline", headers=H).json()
    assert second["monitoring"]["trend"] == "stable"


def test_requires_bias_column(client, biased_df):
    _setup(client, biased_df, bias=())
    r = client.post("/run_pipeline", headers=H)
    assert r.status_code == 400
    assert "bias" in r.json()["detail"]


def test_rejects_unknown_or_target_bias_columns(client, biased_df):
    _setup(client, biased_df, bias=())
    assert client.post("/select_bias", json={"bias_columns": ["nope"]}, headers=H).status_code == 400
    assert client.post("/select_bias", json={"bias_columns": ["approved"]}, headers=H).status_code == 400


def test_rejects_high_cardinality_bias_column(client, biased_df):
    _setup(client, biased_df, bias=())
    r = client.post("/select_bias", json={"bias_columns": ["income"]}, headers=H)
    assert r.status_code == 400
    assert "distinct values" in r.json()["detail"]


def test_large_dataset_trains_on_sample(client, biased_df, monkeypatch):
    import app.modules.module4.train as train

    monkeypatch.setattr(train, "MAX_TRAIN_ROWS", 100)
    _setup(client, biased_df)
    res = client.post("/run_pipeline", headers=H).json()
    assert res["model"]["train_rows"] == 100
    assert res["model"]["train_rows_available"] == 320
    assert res["fairness"]["evaluated_rows"] == 80


def test_non_binary_target_rejected(client, biased_df):
    upload(client, biased_df.assign(approved=range(len(biased_df))))
    r = client.post("/init_contract", json={"target_column": "approved"}, headers=H)
    assert r.status_code == 400
    assert "binary" in r.json()["detail"]


def test_new_upload_clears_results(client, biased_df):
    _setup(client, biased_df)
    client.post("/run_pipeline", headers=H)
    upload(client, biased_df)
    assert client.get("/results", headers=H).status_code == 404


def test_upload_suggests_binary_target(client):
    df = pd.DataFrame({
        "PassengerId": range(30), "Survived": [0, 1] * 15, "Sex": ["m", "f"] * 15,
        "Embarked": ["S", "C", "Q"] * 10,
    })
    body = upload(client, df).json()
    assert body["binary_columns"] == ["Survived", "Sex"]
    assert body["suggested_target"] == "Survived"


def test_latin1_upload(client):
    r = client.post(
        "/upload",
        files={"file": ("d.csv", "name,y\nJosé,1\n".encode("latin-1"), "text/csv")},
        headers=H,
    )
    assert r.status_code == 200
    assert r.json()["rows"] == 1


def test_sessions_are_isolated(client, biased_df):
    _setup(client, biased_df, session="a")
    upload(client, pd.DataFrame({"p": [1, 2], "q": [0, 1]}), session="b")
    r = client.post("/run_pipeline", headers={"X-Session-ID": "a"})
    assert r.status_code == 200


def test_init_contract_does_not_return_rows(client, biased_df):
    upload(client, biased_df)
    body = client.post("/init_contract", json={"target_column": "approved"}, headers=H).json()
    assert "X" not in body and "Y" not in body
    assert body["rows"] == 400


def test_cors_allows_render_frontend_only(client):
    def preflight(origin):
        return client.options(
            "/upload",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "x-session-id",
            },
        )

    ok = preflight("https://bias-platform-frontend.onrender.com")
    assert ok.status_code == 200
    assert ok.headers["access-control-allow-origin"] == "https://bias-platform-frontend.onrender.com"
    assert preflight("https://evil.example.com").status_code == 400
