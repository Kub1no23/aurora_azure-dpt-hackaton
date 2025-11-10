# app.py
import os
import json
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from difflib import get_close_matches

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

# --- načti .env (pokud existuje) a proměnné prostředí ---
# Najde .env vedle tohoto souboru (backend/.env) při vývoji.
BASE_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- Konfigurace pro případné připojení k Azure Foundry / Azure OpenAI ---
def _str2bool(v: str) -> bool:
    return str(v).lower() in ("1", "true", "yes", "on")

# Přečti z prostředí (můžeš je doplnit později do backend/.env nebo do Azure App Settings)
AZ_FOUNDARY_ENABLED = _str2bool(os.environ.get("AZ_FOUNDARY_ENABLED", "False"))
print(f"AZ_FOUNDARY_ENABLED={AZ_FOUNDARY_ENABLED}")
AZ_FOUNDARY_ENDPOINT = os.environ.get("AZ_FOUNDARY_ENDPOINT")
print(f"AZ_FOUNDARY_ENDPOINT={AZ_FOUNDARY_ENDPOINT}")
AZ_FOUNDARY_APIKEY = os.environ.get("AZ_FOUNDARY_APIKEY")
print(f"AZ_FOUNDARY_APIKEY={AZ_FOUNDARY_APIKEY}")
MODEL_DEPLOYMENT = os.environ.get("AZ_FOUNDARY_DEPLOYMENT", "gpt-like-model")
print(f"MODEL_DEPLOYMENT={MODEL_DEPLOYMENT}")

# Poznámka: konkrétní tvar HTTP volání závisí na tom, jak Foundry/endpoint přijímá požadavky.
# Implementace níže je připravená pro běžný Azure OpenAI-style endpoint, ale je robustní
# a pokusí se pracovat i s jednoduchým REST endpointem (pokud vrátí JSON se "answer" nebo "text").

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


def call_foundry_chat(user_msg: str) -> str:
    """Volání Azure Foundry / Azure OpenAI (připraveno, ale záleží na konfiguraci).

    - Čte AZ_FOUNDARY_ENDPOINT, AZ_FOUNDARY_APIKEY a MODEL_DEPLOYMENT z env.
    - Pokusí se zavolat Azure OpenAI chat completion endpoint pokud je to relevantní,
      jinak pošle jednoduchý POST request na zadané endpoint a pokusí se najít odpověď
      v poli `choices[0].message.content` nebo v `answer`/`text`.
    - Vrací textovou odpověď nebo zvedne výjimku při chybě.
    """
    if not AZ_FOUNDARY_ENDPOINT or not AZ_FOUNDARY_APIKEY:
        raise RuntimeError("AZ_FOUNDARY_ENDPOINT nebo AZ_FOUNDARY_APIKEY nejsou nastaveny")

    # Helpr pro hlavičky — Azure často používá header 'api-key'
    headers = {
        "Content-Type": "application/json",
    }
    if AZ_FOUNDARY_APIKEY.startswith("sk-"):
        headers["Authorization"] = f"Bearer {AZ_FOUNDARY_APIKEY}"
    else:
        headers["api-key"] = AZ_FOUNDARY_APIKEY

    # Pokud máme model deployment, zkusíme zavolat Azure OpenAI-compatibilní endpoint
    try:
        if MODEL_DEPLOYMENT and "/openai/" not in AZ_FOUNDARY_ENDPOINT:
            url = AZ_FOUNDARY_ENDPOINT.rstrip("/") + f"/openai/deployments/{MODEL_DEPLOYMENT}/chat/completions?api-version=2023-05-15"
            payload = {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_msg},
                ],
                "max_tokens": 512,
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
        else:
            # Fallback — pošli jednoduchý POST (např. custom Foundry endpoint)
            payload = {"message": user_msg}
            resp = requests.post(AZ_FOUNDARY_ENDPOINT, headers=headers, json=payload, timeout=15)

        resp.raise_for_status()
        data = resp.json()

        # Najdi odpověď v několika možných tvarech
        # 1) Azure OpenAI: choices[0].message.content
        if isinstance(data, dict):
            if "choices" in data and data["choices"]:
                first = data["choices"][0]
                # OpenAI-style
                if isinstance(first, dict) and "message" in first and "content" in first["message"]:
                    return first["message"]["content"].strip()
                # jiné OpenAI-style: text
                if "text" in first:
                    return first["text"].strip()
            # 2) simple API: {"answer": "..."}
            for key in ("answer", "text", "response"):
                if key in data and isinstance(data[key], str):
                    return data[key].strip()

        # Pokud nic nevyšla, fallback na JSON dump
        return json.dumps(data)
    except Exception:
        # Propaguj chybu výše k volajícímu (kde se chytne a vrátí se fallback)
        raise

# --- API endpoint pro chat ---
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "No message"}), 400

    # 2) Pokud bys chtěl později zapnout Foundry, tady je návrh (zatím neaktivní)
    if AZ_FOUNDARY_ENABLED:
        print("Volám Azure Foundry...")
        try:
            resp_text = call_foundry_chat(user_message)
            return jsonify({"answer": resp_text, "source": "az_foundry"})
        except Exception as e:
            # pokud selže, vrať fallback + info o chybě
            fallback = simulated_ai_response(user_message)
            return jsonify({"answer": fallback, "source": "mock_ai", "error": str(e)}), 200

    # 3) fallback: simulated AI
    answer = simulated_ai_response(user_message)
    return jsonify({"answer": answer, "source": "mock_ai"})

# --- Serve statické frontend soubory ---
@app.route("/")
def index():
    return send_from_directory("static", "guide.html")

@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory("static", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
