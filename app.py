import os
import requests
from flask import Flask, redirect, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from google_auth_oauthlib.flow import Flow
from datetime import date, timedelta

app = Flask(__name__)

CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "https://aura-pp1o.onrender.com/callback"
SCOPES = [
    "https://www.googleapis.com/auth/fitness.sleep.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
    "https://www.googleapis.com/auth/fitness.activity.read",
]

tokens_store = {}

def get_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

def get_credentials():
    if "user" not in tokens_store:
        return None
    t = tokens_store["user"]
    creds = Credentials(
        token=t["token"],
        refresh_token=t["refresh_token"],
        token_uri=t["token_uri"],
        client_id=t["client_id"],
        client_secret=t["client_secret"],
        scopes=t["scopes"],
    )
    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        tokens_store["user"]["token"] = creds.token
    return creds

@app.route("/")
def index():
    return "Aura Fitness API funcionando ✅"

@app.route("/auth")
def auth():
    flow = get_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    return redirect(auth_url)

@app.route("/callback")
def callback():
    flow = get_flow()
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    tokens_store["user"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes),
    }
    return "✅ Autenticación completada. Ya puedes cerrar esta ventana y usar Aura."

@app.route("/sleep")
def get_sleep():
    creds = get_credentials()
    if not creds:
        return jsonify({"error": "No autenticado. Ve a /auth primero"}), 401

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    today = date.today().isoformat()

    headers = {"Authorization": f"Bearer {creds.token}"}
    url = (
        f"https://www.googleapis.com/fitness/v1/users/me/sessions"
        f"?startTime={yesterday}T00:00:00Z&endTime={today}T23:59:59Z&activityType=72"
    )

    resp = requests.get(url, headers=headers)
    data = resp.json()
    sessions = data.get("session", [])

    if not sessions:
        return jsonify({"message": "No se encontraron datos de sueño para anoche", "date": yesterday})

    total_ms = sum(
        int(s.get("endTimeMillis", 0)) - int(s.get("startTimeMillis", 0))
        for s in sessions
    )
    total_hours = round(total_ms / 3600000, 1)

    return jsonify({
        "date": yesterday,
        "total_sleep_hours": total_hours,
        "sessions": len(sessions),
    })

@app.route("/heart")
def get_heart():
    creds = get_credentials()
    if not creds:
        return jsonify({"error": "No autenticado. Ve a /auth primero"}), 401

    yesterday = (date.today() - timedelta(days=1)).isoformat()

    headers = {"Authorization": f"Bearer {creds.token}"}
    url = (
        f"https://www.googleapis.com/fitness/v1/users/me/dataSources/"
        f"derived:com.google.heart_rate.bpm:com.google.android.gms:resting_heart_rate<-merge_heart_rate_bpm"
        f"/datasets/{yesterday}T00:00:00Z--{yesterday}T23:59:59Z"
    )

    resp = requests.get(url, headers=headers)
    data = resp.json()
    points = data.get("point", [])

    if not points:
        return jsonify({"message": "No hay datos de frecuencia cardíaca en reposo", "date": yesterday})

    rhr = points[-1]["value"][0]["fpVal"]
    return jsonify({
        "date": yesterday,
        "resting_heart_rate": round(rhr, 1)
    })

@app.route("/summary")
def get_summary():
    creds = get_credentials()
    if not creds:
        return jsonify({"error": "No autenticado. Ve a /auth primero"}), 401

    sleep_resp = get_sleep()
    heart_resp = get_heart()

    return jsonify({
        "sleep": sleep_resp.get_json(),
        "heart_rate": heart_resp.get_json()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
