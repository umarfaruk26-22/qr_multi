import os
import sys
from pathlib import Path
from werkzeug.security import generate_password_hash
import mysql.connector

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import Config
from database.connection import get_db_connection

def init_database(seed_sample_data=True):
    """
    Initializes the MySQL database schema, default admin user,
    and optional sample employees.
    """
    print("=" * 60)
    print("Starting Employee Digital Profile & QR System DB Initialization")
    print("=" * 60)
    print(f"Connecting to MySQL server at {Config.DB_HOST}:{Config.DB_PORT} as user '{Config.DB_USER}'...")

    # Step 1: Connect to server without database to create DB if not exists
    try:
        server_conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            charset="utf8mb4",
            autocommit=True
        )
        server_cursor = server_conn.cursor()
        server_cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        server_cursor.close()
        server_conn.close()
        print(f"[OK] Database `{Config.DB_NAME}` created or already exists.")
    except Exception as e:
        print(f"[ERROR] Failed to connect to MySQL server: {e}")
        print("Please ensure XAMPP MySQL / MySQL service is running on port 3306.")
        return False

    # Step 2: Execute Schema SQL
    schema_path = BASE_DIR / 'database' / 'schema.sql'
    if not schema_path.exists():
        print(f"[ERROR] schema.sql not found at {schema_path}")
        return False

    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Split and execute individual statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        for stmt in statements:
            if stmt:
                cursor.execute(stmt)
                
        db_conn.commit()
        print("[OK] Schema tables and indexes applied successfully.")

        # Ensure review_categories column exists in employees table (migration)
        try:
            cursor.execute("SHOW COLUMNS FROM employees LIKE 'review_categories'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE employees ADD COLUMN review_categories TEXT DEFAULT NULL")
                db_conn.commit()
                print("[OK] Added 'review_categories' column to employees table.")
        except Exception as col_err:
            print(f"[INFO] Column check note: {col_err}")

        # Ensure visitor_leads table exists (migration)
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS `visitor_leads` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `employee_id` INT NOT NULL,
                    `name` VARCHAR(150) NOT NULL,
                    `phone` VARCHAR(50) NOT NULL,
                    `email` VARCHAR(150) NOT NULL,
                    `dob` DATE DEFAULT NULL,
                    `anniversary` DATE DEFAULT NULL,
                    `city` VARCHAR(100) DEFAULT NULL,
                    `source` VARCHAR(50) DEFAULT 'direct_web',
                    `ip_address` VARCHAR(100) DEFAULT '',
                    `user_agent` TEXT,
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT `fk_leads_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE,
                    INDEX `idx_leads_employee` (`employee_id`),
                    INDEX `idx_leads_phone` (`phone`),
                    INDEX `idx_leads_email` (`email`),
                    INDEX `idx_leads_created` (`created_at`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """
            )
            db_conn.commit()
            print("[OK] Verified 'visitor_leads' table structure.")
        except Exception as lead_err:
            print(f"[INFO] visitor_leads table check note: {lead_err}")

        # Step 3: Seed Default Admin
        default_username = 'admin'
        default_password = 'Admin@12345'
        
        cursor.execute("SELECT id FROM admins WHERE username = %s", (default_username,))
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            hashed_pw = generate_password_hash(default_password)
            cursor.execute(
                """
                INSERT INTO admins (username, password_hash, name, is_active)
                VALUES (%s, %s, %s, %s)
                """,
                (default_username, hashed_pw, 'System Administrator', 1)
            )
            db_conn.commit()
            print(f"[OK] Default admin created successfully.")
            print(f"     Username: {default_username}")
            print(f"     Password: {default_password} (Development Only)")
        else:
            print("[INFO] Admin user already exists. Skipping default admin insertion.")

        # Step 4: Seed Company Settings if not present
        cursor.execute("SELECT id FROM settings WHERE id = 1")
        settings_exists = cursor.fetchone()
        if not settings_exists:
            cursor.execute(
                """
                INSERT INTO settings (id, company_name, company_phone, company_email, company_website, primary_color, secondary_color, default_whatsapp_message)
                VALUES (1, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    'Apex Innovations',
                    '+91 98765 43210',
                    'contact@apexinnovations.com',
                    'https://apexinnovations.com',
                    '#4f46e5',
                    '#06b6d4',
                    'Hello, I visited your digital profile and would like to connect.'
                )
            )
            db_conn.commit()
            print("[OK] Default company settings initialized.")

        # Step 5: Seed Sample Employees if requested and table is empty
        if seed_sample_data:
            cursor.execute("SELECT COUNT(*) FROM employees WHERE is_deleted = 0")
            emp_count = cursor.fetchone()[0]
            if emp_count == 0:
                print("[INFO] Seeding sample employee profiles (Rahul Sharma, Aamir Khan, Priya Patel)...")
                sample_employees = [
                    {
                        "first_name": "Rahul",
                        "last_name": "Sharma",
                        "slug": "rahul",
                        "designation": "Senior Sales Executive",
                        "phone": "+919876543210",
                        "whatsapp": "919876543210",
                        "email": "rahul.sharma@apexinnovations.com",
                        "bio": "Passionate sales leader with 7+ years of experience helping enterprise clients scale their digital presence.",
                        "social": {
                            "instagram_url": "https://instagram.com",
                            "facebook_url": "https://facebook.com",
                            "linkedin_url": "https://linkedin.com/in/rahulsharma",
                            "youtube_url": "https://youtube.com",
                            "website_url": "https://apexinnovations.com",
                            "google_review_url": "https://g.page/r/example-review-rahul"
                        }
                    },
                    {
                        "first_name": "Aamir",
                        "last_name": "Khan",
                        "slug": "aamir",
                        "designation": "Business Operations Manager",
                        "phone": "+919811223344",
                        "whatsapp": "919811223344",
                        "email": "aamir.khan@apexinnovations.com",
                        "bio": "Overseeing strategic growth and operational excellence across multi-channel client partnerships.",
                        "social": {
                            "instagram_url": "https://instagram.com",
                            "facebook_url": "https://facebook.com",
                            "linkedin_url": "https://linkedin.com/in/aamirkhan",
                            "youtube_url": "",
                            "website_url": "https://apexinnovations.com",
                            "google_review_url": "https://g.page/r/example-review-aamir"
                        }
                    },
                    {
                        "first_name": "Priya",
                        "last_name": "Patel",
                        "slug": "priya",
                        "designation": "Head of People & Talent",
                        "phone": "+919844556677",
                        "whatsapp": "919844556677",
                        "email": "priya.patel@apexinnovations.com",
                        "bio": "Connecting talented professionals with dream opportunities and building inclusive high-performance cultures.",
                        "social": {
                            "instagram_url": "https://instagram.com",
                            "facebook_url": "",
                            "linkedin_url": "https://linkedin.com/in/priyapatel",
                            "youtube_url": "",
                            "website_url": "https://apexinnovations.com",
                            "google_review_url": "https://g.page/r/example-review-priya"
                        }
                    }
                ]

                for emp in sample_employees:
                    cursor.execute(
                        """
                        INSERT INTO employees (first_name, last_name, slug, designation, phone, whatsapp, email, bio, is_active, is_deleted)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, 0)
                        """,
                        (emp["first_name"], emp["last_name"], emp["slug"], emp["designation"], emp["phone"], emp["whatsapp"], emp["email"], emp["bio"])
                    )
                    emp_id = cursor.lastrowid
                    
                    # Social links
                    s = emp["social"]
                    cursor.execute(
                        """
                        INSERT INTO social_links (employee_id, instagram_url, facebook_url, linkedin_url, youtube_url, website_url, google_review_url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (emp_id, s["instagram_url"], s["facebook_url"], s["linkedin_url"], s["youtube_url"], s["website_url"], s["google_review_url"])
                    )
                    
                    # Placeholder QR code info
                    qr_url = f"{Config.BASE_URL}/q/{emp['slug']}"
                    png_path = f"uploads/qr/{emp['slug']}.png"
                    svg_path = f"uploads/qr/{emp['slug']}.svg"
                    branded_path = f"uploads/qr/{emp['slug']}_branded.png"
                    
                    cursor.execute(
                        """
                        INSERT INTO qr_codes (employee_id, qr_url, png_path, svg_path, branded_png_path)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (emp_id, qr_url, png_path, svg_path, branded_path)
                    )

                db_conn.commit()
                print("[OK] Sample employees (Rahul, Aamir, Priya) seeded successfully.")

        cursor.close()
        db_conn.close()
        print("=" * 60)
        print("[SUCCESS] Database initialization completed successfully!")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    init_database()
