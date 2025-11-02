# app.py
import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
from difflib import get_close_matches
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message    

load_dotenv()  # Load environment variables first


# Create Flask app
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key')  # Add a secret key
app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_SERVER')}/{os.getenv('DB_NAME')}?driver=ODBC+Driver+17+for+SQL+Server"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)
ts = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# User model
class User(db.Model):
    __tablename__ = 'Users'
    user_id = db.Column('user_id', db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    passwd_hash = db.Column(db.String(255), nullable=False)
    last_login = db.Column(db.DateTime)
    language = db.Column(db.String(50))
    login_location = db.Column(db.String(255))
    email_verified = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        """Set hashed password"""
        self.passwd_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.passwd_hash, password)

# Email verification helper functions
def generate_verification_token(email):
    """Generate a time-limited verification token for email confirmation."""
    return ts.dumps(email, salt='email-verify-key')

def verify_token(token, expiration=3600):
    """Verify the email confirmation token."""
    try:
        email = ts.loads(token, salt='email-verify-key', max_age=expiration)
        return email
    except:
        return None

# Email sending function
def send_verification_email(user):
    """send verification email to user"""
    token = generate_verification_token(user.email)
    verify_url = url_for('verify_email', token=token, _external=True)
    subject = "Please verify your email"
    html = f"""
    <h1>Welcome!</h1>
    <p>Thanks for signing up! To verify your email address, please click on the link below:</p>
    <p><a href="{verify_url}">{verify_url}</a></p>
    <p>This link will expire in 1 hour.</p>
    """
    msg = Message(subject, recipients=[user.email], html=html)
    mail.send(msg)

#verification endpoint
@app.route('/api/auth/verify/<token>', methods=['GET'])
def verify_email(token):
    try:
        email = verify_token(token)
        if not email:
            return jsonify({"error": "Invalid or expired token"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if user.email_verified:
            return jsonify({"message": "Email already verified"}), 200
        
        user.email_verified = True
        db.session.commit()
        return jsonify({"message": "Email verified successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Verification failed", 'error': str(e)}), 500



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
# Registration endpoint
@app.route('/api/auth/register', methods=['POST'])
    

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