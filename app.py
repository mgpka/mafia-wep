import json
import os
import random
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DATA_FILE = "game_state.json"

DEFAULT_CARDS = [
    {
        "id": 1,
        "name": "القنبلة",
        "desc": "أنت المافيا.. أزرعها عند ضحيتك بالسر.",
        "img": "card1.jpg",
    },
    {
        "id": 2,
        "name": "العكس (ريفيرس)",
        "desc": "تنعكس القنبلة على المافيا الذي زرعها عندك ليموت هو.",
        "img": "card2.jpg",
    },
    {
        "id": 3,
        "name": "السترة الواقية",
        "desc": "إذا زرعوا القنبلة عندك، تُلفى الجولة بالكامل وتنجو.",
        "img": "card3.jpg",
    },
    {
        "id": 4,
        "name": "مصل الحقيقة",
        "desc": "تُجبر المشتبه به في التحقيق على قول الحقيقة.",
        "img": "card4.jpg",
    },
    {
        "id": 5,
        "name": "فرصة ثانية",
        "desc": "إذا خرجت من اللعبة، تعود في الجولة القادمة.",
        "img": "card5.jpg",
    },
    {
        "id": 6,
        "name": "التنصت والمراقبة",
        "desc": "اسأل الحكم عن شخصين لتعرف إذا أحدهما مافيا.",
        "img": "card6.jpg",
    },
    {
        "id": 7,
        "name": "الاتهام المزدوج",
        "desc": "اتهم شخصين بدل شخص واحد لزيادة فرصة النجاة.",
        "img": "card7.jpg",
    },
    {
        "id": 8,
        "name": "العرّاب (الملك)",
        "desc": "اسأل الحكم عن أي شخص ليعطيك حقيقته الكاملة.",
        "img": "card8.jpg",
    },
    {
        "id": 9,
        "name": "كبش الفداء",
        "desc": "إذا اختاروك للتحقيق، أرسل شخصاً آخر بدلاً منك.",
        "img": "card9.jpg",
    },
    {
        "id": 10,
        "name": "فضح المستور",
        "desc": "اجبر شخصاً في التحقيق على إظهار كرت قدرته.",
        "img": "card10.jpg",
    },
]


def load_game_state():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    cards_catalog = [dict(c) for c in DEFAULT_CARDS]
    card_ids = list(range(1, 11))
    random.shuffle(card_ids)

    players = []
    for i in range(1, 11):
        players.append(
            {
                "seat": i,
                "name": f"اللاعب {i}",
                "pin": f"{1000 + i}",
                "card_id": card_ids[i - 1],
                "is_active": True,
            }
        )

    state = {"cards": cards_catalog, "players": players}
    save_game_state(state)
    return state


def save_game_state(state):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/game-info", methods=["GET"])
def game_info():
    state = load_game_state()
    public_players = [
        {"seat": p["seat"], "name": p["name"], "is_active": p.get("is_active", True)}
        for p in state["players"]
    ]
    return jsonify({"players": public_players})


@app.route("/api/open-box", methods=["POST"])
def open_box():
    data = request.get_json() or {}
    try:
        seat = int(data.get("seat"))
        pin = str(data.get("pin", "")).strip()
    except Exception:
        return jsonify({"status": "error", "message": "بيانات غير صالحة"}), 400

    state = load_game_state()
    player = next((p for p in state["players"] if p["seat"] == seat), None)

    if not player:
        return jsonify({"status": "error", "message": "المقعد غير موجود"}), 404

    if not player.get("is_active", True):
        return (
            jsonify({"status": "error", "message": "تم استبعادك من اللعبة!"}),
            403,
        )

    if str(player["pin"]).strip() != pin:
        return (
            jsonify(
                {"status": "error", "message": "الرمز السري (PIN) غير صحيح!"}
            ),
            401,
        )

    card = next(
        (c for c in state["cards"] if c["id"] == player["card_id"]),
        state["cards"][0],
    )
    return jsonify(
        {
            "status": "success",
            "player_name": player["name"],
            "seat": player["seat"],
            "card": card,
        }
    )


@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if email == "alinael2018fa@gmail.com" and password == "alinael2018qwer":
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "بيانات الدخول خاطئة"}), 401


@app.route("/api/admin/data", methods=["GET"])
def admin_data():
    return jsonify(load_game_state())


@app.route("/api/admin/player/toggle", methods=["POST"])
def admin_toggle_player():
    data = request.get_json() or {}
    seat = data.get("seat")
    state = load_game_state()
    for p in state["players"]:
        if p["seat"] == seat:
            p["is_active"] = not p.get("is_active", True)
            break
    save_game_state(state)
    return jsonify({"status": "success"})


@app.route("/api/admin/player/pin", methods=["POST"])
def admin_update_pin():
    data = request.get_json() or {}
    seat = data.get("seat")
    new_pin = str(data.get("pin", "")).strip()
    if not new_pin:
        return jsonify({"status": "error", "message": "الرمز فارغ"}), 400

    state = load_game_state()
    for p in state["players"]:
        if p["seat"] == seat:
            p["pin"] = new_pin
            break
    save_game_state(state)
    return jsonify({"status": "success"})


@app.route("/api/admin/card/text", methods=["POST"])
def admin_update_card_text():
    data = request.get_json() or {}
    card_id = int(data.get("card_id"))
    new_name = str(data.get("name", "")).strip()
    new_desc = str(data.get("desc", "")).strip()

    state = load_game_state()
    for c in state["cards"]:
        if c["id"] == card_id:
            if new_name:
                c["name"] = new_name
            if new_desc:
                c["desc"] = new_desc
            break
    save_game_state(state)
    return jsonify({"status": "success"})


@app.route("/api/admin/reroll-bomb", methods=["POST"])
def admin_reroll_bomb():
    state = load_game_state()
    active_players = [p for p in state["players"] if p.get("is_active", True)]
    if len(active_players) < 2:
        return (
            jsonify({"status": "error", "message": "اللاعبين غير كافيين"}),
            400,
        )

    current_bomber = next(
        (p for p in active_players if p["card_id"] == 1), None
    )
    candidates = [p for p in active_players if p != current_bomber]
    new_bomber = random.choice(candidates)

    if current_bomber:
        current_bomber["card_id"] = new_bomber["card_id"]
        new_bomber["card_id"] = 1
    else:
        new_bomber["card_id"] = 1

    save_game_state(state)
    return jsonify(
        {
            "status": "success",
            "message": f"تم نقل القنبلة إلى المقعد رقم ({new_bomber['seat']})",
        }
    )


@app.route("/api/admin/shuffle-all", methods=["POST"])
def admin_shuffle_all():
    state = load_game_state()
    active_players = [p for p in state["players"] if p.get("is_active", True)]
    card_ids = [c["id"] for c in state["cards"][: len(active_players)]]
    random.shuffle(card_ids)

    for i, p in enumerate(active_players):
        p["card_id"] = card_ids[i]

    save_game_state(state)
    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
