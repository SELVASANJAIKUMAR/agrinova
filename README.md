# AgriNova

AI-powered smart agriculture marketplace web app connecting farmers (sellers) and buyers across Tamil Nadu, India.

## Tech Stack

- **Frontend:** HTML, CSS, Bootstrap 5, vanilla JavaScript (Django templates)
- **Backend:** Python, Django
- **Database:** MySQL (PyMySQL driver)
- **AI/ML:** scikit-learn (price forecasting), Groq + Gemini (chatbot with fallback)
- **Testing:** pytest-django
- **Deployment:** Render (gunicorn + WhiteNoise)

## Project Structure

```
agrinova/           # Django project settings
accounts/           # Auth & profiles
marketplace/        # Crop listings & browse
orders/             # Cart, checkout, mock payment
chatbot/            # AI assistant (Groq + Gemini fallback)
forecasting/        # Price prediction (synthetic demo data)
matching/           # Buyer-seller matching
dashboard/          # User dashboard
adminpanel/         # Custom admin analytics
static/ & templates/
```

## Local Setup

### 1. Prerequisites

- Python 3.12+
- MySQL Server + MySQL Workbench

### 2. Create MySQL Database

Open MySQL Workbench and run:

```sql
CREATE DATABASE agrinova_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Install Dependencies

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```powershell
copy .env.example .env
```

Edit `.env` with your MySQL credentials and API keys:

```
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=agrinova_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
```

### 5. Run Migrations

```powershell
python manage.py makemigrations
python manage.py migrate
```

### 6. Seed Data

```powershell
python manage.py seed_products
python manage.py seed_price_data
python manage.py createsuperuser
```

### 7. Run Development Server

```powershell
python manage.py runserver
```

Visit http://127.0.0.1:8000/

## Running Tests

Tests use SQLite (via `agrinova.test_settings`) for speed — no MySQL required for test runs.

```powershell
pytest
# or
python manage.py test --settings=agrinova.test_settings
```

## Key Features

| Module | Description |
|--------|-------------|
| Accounts | Register, login, logout, password reset, profile management |
| Marketplace | Browse/create/edit crop listings with filters & search |
| Orders | Session cart, checkout, mock test payment, order history |
| Chatbot | Floating widget + dedicated page, Groq primary / Gemini fallback |
| Forecasting | Synthetic price data + scikit-learn forecast with Chart.js |
| Matching | Explainable buyer-seller scoring on dashboard |
| Admin Panel | User/listing/order management + AI analytics (staff only) |

## Mock Payment

Checkout ends with a **"Confirm Test Payment"** button. No real payment gateway is integrated. Order status is set to `Paid (Test Mode)`.

## Price Forecast Disclaimer

Historical price data is **synthetically generated** by `seed_price_data` for demo purposes. The UI clearly labels this. The forecasting engine works with any `PriceRecord` data — swap in real data later without code changes.

## Deployment (Render)

1. Ensure all tests pass locally
2. Set `DEBUG=False` and configure `ALLOWED_HOSTS`
3. Set all environment variables in Render dashboard
4. Connect MySQL (Render add-on or external)
5. Run seed commands once after first deploy
6. Create superuser via Render shell

See `render.yaml` and `Procfile` for Render configuration.

## API Keys

Never commit `.env`. Both `GROQ_API_KEY` and `GEMINI_API_KEY` are read from environment variables. Provider order is configurable via `AI_PROVIDER_ORDER=groq,gemini`.
