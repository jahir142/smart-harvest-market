# Smart Harvest Market

Digital agri-marketplace platform featuring daily price tracking, category-based browsing, admin panel, and AI shopping assistance.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.9+** (Ensure **"Add Python to PATH"** is checked during installation)
- **XAMPP** (or any MySQL server)

### 2. Database Setup
1. Open **XAMPP Control Panel** and start **Apache** & **MySQL**.
2. Open phpMyAdmin at `http://localhost/phpmyadmin` and execute in the **SQL** tab:
   ```sql
   ALTER USER 'root'@'localhost' IDENTIFIED BY 'root';
   FLUSH PRIVILEGES;
   ```
   *(Note: You can also adjust your password in `db_config.json`)*

### 3. Installation & Run
1. Open a terminal inside the project directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the application:
   ```bash
   python app.py
   ```
4. Access the web app at:
   ```
   http://127.0.0.1:5000
   ```

---

## 🔐 Admin Access

- **URL:** `http://127.0.0.1:5000/admin/login`
- **Email:** `admin@market.com`
- **Password:** `admin123`

---

## 🤖 AI Chatbot Setup (Optional)

Configure your Gemini API key via one of the following methods:
- **Via Admin Panel:** Log in → go to **AI Settings** tab → paste your Gemini API key → click **Save & Verify**.
- **Via Config File:** Add your API key directly into `db_config.json`:
  ```json
  {
    "gemini_key": "YOUR_API_KEY",
    "password": "root"
  }
  ```

---

## 📁 Project Structure

| File / Directory | Description |
|---|---|
| `app.py` | Main Flask application server & API routes |
| `requirements.txt` | Python package dependencies |
| `db_config.json` | Local database & API key configuration |
| `products.json` | Stored custom & admin-managed products |
| `market_prices.json` | Daily market price data |
| `templates/` | HTML templates for market categories and pages |
| `static/` | Static assets (CSS, JavaScript, images) |

---
## 🛠️ Tech Stack & Technologies Used

- **Backend:** Python 3, Flask
- **Database:** MySQL (phpMyAdmin / XAMPP)
- **AI Integration:** Google Gemini API (AI Shopping Assistant)
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla CSS, Dynamic Animations)
- **Authentication:** Role-Based Access Control (Admin & Customer Sessions)

---

## 👨‍💻 Author

- **Developer:** Jahir ([@jahir142](https://github.com/jahir142))
- **GitHub:** [https://github.com/jahir142](https://github.com/jahir142)
- **Project:** [Smart Harvest Market](https://github.com/jahir142/smart-harvest-market)

---

## 🛠️ Troubleshooting

| Issue | Solution |
|---|---|
| `'pip' or 'python' not recognized` | Reinstall Python and ensure **"Add Python to PATH"** is selected. |
| `Database connection failed` | Verify MySQL is running in XAMPP and check the password in `db_config.json`. |
| `Port 5000 already in use` | Run on another port: `python app.py --port 8080`, or close the active process in Task Manager. |
| `Images not displaying` | Check your internet connection (product preview images are fetched online). |
