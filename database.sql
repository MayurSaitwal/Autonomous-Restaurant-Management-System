-- Restaurant Management System Database Schema
-- Run: mysql -u root -p < database.sql

CREATE DATABASE IF NOT EXISTS restaurant_db;
USE restaurant_db;

-- ─── Users ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    full_name   VARCHAR(100) NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    phone       VARCHAR(15)  NOT NULL,
    address     VARCHAR(255) NOT NULL,
    username    VARCHAR(50)  NOT NULL UNIQUE,
    password    VARCHAR(64)  NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── Menu ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS menu (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    category    VARCHAR(50)  NOT NULL,
    price       DECIMAL(8,2) NOT NULL,
    description TEXT,
    available   TINYINT(1) DEFAULT 1
);

-- ─── Tables ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tables (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    table_number  INT NOT NULL UNIQUE,
    location      VARCHAR(120) NOT NULL DEFAULT 'Main Hall',
    capacity      INT NOT NULL DEFAULT 4,
    status        ENUM('available','reserved','occupied') DEFAULT 'available',
    reserved_by   INT NULL,
    FOREIGN KEY (reserved_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ─── Orders ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    table_id      INT,
    order_type    ENUM('dine_in','order_home') NOT NULL DEFAULT 'dine_in',
    payment_method VARCHAR(30) NULL,
    note          TEXT NULL,
    status        ENUM('pending','preparing','ready','completed') DEFAULT 'pending',
    total_amount  DECIMAL(10,2) DEFAULT 0.00,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE,
    FOREIGN KEY (table_id) REFERENCES tables(id) ON DELETE SET NULL
);

-- ─── Order Items ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_items (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    order_id    INT NOT NULL,
    menu_id     INT NOT NULL,
    quantity    INT NOT NULL DEFAULT 1,
    unit_price  DECIMAL(8,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_id)  REFERENCES menu(id)   ON DELETE CASCADE
);

-- ─── Seed: Tables ────────────────────────────────────────────────────────────
INSERT INTO tables (table_number, location, capacity) VALUES
(1, 'Main Hall', 2),(2, 'Main Hall', 2),(3, 'Window Side', 4),(4, 'Window Side', 4),(5, 'Family Zone', 4),
(6, 'Family Zone', 6),(7, 'Garden Deck', 6),(8, 'Garden Deck', 8),(9, 'Rooftop', 8),(10, 'Rooftop', 10);

-- ─── Seed: Menu ──────────────────────────────────────────────────────────────
INSERT INTO menu (name, category, price, description) VALUES
-- Starters
('Veg Spring Rolls',     'Starters', 120.00, 'Crispy rolls filled with mixed vegetables'),
('Paneer Tikka',         'Starters', 180.00, 'Grilled cottage cheese with spices'),
('Soup of the Day',      'Starters',  90.00, 'Chef\'s special daily soup'),
('Garlic Bread',         'Starters',  80.00, 'Toasted bread with garlic butter'),
-- Main Course
('Butter Chicken',       'Main Course', 280.00, 'Tender chicken in creamy tomato gravy'),
('Dal Makhani',          'Main Course', 200.00, 'Slow-cooked black lentils in butter'),
('Paneer Butter Masala', 'Main Course', 220.00, 'Cottage cheese in rich tomato gravy'),
('Veg Biryani',          'Main Course', 180.00, 'Aromatic basmati rice with vegetables'),
('Chicken Biryani',      'Main Course', 260.00, 'Fragrant rice with spiced chicken'),
('Fish Curry',           'Main Course', 320.00, 'Fresh fish in coconut-based curry'),
-- Breads
('Butter Naan',          'Breads',  40.00, 'Soft leavened bread with butter'),
('Roti',                 'Breads',  25.00, 'Whole wheat Indian flatbread'),
('Paratha',              'Breads',  50.00, 'Layered flaky wheat bread'),
-- Drinks
('Mango Lassi',          'Drinks',  80.00, 'Sweet yogurt drink with mango'),
('Fresh Lime Soda',      'Drinks',  60.00, 'Refreshing lime with soda water'),
('Masala Chai',          'Drinks',  40.00, 'Spiced Indian tea'),
('Cold Coffee',          'Drinks',  90.00, 'Chilled coffee with ice cream'),
-- Desserts
('Gulab Jamun',          'Desserts',  80.00, 'Soft milk dumplings in sugar syrup'),
('Kheer',                'Desserts',  70.00, 'Creamy rice pudding with nuts'),
('Ice Cream',            'Desserts',  90.00, 'Choice of vanilla, chocolate, mango');
