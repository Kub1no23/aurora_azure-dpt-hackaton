# app.py
import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from difflib import get_close_matches

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

# --- Konfigurace (pozdeji sem budeš moci vložit Azure proměnné) ---
AZ_FOUNDARY_ENABLED = False  # <-- přepni na True až budeš mít Foundry
# AZ_FOUNDARY_ENDPOINT = os.environ.get("AZ_FOUNDARY_ENDPOINT")
# AZ_FOUNDARY_APIKEY = os.environ.get("AZ_FOUNDARY_APIKEY")
# MODEL_DEPLOYMENT = os.environ.get("AZ_FOUNDARY_DEPLOYMENT", "gpt-like-model")

# --- Lokální FAQ (rychlé zodpovězení bez volání modelu) ---
FAQ = {
    "otevírací doba": "Otevírací doba je Po–Pá 8:00–17:00.",
    "oteviraci doba": "Otevírací doba je Po–Pá 8:00–17:00.",
    "vrácení zboží": "Zboží lze vrátit do 14 dnů s účtenkou.",
    "vraceni zbozi": "Zboží lze vrátit do 14 dnů s účtenkou.",
    "kontakt": "Napište na email podpora@firma.cz nebo volejte 123 456 789.",
    "doprava": "Doprava trvá 2–5 pracovních dnů. Expresní doručení je možné za příplatek.",
}

FAQ_KEYS = list(FAQ.keys())

# --- Simple "simulated AI" fallback (heuristics) ---
def simulated_ai_response(user_msg: str) -> str:
    # 1) přesná odpověď z FAQ (already checked outside)
    # 2) nejbližší shoda přes difflib
    lower = user_msg.lower()
    matches = get_close_matches(lower, FAQ_KEYS, n=1, cutoff=0.5)
    if matches:
        k = matches[0]
        return FAQ[k] + " (poznámka: odpověď z lokální FAQ simulace)."

    # 3) jednoduchá generická odpověď podle klíčových slov
    if any(w in lower for w in ["otevř", "otevir", "kdy ote"]) :
        return "Otevírací doba je Po–Pá 8:00–17:00. Pokud chceš konkrétní pobočku, napiš její jméno."
    if any(w in lower for w in ["vrác", "vraceni", "vratit"]):
        return "Zboží je možné vrátit do 14 dnů s dokladem a nenarušeným obalem."
    if any(w in lower for w in ["kontakt", "telefon", "email", "kontaktujte"]):
        return "Kontakt: podpora@firma.cz, tel. 123 456 789. Pracovní doba podpory 8:00–17:00."
    if "cena" in lower or "kolik" in lower:
        return "Cenu najdeš na stránce produktu — pošli mi odkaz nebo název produktu a zkusím poradit."

    # 4) fallback "ukázková odpověď" (nevolá Azure)
    return (
        "Tohle je ukázková (mock) odpověď — ještě nemám připojení k Azure. "
        "Až připojíš Foundry, tento endpoint bude volat model, který vygeneruje reálnější odpovědi."
    )

# --- API endpoint pro chat ---
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "No message"}), 400

    # 1) lokální FAQ exact match (rychlé)
    key_lower = user_message.lower()
    for k, v in FAQ.items():
        if k in key_lower:
            return jsonify({"answer": v, "source": "faq_local"})

    # 2) Pokud bys chtěl později zapnout Foundry, tady je návrh (zatím neaktivní)
    if AZ_FOUNDARY_ENABLED:
        # *TADY by šel volat Azure Foundry (odkomentuj, nakonfiguruj a používej bezpečně)*
        # resp = call_foundry_chat([...])
        # return jsonify({...})
        pass

    # 3) fallback: simulated AI
    answer = simulated_ai_response(user_message)
    return jsonify({"answer": answer, "source": "mock_ai"})

# --- Serve statické frontend soubory ---
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/guide")
def guide():
    return send_from_directory("static", "guide.html")

@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory("static", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
