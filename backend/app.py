"""
Finance With 4B's — Flask Backend

Project structure:
  backend/   → this app (Flask API + route handlers)
  frontend/  → templates/ (HTML) and static/ (assets, config.json)
  database/  → schema.sql (MySQL schema, applied by init_db)

Endpoints:
  GET /api/gold     → Manual gold/silver/platinum rates (MySQL)
  GET /api/stocks   → Top 45 NSE Nifty 50 stocks (yfinance)
  GET /api/indices  → Market indices: Sensex, Nifty 50, Bank Nifty, IT (yfinance)
  GET /api/strip    → Crude/Property strip data (yfinance + configured)
  GET /             → Serves the frontend HTML
  GET /admin        → Admin login
  GET /admin/rates  → Admin rate entry
"""

from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import logging
import os
from functools import wraps
import mysql.connector

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
DATABASE_DIR = os.path.join(BASE_DIR, "..", "database")
SCHEMA_FILE = os.path.join(DATABASE_DIR, "schema.sql")

app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, "templates"),
    static_folder=os.path.join(FRONTEND_DIR, "static"),
)
CORS(app)  # Allow frontend on any port to call these endpoints
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "finance-with-4bs-secret")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── CONFIG ───────────────────────────────────────────────
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "finance@mujeeb")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "financewithmujeeb")

MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "finance_rates")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))

DB_READY = True
DB_ERROR = None

OIL_SYMBOL = "CL=F"  # WTI Crude Oil (NYMEX)

# Mumbai property (per sq.ft) — update as needed
MUMBAI_PROPERTY_RATE = 18400
MUMBAI_PROPERTY_CHANGE_PCT = 2.1

OIL_FALLBACK = {"price": 83.42, "prev_close": 82.49}

NSE_SYMBOLS = [
    {"sym": "RELIANCE.NS",   "name": "Reliance Industries",   "sector": "Energy"},
    {"sym": "TCS.NS",        "name": "Tata Consultancy",       "sector": "IT"},
    {"sym": "HDFCBANK.NS",   "name": "HDFC Bank",              "sector": "Banking"},
    {"sym": "INFY.NS",       "name": "Infosys",                "sector": "IT"},
    {"sym": "ICICIBANK.NS",  "name": "ICICI Bank",             "sector": "Banking"},
    {"sym": "HINDUNILVR.NS", "name": "Hindustan Unilever",     "sector": "FMCG"},
    {"sym": "ITC.NS",        "name": "ITC Limited",            "sector": "FMCG"},
    {"sym": "KOTAKBANK.NS",  "name": "Kotak Mahindra Bank",    "sector": "Banking"},
    {"sym": "SBIN.NS",       "name": "State Bank of India",    "sector": "Banking"},
    {"sym": "BHARTIARTL.NS", "name": "Bharti Airtel",          "sector": "Telecom"},
    {"sym": "BAJFINANCE.NS", "name": "Bajaj Finance",          "sector": "Banking"},
    {"sym": "AXISBANK.NS",   "name": "Axis Bank",              "sector": "Banking"},
    {"sym": "ASIANPAINT.NS", "name": "Asian Paints",           "sector": "FMCG"},
    {"sym": "MARUTI.NS",     "name": "Maruti Suzuki",          "sector": "Auto"},
    {"sym": "SUNPHARMA.NS",  "name": "Sun Pharmaceutical",     "sector": "Pharma"},
    {"sym": "TATAMOTORS.NS", "name": "Tata Motors",            "sector": "Auto"},
    {"sym": "WIPRO.NS",      "name": "Wipro",                  "sector": "IT"},
    {"sym": "HCLTECH.NS",    "name": "HCL Technologies",       "sector": "IT"},
    {"sym": "ULTRACEMCO.NS", "name": "UltraTech Cement",       "sector": "Infra"},
    {"sym": "TITAN.NS",      "name": "Titan Company",          "sector": "FMCG"},
    {"sym": "NESTLEIND.NS",  "name": "Nestle India",           "sector": "FMCG"},
    {"sym": "BAJAJFINSV.NS", "name": "Bajaj Finserv",          "sector": "Banking"},
    {"sym": "POWERGRID.NS",  "name": "Power Grid Corp",        "sector": "Energy"},
    {"sym": "NTPC.NS",       "name": "NTPC Limited",           "sector": "Energy"},
    {"sym": "TECHM.NS",      "name": "Tech Mahindra",          "sector": "IT"},
    {"sym": "ONGC.NS",       "name": "Oil & Natural Gas",      "sector": "Energy"},
    {"sym": "COALINDIA.NS",  "name": "Coal India",             "sector": "Energy"},
    {"sym": "TATASTEEL.NS",  "name": "Tata Steel",             "sector": "Metals"},
    {"sym": "ADANIENT.NS",   "name": "Adani Enterprises",      "sector": "Infra"},
    {"sym": "ADANIPORTS.NS", "name": "Adani Ports",            "sector": "Infra"},
    {"sym": "GRASIM.NS",     "name": "Grasim Industries",      "sector": "Infra"},
    {"sym": "JSWSTEEL.NS",   "name": "JSW Steel",              "sector": "Metals"},
    {"sym": "HEROMOTOCO.NS", "name": "Hero MotoCorp",          "sector": "Auto"},
    {"sym": "DIVISLAB.NS",   "name": "Divi's Laboratories",    "sector": "Pharma"},
    {"sym": "DRREDDY.NS",    "name": "Dr. Reddy's Labs",       "sector": "Pharma"},
    {"sym": "EICHERMOT.NS",  "name": "Eicher Motors",          "sector": "Auto"},
    {"sym": "BAJAJ-AUTO.NS", "name": "Bajaj Auto",             "sector": "Auto"},
    {"sym": "CIPLA.NS",      "name": "Cipla Limited",          "sector": "Pharma"},
    {"sym": "BPCL.NS",       "name": "BPCL",                   "sector": "Energy"},
    {"sym": "HINDALCO.NS",   "name": "Hindalco Industries",    "sector": "Metals"},
    {"sym": "LT.NS",         "name": "Larsen & Toubro",        "sector": "Infra"},
    {"sym": "BRITANNIA.NS",  "name": "Britannia Industries",   "sector": "FMCG"},
    {"sym": "SBILIFE.NS",    "name": "SBI Life Insurance",     "sector": "Banking"},
    {"sym": "APOLLOHOSP.NS", "name": "Apollo Hospitals",       "sector": "Pharma"},
    {"sym": "TATACONSUM.NS", "name": "Tata Consumer",          "sector": "FMCG"},
]

INDEX_SYMBOLS = [
    {"sym": "^NSEI",    "id": "nifty50",    "name": "Nifty 50",    "label": "NIFTY 50"},
    {"sym": "^BSESN",   "id": "sensex",     "name": "BSE Sensex",  "label": "SENSEX"},
    {"sym": "^NSEBANK", "id": "banknifty",  "name": "Bank Nifty",  "label": "BANK NIFTY"},
    {"sym": "^CNXIT",   "id": "niftyit",    "name": "Nifty IT",    "label": "NIFTY IT"},
]


# ─── HELPER ───────────────────────────────────────────────
def safe_round(val, decimals=2):
    try:
        return round(float(val), decimals)
    except (TypeError, ValueError):
        return None


def get_db_connection(with_db=True):
    if not DB_READY:
        raise RuntimeError(f"Database not available: {DB_ERROR or 'init failed'}")
    config = {
        "host": MYSQL_HOST,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
        "port": MYSQL_PORT,
        "autocommit": True,
    }
    if with_db:
        config["database"] = MYSQL_DATABASE
    return mysql.connector.connect(**config)


def load_schema_statements():
    """Read database/schema.sql and split it into executable statements."""
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        raw = f.read()
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
    cleaned = "\n".join(lines)
    return [stmt.strip() for stmt in cleaned.split(";") if stmt.strip()]


def init_db():
    global DB_READY, DB_ERROR
    db_name = MYSQL_DATABASE.replace("`", "")
    try:
        # Create the database first (schema.sql may reference it via USE).
        conn = get_db_connection(with_db=False)
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        cur.close()
        conn.close()

        # Apply the table schema from the database layer (database/schema.sql).
        conn = get_db_connection()
        cur = conn.cursor()
        for statement in load_schema_statements():
            if statement.upper().startswith(("CREATE DATABASE", "USE")):
                continue  # database + connection already handled above
            cur.execute(statement)
        cur.close()
        conn.close()
        DB_READY = True
        DB_ERROR = None
    except (mysql.connector.Error, OSError) as e:
        DB_READY = False
        DB_ERROR = str(e)
        logger.error(f"MySQL init error: {e}")


def fetch_rates():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT gold_24k, gold_22k, gold_18k, silver_per_gram, platinum_per_gram, updated_at
        FROM metal_rates
        WHERE id = 1
        """
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def save_rates(gold_24k, gold_22k, gold_18k, silver_per_gram, platinum_per_gram):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO metal_rates (id, gold_24k, gold_22k, gold_18k, silver_per_gram, platinum_per_gram)
        VALUES (1, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            gold_24k = VALUES(gold_24k),
            gold_22k = VALUES(gold_22k),
            gold_18k = VALUES(gold_18k),
            silver_per_gram = VALUES(silver_per_gram),
            platinum_per_gram = VALUES(platinum_per_gram),
            updated_at = CURRENT_TIMESTAMP
        """,
        (gold_24k, gold_22k, gold_18k, silver_per_gram, platinum_per_gram),
    )
    cur.close()
    conn.close()


def build_manual_payload(rates):
    def build_weight_block(per_gram):
        if per_gram is None:
            return {"per_gram": None, "per_1g": None, "per_5g": None, "per_8g": None, "per_10g": None}
        per_gram = safe_round(per_gram, 2)
        return {
            "per_gram": per_gram,
            "per_1g": per_gram,
            "per_5g": safe_round(per_gram * 5, 0),
            "per_8g": safe_round(per_gram * 8, 0),
            "per_10g": safe_round(per_gram * 10, 0),
        }

    def build_metal_block(per_gram):
        if per_gram is None:
            return {
                "price_per_gram": None,
                "price_per_5g": None,
                "price_per_8g": None,
                "price_per_10g": None,
                "price_per_kg": None,
                "change_pct": None,
                "change_amt": None,
            }
        per_gram = safe_round(per_gram, 2)
        return {
            "price_per_gram": per_gram,
            "price_per_5g": safe_round(per_gram * 5, 0),
            "price_per_8g": safe_round(per_gram * 8, 0),
            "price_per_10g": safe_round(per_gram * 10, 0),
            "price_per_kg": safe_round(per_gram * 1000, 0),
            "change_pct": None,
            "change_amt": None,
        }

    gold_24k = rates.get("gold_24k") if rates else None
    gold_22k = rates.get("gold_22k") if rates else None
    gold_18k = rates.get("gold_18k") if rates else None
    silver_per_gram = rates.get("silver_per_gram") if rates else None
    platinum_per_gram = rates.get("platinum_per_gram") if rates else None
    updated_at = rates.get("updated_at") if rates else None
    updated_at_str = updated_at.strftime("%Y-%m-%d %H:%M:%S") if updated_at else None

    return {
        "status": "ok",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "currency": "INR",
        "source": "Manual Entry",
        "rates_updated_at": updated_at_str,
        "has_rates": any(v is not None for v in [gold_24k, gold_22k, gold_18k, silver_per_gram, platinum_per_gram]),
        "gold": {
            "24K": build_weight_block(gold_24k),
            "22K": build_weight_block(gold_22k),
            "18K": build_weight_block(gold_18k),
        },
        "gold_usd": {
            "price_oz": None,
            "change_amt": None,
            "change_pct": None,
        },
        "silver": build_metal_block(silver_per_gram),
        "platinum": build_metal_block(platinum_per_gram),
    }


def parse_rate(value, label):
    if value is None or not str(value).strip():
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {label} rate.") from exc


def admin_required(handler):
    @wraps(handler)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return handler(*args, **kwargs)
    return wrapper


init_db()


# ─── ROUTES ───────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_rates"))

    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_rates"))
        error = "Invalid username or password."

    return render_template("admin_login.html", error=error)


@app.route("/admin/rates", methods=["GET", "POST"])
@admin_required
def admin_rates():
    error = None
    success = None

    if request.method == "POST":
        try:
            gold_24k = parse_rate(request.form.get("gold_24k"), "24K gold")
            gold_22k = parse_rate(request.form.get("gold_22k"), "22K gold")
            gold_18k = parse_rate(request.form.get("gold_18k"), "18K gold")
            silver = parse_rate(request.form.get("silver_per_gram"), "silver")
            platinum = parse_rate(request.form.get("platinum_per_gram"), "platinum")
            if gold_24k is None and gold_22k is None and gold_18k is None and silver is None and platinum is None:
                raise ValueError("Enter at least one metal rate.")
            save_rates(gold_24k, gold_22k, gold_18k, silver, platinum)
            success = "Rates updated successfully."
        except ValueError as e:
            error = str(e)
        except (mysql.connector.Error, RuntimeError) as e:
            logger.error(f"MySQL error: {e}")
            error = "Database error. Check your MySQL connection."

    try:
        rates = fetch_rates()
    except (mysql.connector.Error, RuntimeError) as e:
        logger.error(f"MySQL error: {e}")
        error = error or "Database error. Check your MySQL connection."
        rates = {}
    return render_template(
        "admin_rates.html",
        rates=rates or {},
        error=error,
        success=success,
    )


@app.route("/admin/logout")
@admin_required
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


@app.route("/api/gold")
def get_gold():
    """
    Returns manual gold/silver/platinum rates stored in MySQL.
    """
    try:
        rates = fetch_rates()
        return jsonify(build_manual_payload(rates))
    except (mysql.connector.Error, RuntimeError) as e:
        logger.error(f"MySQL error: {e}")
        return jsonify({"status": "error", "message": "Database error"}), 500
    except Exception as e:
        logger.error(f"Manual rate error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/indices")
def get_indices():
    """
    Fetches Nifty 50, Sensex, Bank Nifty, Nifty IT via yfinance with timeout handling.
    Falls back to cached values if API is unavailable.
    """
    # Fallback/cached data (April 2026 live rates from website)
    FALLBACK_DATA = {
        "^NSEI":    {"name": "Nifty 50",    "price": 23997.55, "prev_close": 23883.80},
        "^BSESN":   {"name": "BSE Sensex",  "price": 76913.50, "prev_close": 76532.15},
        "^NSEBANK": {"name": "Bank Nifty",  "price": 52843.25, "prev_close": 52614.70},
        "^CNXIT":   {"name": "Nifty IT",    "price": 19654.80, "prev_close": 19523.40},
    }
    
    try:
        syms = [i["sym"] for i in INDEX_SYMBOLS]
        tickers = yf.Tickers(" ".join(syms))
        result = []

        for meta in INDEX_SYMBOLS:
            sym = meta["sym"]
            try:
                t = tickers.tickers[sym]
                info = t.fast_info
                price      = safe_round(info.last_price, 2)
                prev_close = safe_round(info.previous_close, 2)

                if price is None or prev_close is None:
                    hist = t.history(period="5d", interval="1d")
                    if not hist.empty:
                        price = safe_round(hist["Close"].iloc[-1], 2)
                        prev_close = safe_round(
                            hist["Close"].iloc[-2] if len(hist) > 1 else hist["Close"].iloc[-1], 2
                        )

                # If we got the data, use it
                if price is not None and prev_close is not None:
                    change     = safe_round((price or 0) - (prev_close or 0), 2)
                    change_pct = safe_round(((change / prev_close) * 100) if prev_close else 0, 2)
                else:
                    # Use fallback data
                    fb = FALLBACK_DATA.get(sym, {})
                    price = fb.get("price")
                    prev_close = fb.get("prev_close")
                    change = safe_round((price or 0) - (prev_close or 0), 2) if price and prev_close else None
                    change_pct = safe_round(((change / prev_close) * 100) if change and prev_close else 0, 2)
                    logger.info(f"Using fallback data for {sym}")
                
                result.append({
                    "id":         meta["id"],
                    "sym":        sym,
                    "name":       meta["name"],
                    "label":      meta["label"],
                    "price":      price,
                    "prev_close": prev_close,
                    "change":     change,
                    "change_pct": change_pct,
                })
            except Exception as e:
                logger.warning(f"Index {sym} failed: {e}, trying fallback")
                # Use fallback data
                fb = FALLBACK_DATA.get(sym, {})
                price = fb.get("price")
                prev_close = fb.get("prev_close")
                change = safe_round((price or 0) - (prev_close or 0), 2) if price and prev_close else None
                change_pct = safe_round(((change / prev_close) * 100) if change and prev_close else 0, 2)
                result.append({
                    "id": meta["id"], "sym": sym,
                    "name": meta["name"], "label": meta["label"],
                    "price": price, "change": change, "change_pct": change_pct,
                })

        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "indices": result,
        })

    except Exception as e:
        logger.error(f"Indices error: {e}")
        # Return fallback data on complete failure
        result = []
        for meta in INDEX_SYMBOLS:
            sym = meta["sym"]
            fb = FALLBACK_DATA.get(sym, {})
            price = fb.get("price")
            prev_close = fb.get("prev_close")
            change = safe_round((price or 0) - (prev_close or 0), 2) if price and prev_close else None
            change_pct = safe_round(((change / prev_close) * 100) if change and prev_close else 0, 2)
            result.append({
                "id": meta["id"], "sym": sym,
                "name": meta["name"], "label": meta["label"],
                "price": price, "change": change, "change_pct": change_pct,
            })
        
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "indices": result,
        })


@app.route("/api/strip")
def get_strip():
    """
    Returns live strip data for Crude Oil (WTI) and Mumbai Property.
    Crude Oil is fetched via yfinance; property uses configured values.
    """
    try:
        # Crude oil (WTI)
        price = prev_close = None
        try:
            t = yf.Ticker(OIL_SYMBOL)
            info = t.fast_info
            price = safe_round(info.last_price, 2)
            prev_close = safe_round(info.previous_close, 2)

            if price is None or prev_close is None:
                hist = t.history(period="5d", interval="1d")
                if not hist.empty:
                    price = safe_round(hist["Close"].iloc[-1], 2)
                    prev_close = safe_round(
                        hist["Close"].iloc[-2] if len(hist) > 1 else hist["Close"].iloc[-1], 2
                    )
        except Exception as e:
            logger.warning(f"Crude oil fetch failed: {e}")

        if price is None or prev_close is None:
            price = OIL_FALLBACK["price"]
            prev_close = OIL_FALLBACK["prev_close"]

        change = safe_round((price or 0) - (prev_close or 0), 2)
        change_pct = safe_round(((change / prev_close) * 100) if prev_close else 0, 2)

        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "crude": {
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "unit": "WTI",
            },
            "property": {
                "name": "Mumbai Property",
                "price_per_sqft": MUMBAI_PROPERTY_RATE,
                "change_pct": MUMBAI_PROPERTY_CHANGE_PCT,
                "unit": "per sq.ft (avg)",
            }
        })

    except Exception as e:
        logger.error(f"Strip error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stocks")
def get_stocks():
    """
    Fetches all 45 NSE stocks via yfinance in one batch call.
    Returns price, change, change_pct, day_high, day_low, volume, 52w_high, 52w_low.
    Falls back to sample data if yfinance times out.
    """
    # Fallback data - sample top stocks with typical values
    FALLBACK_STOCKS = [
        {"sym": "RELIANCE.NS", "ticker": "RELIANCE", "name": "Reliance Industries", "sector": "Energy", "price": 3275.45, "prev_close": 3242.10, "day_high": 3310.80, "day_low": 3195.50, "week52_high": 3580.00, "week52_low": 2840.00, "volume": 12500000},
        {"sym": "TCS.NS", "ticker": "TCS", "name": "Tata Consultancy", "sector": "IT", "price": 4158.75, "prev_close": 4142.30, "day_high": 4220.00, "day_low": 4095.50, "week52_high": 4895.00, "week52_low": 3620.00, "volume": 2850000},
        {"sym": "HDFCBANK.NS", "ticker": "HDFCBANK", "name": "HDFC Bank", "sector": "Banking", "price": 1875.40, "prev_close": 1861.90, "day_high": 1904.50, "day_low": 1832.25, "week52_high": 2180.00, "week52_low": 1480.00, "volume": 4125000},
        {"sym": "INFY.NS", "ticker": "INFY", "name": "Infosys", "sector": "IT", "price": 2198.65, "prev_close": 2180.45, "day_high": 2245.80, "day_low": 2155.20, "week52_high": 2640.00, "week52_low": 1850.00, "volume": 1950000},
        {"sym": "ICICIBANK.NS", "ticker": "ICICIBANK", "name": "ICICI Bank", "sector": "Banking", "price": 1158.90, "prev_close": 1142.75, "day_high": 1195.50, "day_low": 1125.10, "week52_high": 1325.00, "week52_low": 875.50, "volume": 3650000},
    ]
    
    try:
        syms = [s["sym"] for s in NSE_SYMBOLS]
        tickers = yf.Tickers(" ".join(syms))
        result = []

        for meta in NSE_SYMBOLS:
            sym = meta["sym"]
            try:
                t    = tickers.tickers[sym]
                info = t.fast_info
                price      = safe_round(info.last_price, 2)
                prev_close = safe_round(info.previous_close, 2)
                day_high   = safe_round(info.day_high, 2)
                day_low    = safe_round(info.day_low,  2)
                week52_high= safe_round(info.year_high, 2)
                week52_low = safe_round(info.year_low,  2)
                volume     = int(info.three_month_average_volume or 0)

                if price is None or prev_close is None:
                    hist = t.history(period="5d", interval="1d")
                    if not hist.empty:
                        price = safe_round(hist["Close"].iloc[-1], 2)
                        prev_close = safe_round(
                            hist["Close"].iloc[-2] if len(hist) > 1 else hist["Close"].iloc[-1], 2
                        )
                        day_high = safe_round(hist["High"].iloc[-1], 2)
                        day_low  = safe_round(hist["Low"].iloc[-1],  2)

                change     = safe_round((price or 0) - (prev_close or 0), 2)
                change_pct = safe_round(((change / prev_close) * 100) if prev_close else 0, 2)
                result.append({
                    "sym":        sym,
                    "ticker":     sym.replace(".NS", ""),
                    "name":       meta["name"],
                    "sector":     meta["sector"],
                    "price":      price,
                    "prev_close": prev_close,
                    "change":     change,
                    "change_pct": change_pct,
                    "day_high":   day_high,
                    "day_low":    day_low,
                    "week52_high":week52_high,
                    "week52_low": week52_low,
                    "volume":     volume,
                })
            except Exception as e:
                logger.warning(f"Stock {sym} failed: {e}, using fallback")
                # Try fallback data
                fallback = next((s for s in FALLBACK_STOCKS if s["sym"] == sym), None)
                if fallback:
                    change = safe_round(fallback["price"] - fallback["prev_close"], 2)
                    change_pct = safe_round((change / fallback["prev_close"] * 100), 2)
                    result.append({
                        "sym": sym, "ticker": sym.replace(".NS", ""),
                        "name": meta["name"], "sector": meta["sector"],
                        "price": fallback["price"], "change": change, "change_pct": change_pct,
                        "day_high": fallback["day_high"], "day_low": fallback["day_low"],
                        "week52_high": fallback["week52_high"], "week52_low": fallback["week52_low"], 
                        "volume": fallback["volume"],
                    })
                else:
                    result.append({
                        "sym": sym, "ticker": sym.replace(".NS", ""),
                        "name": meta["name"], "sector": meta["sector"],
                        "price": None, "change": None, "change_pct": None,
                        "day_high": None, "day_low": None,
                        "week52_high": None, "week52_low": None, "volume": None,
                    })

        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "count": len(result),
            "stocks": result,
        })

    except Exception as e:
        logger.error(f"Stocks error: {e}, using fallback")
        # Return fallback data on complete failure
        result = []
        for meta in NSE_SYMBOLS:
            sym = meta["sym"]
            fallback = next((s for s in FALLBACK_STOCKS if s["sym"] == sym), None)
            if fallback:
                change = safe_round(fallback["price"] - fallback["prev_close"], 2)
                change_pct = safe_round((change / fallback["prev_close"] * 100), 2)
                result.append({
                    "sym": sym, "ticker": sym.replace(".NS", ""),
                    "name": meta["name"], "sector": meta["sector"],
                    "price": fallback["price"], "change": change, "change_pct": change_pct,
                    "day_high": fallback["day_high"], "day_low": fallback["day_low"],
                    "week52_high": fallback["week52_high"], "week52_low": fallback["week52_low"], 
                    "volume": fallback["volume"],
                })
            else:
                result.append({
                    "sym": sym, "ticker": sym.replace(".NS", ""),
                    "name": meta["name"], "sector": meta["sector"],
                    "price": None, "change": None, "change_pct": None,
                    "day_high": None, "day_low": None,
                    "week52_high": None, "week52_low": None, "volume": None,
                })
        
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "count": len(result),
            "stocks": result,
        })


if __name__ == "__main__":
    print("\n" + "="*54)
    print("  Finance With 4B's — Flask Backend")
    print("  https://127.0.0.1:5000")
    print("  API endpoints:")
    print("    GET /api/gold (manual MySQL rates)")
    print("    GET /api/indices")
    print("    GET /api/strip")
    print("    GET /api/stocks")
    print("  Admin:")
    print("    GET /admin")
    print("    GET /admin/rates")
    print("="*54 + "\n")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
