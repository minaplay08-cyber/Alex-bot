from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import asyncio
import threading

app = Flask(__name__, static_folder='webapp', static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*"}})

DATA_FILE = "user_data.json"


def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"users": {}, "conversation_history": {}, "memory": {}}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    return send_from_directory('webapp', 'index.html')

@app.route("/app")
def app_page():
    return send_from_directory('webapp', 'index.html')


@app.route("/api/profile/<user_id>", methods=["GET"])
def get_profile(user_id):
    data = load_data()
    uid = str(user_id)
    
    if uid not in data["users"]:
        return jsonify({
            "name": None,
            "persona": None,
            "color": "#DC143C",
            "chat_mode": "romantic"
        })
    
    user = data["users"][uid]
    return jsonify({
        "name": user.get("name"),
        "persona": user.get("interests"),
        "color": user.get("color", "#DC143C"),
        "chat_mode": user.get("chat_mode", "romantic")
    })


@app.route("/api/profile/<user_id>", methods=["POST"])
def save_profile(user_id):
    data = load_data()
    uid = str(user_id)
    
    if uid not in data["users"]:
        data["users"][uid] = {
            "name": None,
            "gender": None,
            "appearance": None,
            "interests": None,
            "reminders_enabled": False,
            "dark_mode": False,
            "last_reminder": {},
            "color": "#DC143C",
            "chat_mode": "romantic"
        }
    
    profile = request.json
    
    if "name" in profile:
        data["users"][uid]["name"] = profile["name"]
    if "persona" in profile:
        data["users"][uid]["interests"] = profile["persona"]
    if "color" in profile:
        data["users"][uid]["color"] = profile["color"]
    if "chat_mode" in profile:
        data["users"][uid]["chat_mode"] = profile["chat_mode"]
        data["users"][uid]["dark_mode"] = profile["chat_mode"] == "mysterious"
    
    save_data(data)
    
    return jsonify({"success": True, "message": "Профиль сохранён!"})


def run_bot():
    import sys
    import main as bot_module
    asyncio.run(bot_module.main())


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "bot":
        run_bot()
    else:
        from dotenv import load_dotenv
        load_dotenv()
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        app.run(host="0.0.0.0", port=8080)
