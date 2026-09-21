import os
import uuid
import re
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# ─── App Setup ───────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'campusguard.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

db = SQLAlchemy(app)

# ─── Database Models ──────────────────────────────────────────────────────────

class ItemReport(db.Model):
    __tablename__ = "item_reports"

    id          = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_type = db.Column(db.String(10), nullable=False)          # "lost" | "found"
    item_name   = db.Column(db.String(120), nullable=False)
    category    = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location    = db.Column(db.String(200), nullable=False)
    date_time   = db.Column(db.String(40), nullable=False)
    contact     = db.Column(db.String(120), nullable=True)
    image_url   = db.Column(db.String(300), nullable=True)
    status      = db.Column(db.String(20), default="active")        # active | resolved
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":          self.id,
            "report_type": self.report_type,
            "item_name":   self.item_name,
            "category":    self.category,
            "description": self.description,
            "location":    self.location,
            "date_time":   self.date_time,
            "contact":     self.contact,
            "image_url":   f"/uploads/{self.image_url}" if self.image_url else None,
            "status":      self.status,
            "created_at":  self.created_at.isoformat(),
            "emoji":       CATEGORY_EMOJI.get(self.category.lower(), "📦"),
        }


class Match(db.Model):
    __tablename__ = "matches"

    id              = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lost_item_id    = db.Column(db.String(36), db.ForeignKey("item_reports.id"), nullable=False)
    found_item_id   = db.Column(db.String(36), db.ForeignKey("item_reports.id"), nullable=False)
    confidence      = db.Column(db.Float, nullable=False)           # 0.0 – 1.0
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        lost  = db.session.get(ItemReport, self.lost_item_id)
        found = db.session.get(ItemReport, self.found_item_id)
        return {
            "id":         self.id,
            "confidence": round(self.confidence * 100, 1),
            "lost_item":  lost.to_dict()  if lost  else None,
            "found_item": found.to_dict() if found else None,
            "created_at": self.created_at.isoformat(),
        }


# ─── Category & Emoji Map ─────────────────────────────────────────────────────

CATEGORY_EMOJI = {
    "phone":       "📱",
    "laptop":      "💻",
    "keys":        "🔑",
    "wallet":      "👛",
    "bag":         "🎒",
    "id card":     "🪪",
    "headphones":  "🎧",
    "bottle":      "🍶",
    "book":        "📚",
    "glasses":     "👓",
    "umbrella":    "☂️",
    "clothing":    "👕",
    "jewelry":     "💍",
    "charger":     "🔌",
    "tablet":      "📱",
    "other":       "📦",
}

KEYWORD_CATEGORY = {
    r"\bphone|mobile|iphone|android|samsung\b": "phone",
    r"\blaptop|macbook|notebook|computer\b":    "laptop",
    r"\bkey|keychain|keys\b":                   "keys",
    r"\bwallet|purse|billfold\b":               "wallet",
    r"\bbag|backpack|satchel|tote\b":           "bag",
    r"\bid card|student id|identity|card\b":    "id card",
    r"\bheadphone|earbud|airpod|headset\b":     "headphones",
    r"\bbottle|flask|tumbler\b":                "bottle",
    r"\bbook|textbook|notebook|journal\b":      "book",
    r"\bglasses|spectacles|sunglasses\b":       "glasses",
    r"\bumbrella\b":                            "umbrella",
    r"\bshirt|jacket|hoodie|coat|cloth\b":      "clothing",
    r"\bjewelry|ring|necklace|bracelet\b":      "jewelry",
    r"\bcharger|cable|adapter\b":               "charger",
    r"\btablet|ipad\b":                         "tablet",
}


def detect_category(text: str) -> str:
    """Return a category from free-text using keyword matching."""
    t = text.lower()
    for pattern, cat in KEYWORD_CATEGORY.items():
        if re.search(pattern, t):
            return cat
    return "other"


# ─── AI Matching Engine ───────────────────────────────────────────────────────

def tokenize(text: str) -> set:
    """Lower-case alphanumeric word tokens."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))

STOP_WORDS = {
    "a","an","the","is","it","was","at","in","on","of","for",
    "and","or","but","to","i","my","me","we","our","this","that",
    "have","has","had","with","its","their","which","been","be",
}

def jaccard(set_a: set, set_b: set) -> float:
    a = set_a - STOP_WORDS
    b = set_b - STOP_WORDS
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def location_score(loc_a: str, loc_b: str) -> float:
    """Partial location match – reward shared building / keyword overlap."""
    ta = tokenize(loc_a)
    tb = tokenize(loc_b)
    shared = len(ta & tb)
    if shared == 0:
        return 0.0
    return min(1.0, shared / 3)          # cap at 1.0 after 3 shared tokens


def compute_confidence(lost: ItemReport, found: ItemReport) -> float:
    """
    Weighted confidence score between 0 and 1:
      40% – description similarity (Jaccard)
      25% – item name similarity
      20% – category match (binary)
      15% – location proximity
    """
    desc_score = jaccard(tokenize(lost.description), tokenize(found.description))
    name_score = jaccard(tokenize(lost.item_name),   tokenize(found.item_name))
    cat_score  = 1.0 if lost.category.lower() == found.category.lower() else 0.0
    loc_score  = location_score(lost.location, found.location)

    confidence = (
        0.40 * desc_score +
        0.25 * name_score +
        0.20 * cat_score  +
        0.15 * loc_score
    )
    return round(min(confidence, 1.0), 4)


def run_matching(new_item: ItemReport):
    """
    Compare new_item against all active items of the opposite type.
    Store any match with confidence ≥ 0.15.
    """
    opposite = "found" if new_item.report_type == "lost" else "lost"
    candidates = ItemReport.query.filter_by(report_type=opposite, status="active").all()

    for candidate in candidates:
        if new_item.report_type == "lost":
            lost, found = new_item, candidate
        else:
            lost, found = candidate, new_item

        score = compute_confidence(lost, found)
        if score >= 0.15:
            # Avoid duplicate matches
            existing = Match.query.filter_by(
                lost_item_id=lost.id, found_item_id=found.id
            ).first()
            if not existing:
                db.session.add(Match(
                    lost_item_id=lost.id,
                    found_item_id=found.id,
                    confidence=score,
                ))
    db.session.commit()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── REST API ─────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "CampusGuard AI"})


@app.route("/api/reports", methods=["POST"])
def submit_report():
    """Submit a Lost or Found item report."""
    data        = request.form
    report_type = data.get("report_type", "").lower()
    item_name   = data.get("item_name", "").strip()
    description = data.get("description", "").strip()
    location    = data.get("location", "").strip()
    date_time   = data.get("date_time", "").strip()
    contact     = data.get("contact", "").strip()

    # Category: user-provided or auto-detected
    category = data.get("category", "").strip().lower()
    if not category or category == "auto":
        category = detect_category(f"{item_name} {description}")

    if report_type not in ("lost", "found"):
        return jsonify({"error": "report_type must be 'lost' or 'found'"}), 400
    if not item_name or not description or not location or not date_time:
        return jsonify({"error": "item_name, description, location, date_time are required"}), 400

    image_filename = None
    if "image" in request.files:
        file = request.files["image"]
        if file and file.filename and allowed_file(file.filename):
            ext = secure_filename(file.filename).rsplit(".", 1)[1].lower()
            image_filename = f"{uuid.uuid4()}.{ext}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

    item = ItemReport(
        report_type=report_type,
        item_name=item_name,
        category=category,
        description=description,
        location=location,
        date_time=date_time,
        contact=contact,
        image_url=image_filename,
    )
    db.session.add(item)
    db.session.commit()

    run_matching(item)
    return jsonify({"message": "Report submitted successfully", "item": item.to_dict()}), 201


@app.route("/api/reports", methods=["GET"])
def get_reports():
    """Fetch active item reports (optionally filter by type)."""
    report_type = request.args.get("type")
    query = ItemReport.query.filter_by(status="active")
    if report_type in ("lost", "found"):
        query = query.filter_by(report_type=report_type)
    items = query.order_by(ItemReport.created_at.desc()).all()
    return jsonify([i.to_dict() for i in items])


@app.route("/api/reports/<item_id>/resolve", methods=["PATCH"])
def resolve_report(item_id):
    item = db.session.get(ItemReport, item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    item.status = "resolved"
    db.session.commit()
    return jsonify({"message": "Item marked as resolved"})


@app.route("/api/reports/<item_id>", methods=["DELETE"])
def delete_report(item_id):
    try:
        item = db.session.get(ItemReport, item_id)
        if item is None:
            return jsonify({"error": "Item not found"}), 404
        # Remove associated matches first (foreign key references)
        Match.query.filter(
            (Match.lost_item_id == item_id) | (Match.found_item_id == item_id)
        ).delete(synchronize_session=False)
        # Remove uploaded image file if present
        if item.image_url:
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], item.image_url)
            if os.path.exists(image_path):
                os.remove(image_path)
        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True, "message": "Item deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/matches", methods=["GET"])
def get_matches():
    """Fetch all AI-generated matches, highest confidence first."""
    min_conf = float(request.args.get("min_confidence", 0))
    matches = (
        Match.query
        .join(ItemReport, Match.lost_item_id == ItemReport.id)
        .filter(Match.confidence >= min_conf / 100)
        .order_by(Match.confidence.desc())
        .all()
    )
    return jsonify([m.to_dict() for m in matches])


@app.route("/api/matches/<item_id>", methods=["GET"])
def get_matches_for_item(item_id):
    """Get matches involving a specific item."""
    matches = Match.query.filter(
        (Match.lost_item_id == item_id) | (Match.found_item_id == item_id)
    ).order_by(Match.confidence.desc()).all()
    return jsonify([m.to_dict() for m in matches])


@app.route("/api/stats", methods=["GET"])
def get_stats():
    total_lost    = ItemReport.query.filter_by(report_type="lost",  status="active").count()
    total_found   = ItemReport.query.filter_by(report_type="found", status="active").count()
    total_resolved= ItemReport.query.filter_by(status="resolved").count()
    total_matches = Match.query.count()
    return jsonify({
        "active_lost":    total_lost,
        "active_found":   total_found,
        "resolved":       total_resolved,
        "total_matches":  total_matches,
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    """Simple rule-based AI chat assistant."""
    body    = request.get_json(silent=True) or {}
    message = body.get("message", "").lower().strip()

    stats = {
        "lost":     ItemReport.query.filter_by(report_type="lost",  status="active").count(),
        "found":    ItemReport.query.filter_by(report_type="found", status="active").count(),
        "resolved": ItemReport.query.filter_by(status="resolved").count(),
    }

    if any(w in message for w in ["hello", "hi", "hey", "greet"]):
        reply = "👋 Hi there! I'm GuardBot, your campus lost & found assistant. How can I help you today?"
    elif "lost" in message and "report" in message:
        reply = "📝 To report a lost item, click the **Report Lost Item** button in the navigation. Fill in the item details and I'll search for matches automatically!"
    elif "found" in message and "report" in message:
        reply = "📝 To report a found item, click the **Report Found Item** button. Help reunite items with their owners!"
    elif "match" in message or "find" in message:
        reply = f"🤖 Our AI engine has found **{stats['found']}** items currently listed. Submit a lost report and I'll automatically compute match scores for you!"
    elif "how" in message and "work" in message:
        reply = "🧠 I use a weighted similarity algorithm combining description keywords (40%), item name (25%), category (20%), and location (15%) to compute a confidence score. Scores ≥ 70% are high confidence!"
    elif "stats" in message or "statistic" in message or "how many" in message:
        reply = f"📊 Current stats — Lost: **{stats['lost']}** | Found: **{stats['found']}** | Resolved: **{stats['resolved']}**"
    elif "contact" in message or "email" in message or "reach" in message:
        reply = "📧 You can add your contact info when submitting a report so the finder/owner can reach you directly. Check the 'Contact' field in the form."
    elif "resolve" in message or "claim" in message:
        reply = "✅ Once you've recovered your item, click the **Mark Resolved** button on your report card to close it and remove it from active listings."
    elif "thank" in message:
        reply = "😊 You're welcome! I'm always here to help. Good luck finding your item!"
    else:
        reply = "🤔 I'm not sure about that. You can ask me how the matching works, how to submit reports, or about current stats. Type **help** for a quick guide!"

    return jsonify({"reply": reply})


# ─── Static File Serving ──────────────────────────────────────────────────────

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/", defaults={"path": ""}, methods=["GET", "HEAD"])
@app.route("/<path:path>", methods=["GET", "HEAD"])
def serve_frontend(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


# ─── Entry Point ─────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
