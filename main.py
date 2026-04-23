import nest_asyncio
nest_asyncio.apply()

import asyncio
import logging
from flask import Flask, request, jsonify, send_from_directory
from aiogram import Bot, Dispatcher, types
from models import init_db, SessionLocal
from bot import router
from config import BOT_TOKEN, WEBAPP_URL

logging.basicConfig(level=logging.INFO)
init_db()

app = Flask(__name__, static_folder='webapp/static', static_url_path='/static')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)


ALLOWED_UPDATES = ["message", "callback_query", "my_chat_member", "chat_member"]


def _set_webhook():
    wh_url = f"{WEBAPP_URL}/webhook"
    try:
        asyncio.run(bot.set_webhook(url=wh_url, allowed_updates=ALLOWED_UPDATES))
        logging.info(f"Webhook set to {wh_url}")
    except Exception as e:
        logging.warning(f"Webhook setup error: {e}")


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = types.Update.model_validate(data)
    asyncio.run(dp.feed_update(bot, update))
    return "OK", 200


@app.route("/")
def index():
    return send_from_directory("webapp", "index.html")


@app.route("/app.html")
def app_page():
    return send_from_directory("webapp", "app.html")


@app.route("/api/tournament", methods=["GET"])
def api_active_tournament():
    db = SessionLocal()
    from tournament import get_active_tournament
    t = get_active_tournament(db)
    if not t:
        return jsonify({"exists": False})
    return jsonify({
        "exists": True,
        "id": t.id,
        "name": t.name,
        "status": t.status.value,
        "max_participants": t.max_participants,
        "participants_count": len(t.participants)
    })


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(force=True)
    user_id = data.get("user_id")
    username = data.get("username")
    game_nickname = data.get("game_nickname")
    if not all([user_id, game_nickname]):
        return jsonify({"success": False, "error": "Missing data"})
    db = SessionLocal()
    from tournament import register_participant, get_active_tournament
    t = get_active_tournament(db)
    if not t or t.status.value != "registration":
        return jsonify({"success": False, "error": "No active registration"})
    p = register_participant(db, t.id, int(user_id), username or "", game_nickname)
    if p:
        return jsonify({"success": True, "participant_id": p.id})
    return jsonify({"success": False, "error": "Already registered or tournament full"})


@app.route("/api/standings", methods=["GET"])
def api_standings():
    db = SessionLocal()
    from tournament import get_active_tournament, get_all_standings
    t = get_active_tournament(db)
    if not t:
        return jsonify({"exists": False})
    data = get_all_standings(db, t.id)
    return jsonify({"exists": True, "tournament_name": t.name, "groups": data})


@app.route("/api/my_matches", methods=["GET"])
def api_my_matches():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"})
    db = SessionLocal()
    from tournament import get_active_tournament, get_user_matches
    t = get_active_tournament(db)
    if not t:
        return jsonify({"exists": False})
    data = get_user_matches(db, t.id, int(user_id))
    return jsonify({"exists": True, "matches": data})


@app.route("/api/remaining", methods=["GET"])
def api_remaining():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"})
    db = SessionLocal()
    from tournament import get_active_tournament, get_remaining_matches_for_user
    t = get_active_tournament(db)
    if not t:
        return jsonify({"exists": False})
    data = get_remaining_matches_for_user(db, t.id, int(user_id))
    return jsonify({"exists": True, "matches": data})


@app.route("/api/submit_result", methods=["POST"])
def api_submit_result():
    data = request.get_json(force=True)
    match_id = data.get("match_id")
    p1_score = data.get("player1_score")
    p2_score = data.get("player2_score")
    if not all([match_id, p1_score is not None, p2_score is not None]):
        return jsonify({"success": False, "error": "Missing data"})
    db = SessionLocal()
    from tournament import submit_match_result
    m = submit_match_result(db, int(match_id), int(p1_score), int(p2_score))
    if m:
        return jsonify({"success": True, "match_id": m.id, "winner_id": m.winner_id})
    return jsonify({"success": False, "error": "Invalid match or draw"})


if __name__ == "__main__":
    _set_webhook()
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

