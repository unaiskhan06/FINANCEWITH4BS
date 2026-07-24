# Finance With 4B's - Setup & Usage Guide

## Quick Start

## GitHub Pages (Static Hosting)
1. Push this repo to GitHub.
2. In **Settings → Pages**, set **Source** to `main` and **/ (root)**.
3. Visit `https://<username>.github.io/<repo>/`.

**Note:** GitHub Pages is static only. The Flask admin panel and live API do not run there. Edit the `STATIC_DATA` block inside `templates/index.html` to update the displayed rates, or connect the frontend to a hosted backend using `static/config.json`.

## Render (Backend Hosting)
1. Create a new Render **Web Service** and connect this GitHub repo.
2. Render will use `render.yaml` automatically. If prompted:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `python app.py`
3. After deploy, copy your Render URL (e.g. `https://your-app.onrender.com`).
4. Open `static/config.json` and set:
   ```json
   { "apiBase": "https://your-app.onrender.com" }
   ```
5. Commit and push the change so GitHub Pages points to the backend.

### 1. Set Environment Variables (PowerShell)
```powershell
$env:MYSQL_HOST="localhost"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="root"
$env:MYSQL_DATABASE="finance_rates"
$env:MYSQL_PORT="3306"
```

### 2. Run the App
```bash
python app.py
```

The app starts on: **http://127.0.0.1:5000**

---

## Admin Panel Usage

### 1. Access Admin Login
Open browser to: **http://127.0.0.1:5000/admin**

### 2. Login Credentials
- **Username:** `finance@mujeeb`
- **Password:** `financewithmujeeb`

### 3. Enter Metal Rates
The admin panel now accepts separate rates for:
- **24K Gold** (per gram in ₹)
- **22K Gold** (per gram in ₹)
- **18K Gold** (per gram in ₹)
- **Silver** (per gram in ₹)
- **Platinum** (per gram in ₹)

### 4. Submit Rates
- Click "Save Rates"
- You'll see a success message
- The rates now appear on the public website

---

## Public Website Display

After entering rates in admin panel:

### Gold Rates Section
Shows three cards for each purity:
- **24K Gold** with prices for 5g, 8g, 10g
- **22K Gold** with prices for 5g, 8g, 10g
- **18K Gold** with prices for 5g, 8g, 10g

### Silver & Platinum Sections
Shows prices for 5g, 8g, 10g quantities

### Gold Calculator
The on-page calculator updates with your entered 24K gold rate.

---

## Database

**Database Name:** `finance_rates`

**Table:** `metal_rates`
```sql
CREATE TABLE metal_rates (
    id INT PRIMARY KEY,
    gold_24k DECIMAL(12,2) NULL,
    gold_22k DECIMAL(12,2) NULL,
    gold_18k DECIMAL(12,2) NULL,
    silver_per_gram DECIMAL(12,2) NULL,
    platinum_per_gram DECIMAL(12,2) NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

---

## Example Rates to Enter

| Metal | Rate (₹ per gram) |
|-------|------------------|
| 24K Gold | 7500 |
| 22K Gold | 6875 |
| 18K Gold | 5625 |
| Silver | 90 |
| Platinum | 3200 |

---

## Troubleshooting

### Error: "Access denied for user 'root'@'localhost'"
- Ensure MySQL is running
- Verify credentials are correct: `root` / `root`
- Check MYSQL_HOST is `localhost` and MYSQL_PORT is `3306`

### Error: "Database error. Check your MySQL connection."
- Ensure all environment variables are set correctly
- Verify MySQL service is running
- Try restarting the app after checking MySQL connection

### Rates not showing on public site
- Ensure you logged in with correct credentials
- Verify you clicked "Save Rates" button
- Check admin panel shows last updated timestamp
- Refresh the public website in browser

---

## Features

✅ Manual rate entry (no external API dependency)
✅ Automatic weight calculations (5g, 8g, 10g)
✅ Three gold purities (24K, 22K, 18K)
✅ Silver and platinum support
✅ Admin authentication
✅ MySQL database storage
✅ Real-time display on public website
