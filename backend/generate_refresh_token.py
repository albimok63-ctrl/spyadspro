import sys
from google_auth_oauthlib.flow import InstalledAppFlow

def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        "google_ads_credentials.json",
        scopes=["https://www.googleapis.com/auth/adwords"]
    )
    creds = flow.run_local_server(port=8080)
    print("\n✅ REFRESH TOKEN GENERATO CON SUCCESSO!\n")
    print(f"refresh_token: {creds.refresh_token}")

if __name__ == "__main__":
    main()