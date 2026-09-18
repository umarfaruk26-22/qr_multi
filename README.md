# Employee Digital Profile & QR Review System

A full-stack, production-ready web application built with **Python 3 Flask**, **MySQL**, **Vanilla HTML5/CSS3/JavaScript**, and **Python `qrcode`/Pillow**.

Every employee automatically gets:
1. A **dynamic public profile** page (e.g. `https://yourdomain.com/rahul`).
2. A **permanent QR code** pointing to `/q/<slug>` (e.g. `https://yourdomain.com/q/rahul`), which tracks scan analytics and redirects to their profile.
3. One-click **Google Review** CTA, **WhatsApp direct chat** with customizable prefilled message, and social links (Instagram, LinkedIn, Facebook, YouTube, Website).
4. Downloadable QR assets in **PNG**, **SVG**, and **Branded Corporate Card PNG** formats.

---

## Architecture Overview

```
                      [ CUSTOMER / CLIENT ]
                                │
                          Scans QR Code
                                │
                                ▼
                         GET /q/<slug>
                                │
                      (Records `qr_scan` event)
                                │
                                ▼ (302 Redirect)
                           GET /<slug>
                                │
                     ┌──────────┴──────────┐
                     │   Flask App (5000)  │
                     └──────────┬──────────┘
                                │ Parameterized Query
                                ▼
                      ┌───────────────────┐
                      │    MySQL (3306)   │
                      └───────────────────┘
                                │
                                ▼
                     Renders `employee.html`
             ┌──────────────────┼──────────────────┐
             ▼                  ▼                  ▼
        ⭐ Google Review     💬 WhatsApp       📸 Socials
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3 + Flask 3.x |
| **Database** | MySQL (XAMPP / MariaDB / Cloud MySQL) |
| **Database Connector** | `mysql-connector-python` (Parameterized queries & connection pooling) |
| **Frontend UI** | Semantic HTML5 + Custom Vanilla CSS3 (Design tokens, glassmorphism, responsive) |
| **Frontend Logic** | Vanilla JavaScript (Fetch API, Toast Notifications, Native Web Share) |
| **QR Generation** | Python `qrcode` + `Pillow` (PNG, SVG, and Branded Card generation) |
| **Authentication** | Flask Sessions + `werkzeug.security` password hashing |
| **Config & Env** | `python-dotenv` |

---

## Directory Structure

```
Multi-User-System/
├── app.py                     # Application entry point & factory
├── config.py                  # Environment configuration & constants
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── .env                       # Local environment file
├── .gitignore                 # Git ignore rules
├── README.md                  # Complete documentation & deployment guide
│
├── database/
│   ├── connection.py          # MySQL connection pool & context managers
│   ├── schema.sql             # Table creation & constraints
│   ├── seed.sql               # Default admin & sample employees
│   └── init_db.py             # CLI database migration / setup script
│
├── services/
│   ├── employee_service.py    # Employee CRUD, status toggling, soft delete
│   ├── slug_service.py        # Unique URL-safe slug generation logic
│   ├── qr_service.py          # PNG, SVG, and Branded QR generation with Pillow
│   ├── analytics_service.py   # Event tracking (views, scans, clicks) & metrics
│   ├── settings_service.py    # Company branding & global settings management
│   └── auth_service.py        # Admin login verification & password hashing
│
├── routes/
│   ├── auth.py                # Admin login, logout, session management
│   ├── admin.py               # Admin dashboard, employee CRUD, settings
│   ├── employee.py            # Public profile dynamic route (/<slug>)
│   ├── qr.py                  # QR scan redirection (/q/<slug>) & QR downloads
│   └── analytics.py           # Analytics ingestion & reporting REST APIs
│
├── templates/
│   ├── base.html              # Base HTML with SEO & assets
│   ├── public/
│   │   ├── employee.html      # Dynamic public mobile-first profile
│   │   ├── 404.html           # Custom 404 page
│   │   └── 500.html           # Custom 500 error page
│   └── admin/
│       ├── base_admin.html    # Admin layout with sidebar & top navbar
│       ├── login.html         # Admin login screen
│       ├── dashboard.html     # High-level metrics & quick actions
│       ├── employees.html     # Employee management table with filters & pagination
│       ├── add_employee.html  # Create employee form
│       ├── edit_employee.html # Edit employee form
│       ├── employee_details.html # Employee profile card, QR downloads & analytics
│       ├── analytics.html     # Detailed event metrics & charts/breakdowns
│       └── settings.html      # Company profile & color customization
│
├── static/
│   ├── css/
│   │   ├── main.css           # Global tokens, reset, typography & utility classes
│   │   ├── admin.css          # Admin SaaS UI, sidebar, cards, tables, modal, toast
│   │   └── public.css         # Premium glassmorphic mobile-first employee card
│   ├── js/
│   │   ├── main.js            # Global utilities (toast, copy-to-clipboard, theme)
│   │   ├── admin.js           # AJAX operations, filters, modals, image previews
│   │   └── public.js          # Analytics event logging on click, interactive share
│   └── images/                # Default logos and icons
│
├── uploads/                   # Runtime user uploads (git-ignored)
│   ├── profiles/
│   ├── logos/
│   └── qr/
│
└── tests/
    ├── test_auth.py           # Admin authentication tests
    ├── test_employees.py      # Employee CRUD & slug uniqueness tests
    └── test_qr.py             # QR code generation & scan redirection tests
```

---

## Local Setup & Installation (Windows + XAMPP)

### Step 1: Start XAMPP MySQL
1. Open **XAMPP Control Panel**.
2. Click **Start** next to **MySQL** (Port 3306).
3. *(Optional)* Apache can be started if you want to use phpMyAdmin at `http://localhost/phpmyadmin`.

### Step 2: Set Up Python Virtual Environment
Open PowerShell or Terminal inside `c:\Users\umarf\Multi-User-System`:

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` (already done by default):

```ini
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev_secret_key_change_in_production_987654321
BASE_URL=http://127.0.0.1:5000

DB_HOST=localhost
DB_PORT=3306
DB_NAME=employee_qr_system
DB_USER=root
DB_PASSWORD=

MAX_CONTENT_LENGTH=5242880
UPLOAD_FOLDER=uploads
```

### Step 4: Initialize the Database & Seed Data
Run the automated initialization script:

```powershell
.\venv\Scripts\python -m database.init_db
```

This will:
- Create the database `employee_qr_system` if it does not exist.
- Create all 6 tables (`admins`, `employees`, `social_links`, `qr_codes`, `analytics`, `settings`).
- Create the default administrator account (`admin` / `Admin@12345`).
- Seed sample employee profiles:
  - **Rahul Sharma** (`/rahul` & `/q/rahul`)
  - **Aamir Khan** (`/aamir` & `/q/aamir`)
  - **Priya Patel** (`/priya` & `/q/priya`)
- Generate standard PNG, SVG, and Branded Card PNG QR codes on disk.

### Step 5: Run the Flask Application
```powershell
.\venv\Scripts\python app.py
```

Open your browser:
- **Admin Portal**: `http://127.0.0.1:5000/admin/login`
- **Public Profile (Rahul)**: `http://127.0.0.1:5000/rahul`
- **QR Scan Redirection**: `http://127.0.0.1:5000/q/rahul`

---

## Default Admin Credentials

> [!NOTE]
> - **Username**: `admin`
> - **Password**: `Admin@12345`
> 
> You can update the password anytime under **Settings & Brand** -> **Change Admin Password**.

---

## REST API Reference

| Endpoint | Method | Access | Description |
|---|---|---|---|
| `/api/employees` | `GET` | Admin | Get paginated employee list (`?search=&status=&page=&per_page=`) |
| `/api/employees/<id>` | `GET` | Admin | Get single employee details with social links and QR records |
| `/api/employees/<id>` | `DELETE` | Admin | Soft-delete employee |
| `/api/employees/<id>/toggle-status` | `POST` | Admin | Toggle active/inactive status |
| `/api/analytics/event` | `POST` | Public | Log client-side engagement (`whatsapp_click`, `google_review_click`, etc.) |
| `/api/analytics/employee/<id>` | `GET` | Admin | Get analytics metrics breakdown for an employee |
| `/admin/qr/download/<id>/<format>` | `GET` | Admin | Download QR asset (`png`, `svg`, `branded`) |

---

## Running Automated Tests

Run the test suite using Python's `unittest`:

```powershell
.\venv\Scripts\python -m unittest discover -s tests
```

---

## Production Deployment Guide (Linux VPS + Nginx + Gunicorn + MySQL)

### 1. Server Prerequisites (Ubuntu 22.04 / 24.04 LTS)
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv mysql-server nginx git ufw certbot python3-certbot-nginx
```

### 2. Configure Production MySQL
```bash
sudo mysql_secure_installation
sudo mysql -u root -p
```
```sql
CREATE DATABASE employee_qr_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'emp_admin'@'localhost' IDENTIFIED BY 'StrongProductionPassword123!';
GRANT ALL PRIVILEGES ON employee_qr_system.* TO 'emp_admin'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Deploy Application Code
```bash
sudo mkdir -p /var/www/employee-system
sudo chown -R $USER:$USER /var/www/employee-system
cd /var/www/employee-system
git clone <your-repo-url> .

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn
```

### 4. Production `.env` File
```ini
FLASK_APP=app.py
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=generate_a_random_64_char_secret_key_here
BASE_URL=https://yourcompany.com

DB_HOST=localhost
DB_PORT=3306
DB_NAME=employee_qr_system
DB_USER=emp_admin
DB_PASSWORD=StrongProductionPassword123!

MAX_CONTENT_LENGTH=5242880
UPLOAD_FOLDER=uploads
```

Initialize database:
```bash
python3 -m database.init_db
```

### 5. Systemd Gunicorn Service (`/etc/systemd/system/employee-system.service`)
```ini
[Unit]
Description=Gunicorn instance to serve Employee QR Review System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/employee-system
Environment="PATH=/var/www/employee-system/venv/bin"
ExecStart=/var/www/employee-system/venv/bin/gunicorn --workers 4 --bind unix:/var/www/employee-system/app.sock "app:create_app()"

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo chown -R www-data:www-data /var/www/employee-system/uploads
sudo systemctl daemon-reload
sudo systemctl start employee-system
sudo systemctl enable employee-system
```

### 6. Nginx Reverse Proxy (`/etc/nginx/sites-available/employee-system`)
```nginx
server {
    listen 80;
    server_name yourcompany.com www.yourcompany.com;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/employee-system/static/;
        expires 30d;
    }

    location /uploads/ {
        alias /var/www/employee-system/uploads/;
        expires 7d;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/employee-system/app.sock;
    }
}
```

Enable site and configure SSL:
```bash
sudo ln -s /etc/nginx/sites-available/employee-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Install free SSL Certificate with Let's Encrypt
sudo certbot --nginx -d yourcompany.com -d www.yourcompany.com
```
