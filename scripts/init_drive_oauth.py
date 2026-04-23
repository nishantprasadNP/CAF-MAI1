from __future__ import annotations

import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]
OAUTH_CLIENT_FILE = Path(
    os.getenv("GOOGLE_OAUTH_CLIENT_FILE", "googledriveapi_key/oauth_client.json")
)
OAUTH_TOKEN_FILE = Path(
    os.getenv("GOOGLE_OAUTH_TOKEN_FILE", "googledriveapi_key/oauth_token.json")
)
OAUTH_LOCAL_PORT = int(os.getenv("GOOGLE_OAUTH_LOCAL_PORT", "8000"))


def main() -> None:
    if not OAUTH_CLIENT_FILE.exists():
        raise FileNotFoundError(
            f"OAuth client config not found at {OAUTH_CLIENT_FILE}. "
            "Set GOOGLE_OAUTH_CLIENT_FILE or place oauth_client.json at this path."
        )

    # Your oauth_client.json currently allows localhost:8000 redirect.
    flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_CLIENT_FILE), SCOPES)
    credentials = flow.run_local_server(
        port=OAUTH_LOCAL_PORT,
        open_browser=True,
        redirect_uri_trailing_slash=False,
    )

    OAUTH_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    OAUTH_TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    print(f"OAuth token saved to: {OAUTH_TOKEN_FILE}")


if __name__ == "__main__":
    main()
