# google_ads_connector.py

import json
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def connect_google_ads():
    """
    Connette SpyAds Pro all'API di Google Ads usando le credenziali OAuth scaricate.
    """
    try:
        client = GoogleAdsClient.load_from_storage("google-ads.yaml")
        print("✅ Connessione Google Ads API riuscita!")
        return client
    except GoogleAdsException as e:
        print("❌ Errore nella connessione a Google Ads API:", e)
        return None