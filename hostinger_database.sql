-- ==========================================================
-- Employee Digital Profile & QR Review System
-- Production Database Setup for Hostinger phpMyAdmin
-- Database: u121474497_qr
-- Subdomain: https://qr.nexalogictechno.com
-- ==========================================================

-- 1. Admins Table
CREATE TABLE IF NOT EXISTS `admins` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(100) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `name` VARCHAR(150) NOT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Default Administrator (Username: Nexalogic | Password: Nexalogictechno@1026#)
INSERT INTO `admins` (`id`, `username`, `password_hash`, `name`, `is_active`)
VALUES (1, 'Nexalogic', 'scrypt:32768:8:1$BQ9y4vM9ch4DGD65$6436ac3f08e0fb75d4ff80e61cd887352918aab116f6dcdaf292b268fbddf519abc59426738a4fd5259ebc4dfa040fadf5e7d53d20755d4ada1ed040701f7e5c', 'Nexalogic Admin', 1)
ON DUPLICATE KEY UPDATE `username` = VALUES(`username`), `password_hash` = VALUES(`password_hash`), `name` = VALUES(`name`);

-- 2. Employees Table
CREATE TABLE IF NOT EXISTS `employees` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `first_name` VARCHAR(100) NOT NULL,
    `last_name` VARCHAR(100) DEFAULT '',
    `slug` VARCHAR(150) NOT NULL UNIQUE,
    `designation` VARCHAR(150) DEFAULT '',
    `phone` VARCHAR(50) DEFAULT '',
    `whatsapp` VARCHAR(50) DEFAULT '',
    `email` VARCHAR(150) DEFAULT '',
    `profile_image` VARCHAR(255) DEFAULT '',
    `company_logo` VARCHAR(255) DEFAULT '',
    `bio` TEXT,
    `review_categories` TEXT DEFAULT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `is_deleted` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_employee_slug` (`slug`),
    INDEX `idx_employee_active_deleted` (`is_active`, `is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Social Links Table
CREATE TABLE IF NOT EXISTS `social_links` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `employee_id` INT NOT NULL UNIQUE,
    `instagram_url` TEXT,
    `facebook_url` TEXT,
    `linkedin_url` TEXT,
    `youtube_url` TEXT,
    `website_url` TEXT,
    `google_review_url` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_social_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3.1 Custom Dynamic Social Links Table
CREATE TABLE IF NOT EXISTS `custom_social_links` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `employee_id` INT NOT NULL,
    `platform` VARCHAR(50) NOT NULL DEFAULT 'custom',
    `title` VARCHAR(150) NOT NULL,
    `url` TEXT NOT NULL,
    `sort_order` INT NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_custom_links_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE,
    INDEX `idx_custom_links_employee` (`employee_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. QR Codes Table
CREATE TABLE IF NOT EXISTS `qr_codes` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `employee_id` INT NOT NULL UNIQUE,
    `qr_url` VARCHAR(255) NOT NULL,
    `png_path` VARCHAR(255) DEFAULT '',
    `svg_path` VARCHAR(255) DEFAULT '',
    `branded_png_path` VARCHAR(255) DEFAULT '',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_qr_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Analytics Table
CREATE TABLE IF NOT EXISTS `analytics` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `employee_id` INT NOT NULL,
    `event_type` VARCHAR(50) NOT NULL,
    `device_type` VARCHAR(50) DEFAULT 'desktop',
    `referrer` VARCHAR(255) DEFAULT '',
    `ip_address` VARCHAR(100) DEFAULT '',
    `user_agent` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_analytics_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE,
    INDEX `idx_analytics_employee` (`employee_id`),
    INDEX `idx_analytics_event` (`event_type`),
    INDEX `idx_analytics_date` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Settings Table
CREATE TABLE IF NOT EXISTS `settings` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `company_name` VARCHAR(150) NOT NULL DEFAULT 'Nexalogic Techno',
    `company_logo` VARCHAR(255) DEFAULT '',
    `company_phone` VARCHAR(50) DEFAULT '+91 98765 43210',
    `company_email` VARCHAR(150) DEFAULT 'contact@nexalogictechno.com',
    `company_website` VARCHAR(255) DEFAULT 'https://qr.nexalogictechno.com',
    `primary_color` VARCHAR(20) DEFAULT '#4f46e5',
    `secondary_color` VARCHAR(20) DEFAULT '#06b6d4',
    `default_whatsapp_message` VARCHAR(255) DEFAULT 'Hello, I visited your digital profile and would like to connect.',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Visitor Leads Table
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

-- Initial Settings Data
INSERT INTO `settings` (`id`, `company_name`, `company_phone`, `company_email`, `company_website`, `primary_color`, `secondary_color`, `default_whatsapp_message`)
VALUES (1, 'Nexalogic Techno', '+91 98765 43210', 'contact@nexalogictechno.com', 'https://qr.nexalogictechno.com', '#4f46e5', '#06b6d4', 'Hello, I visited your digital profile and would like to connect.')
ON DUPLICATE KEY UPDATE `company_name` = VALUES(`company_name`);

-- Sample Employees Seed
INSERT INTO `employees` (`id`, `first_name`, `last_name`, `slug`, `designation`, `phone`, `whatsapp`, `email`, `bio`, `is_active`, `is_deleted`)
VALUES 
(1, 'Rahul', 'Sharma', 'rahul', 'Senior Sales Executive', '+919876543210', '919876543210', 'rahul@nexalogictechno.com', 'Passionate sales leader helping enterprise clients scale their digital presence.', 1, 0),
(2, 'Aamir', 'Khan', 'aamir', 'Business Operations Manager', '+919811223344', '919811223344', 'aamir@nexalogictechno.com', 'Overseeing strategic growth and operational excellence.', 1, 0),
(3, 'Priya', 'Patel', 'priya', 'Head of People & Talent', '+919844556677', '919844556677', 'priya@nexalogictechno.com', 'Connecting talented professionals with dream opportunities.', 1, 0)
ON DUPLICATE KEY UPDATE `first_name` = VALUES(`first_name`);

-- Sample Social Links
INSERT INTO `social_links` (`employee_id`, `instagram_url`, `facebook_url`, `linkedin_url`, `youtube_url`, `website_url`, `google_review_url`)
VALUES
(1, 'https://instagram.com', 'https://facebook.com', 'https://linkedin.com', 'https://youtube.com', 'https://qr.nexalogictechno.com', 'https://g.page/review-rahul'),
(2, 'https://instagram.com', 'https://facebook.com', 'https://linkedin.com', '', 'https://qr.nexalogictechno.com', 'https://g.page/review-aamir'),
(3, 'https://instagram.com', '', 'https://linkedin.com', '', 'https://qr.nexalogictechno.com', 'https://g.page/review-priya')
ON DUPLICATE KEY UPDATE `employee_id` = VALUES(`employee_id`);
