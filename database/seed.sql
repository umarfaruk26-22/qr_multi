-- Employee Digital Profile & QR Review System
-- Initial Seed Data

USE `employee_qr_system`;

-- 1. Initial Company Settings
INSERT INTO `settings` (`id`, `company_name`, `company_phone`, `company_email`, `company_website`, `primary_color`, `secondary_color`, `default_whatsapp_message`)
VALUES (
    1,
    'Apex Innovations',
    '+91 98765 43210',
    'contact@apexinnovations.com',
    'https://apexinnovations.com',
    '#4f46e5',
    '#06b6d4',
    'Hello, I visited your digital profile and would like to connect.'
) ON DUPLICATE KEY UPDATE `company_name` = VALUES(`company_name`);

-- 2. Seed Employees
-- Note: Passwords & Initial Admins are seeded securely via init_db.py using Werkzeug hashing.

INSERT INTO `employees` (`id`, `first_name`, `last_name`, `slug`, `designation`, `phone`, `whatsapp`, `email`, `bio`, `is_active`, `is_deleted`)
VALUES 
(
    1,
    'Rahul',
    'Sharma',
    'rahul',
    'Senior Sales Executive',
    '+919876543210',
    '919876543210',
    'rahul.sharma@apexinnovations.com',
    'Passionate sales leader with 7+ years of experience helping enterprise clients scale their digital presence.',
    1,
    0
),
(
    2,
    'Aamir',
    'Khan',
    'aamir',
    'Business Operations Manager',
    '+919811223344',
    '919811223344',
    'aamir.khan@apexinnovations.com',
    'Overseeing strategic growth and operational excellence across multi-channel client partnerships.',
    1,
    0
),
(
    3,
    'Priya',
    'Patel',
    'priya',
    'Head of People & Talent',
    '+919844556677',
    '919844556677',
    'priya.patel@apexinnovations.com',
    'Connecting talented professionals with dream opportunities and building inclusive high-performance cultures.',
    1,
    0
)
ON DUPLICATE KEY UPDATE `first_name` = VALUES(`first_name`);

-- 3. Social Links
INSERT INTO `social_links` (`employee_id`, `instagram_url`, `facebook_url`, `linkedin_url`, `youtube_url`, `website_url`, `google_review_url`)
VALUES
(
    1,
    'https://instagram.com',
    'https://facebook.com',
    'https://linkedin.com/in/rahulsharma',
    'https://youtube.com',
    'https://apexinnovations.com',
    'https://g.page/r/example-review-rahul'
),
(
    2,
    'https://instagram.com',
    'https://facebook.com',
    'https://linkedin.com/in/aamirkhan',
    '',
    'https://apexinnovations.com',
    'https://g.page/r/example-review-aamir'
),
(
    3,
    'https://instagram.com',
    '',
    'https://linkedin.com/in/priyapatel',
    '',
    'https://apexinnovations.com',
    'https://g.page/r/example-review-priya'
)
ON DUPLICATE KEY UPDATE `linkedin_url` = VALUES(`linkedin_url`);

-- 4. Initial QR code records
INSERT INTO `qr_codes` (`employee_id`, `qr_url`, `png_path`, `svg_path`, `branded_png_path`)
VALUES
(1, 'http://127.0.0.1:5000/q/rahul', 'uploads/qr/rahul.png', 'uploads/qr/rahul.svg', 'uploads/qr/rahul_branded.png'),
(2, 'http://127.0.0.1:5000/q/aamir', 'uploads/qr/aamir.png', 'uploads/qr/aamir.svg', 'uploads/qr/aamir_branded.png'),
(3, 'http://127.0.0.1:5000/q/priya', 'uploads/qr/priya.png', 'uploads/qr/priya.svg', 'uploads/qr/priya_branded.png')
ON DUPLICATE KEY UPDATE `qr_url` = VALUES(`qr_url`);
