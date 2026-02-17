-- FarmIntel Database Schema
-- Database: farm_intel (create manually: CREATE DATABASE farm_intel;)
-- Run this after creating database. Use with XAMPP MySQL.

USE farm_intel;

-- Users: both Admin and Farmer
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role ENUM('admin', 'farmer') NOT NULL,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    mobile VARCHAR(15) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    -- Farmer-specific
    village VARCHAR(100) DEFAULT NULL,
    taluka VARCHAR(100) DEFAULT NULL,
    district VARCHAR(100) DEFAULT NULL,
    land_area DECIMAL(10,2) DEFAULT NULL COMMENT 'in Acre',
    soil_type VARCHAR(50) DEFAULT NULL,
    water_availability VARCHAR(50) DEFAULT NULL,
    -- Admin-specific
    admin_role VARCHAR(50) DEFAULT NULL COMMENT 'Super Admin / Data Manager',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crops (Admin managed)
CREATE TABLE IF NOT EXISTS crops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category ENUM('Spices', 'Vegetables', 'Pulses', 'Oil Seeds', 'Fruits') NOT NULL,
    image_paths TEXT COMMENT 'JSON array of image paths',
    duration VARCHAR(100) DEFAULT NULL,
    average_price DECIMAL(12,2) DEFAULT NULL,
    market_price DECIMAL(12,2) DEFAULT NULL,
    pesticides_name TEXT,
    best_seeds_name TEXT,
    fertilizer_name TEXT,
    season ENUM('Kharif', 'Rabi', 'Zaid', 'All') NOT NULL,
    soil_type VARCHAR(100) DEFAULT NULL,
    india_demand ENUM('Low', 'Medium', 'High') DEFAULT NULL,
    description TEXT,
    active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Government Schemes
CREATE TABLE IF NOT EXISTS schemes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    scheme_type ENUM('Central', 'State') NOT NULL,
    eligible_crop VARCHAR(255) DEFAULT NULL,
    eligibility_criteria TEXT,
    benefits TEXT,
    required_documents TEXT,
    apply_link VARCHAR(500) DEFAULT NULL,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Store Products (Fertilizers, Seeds, Pesticides, Equipment, Tools)
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    image_path VARCHAR(500) DEFAULT NULL,
    category ENUM('Fertilizers', 'Seeds', 'Pesticides', 'Equipment', 'Tools') NOT NULL,
    brand VARCHAR(100) DEFAULT NULL,
    description TEXT,
    price DECIMAL(12,2) NOT NULL,
    discount DECIMAL(5,2) DEFAULT 0,
    stock INT DEFAULT 0,
    usage_crops TEXT COMMENT 'comma or JSON',
    nutrient_composition TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cart (Farmer)
CREATE TABLE IF NOT EXISTS cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY (farmer_id, product_id)
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subtotal DECIMAL(12,2) NOT NULL,
    gst DECIMAL(12,2) DEFAULT 0,
    total DECIMAL(12,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'Completed',
    FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Order Items
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price_per_unit DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Financial Analysis (Farmer)
CREATE TABLE IF NOT EXISTS financial_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    crop_name VARCHAR(150) NOT NULL,
    season VARCHAR(50) DEFAULT NULL,
    seeds_cost DECIMAL(12,2) DEFAULT 0,
    fertilizer_cost DECIMAL(12,2) DEFAULT 0,
    pesticides_cost DECIMAL(12,2) DEFAULT 0,
    irrigation_cost DECIMAL(12,2) DEFAULT 0,
    labour_cost DECIMAL(12,2) DEFAULT 0,
    machinery_cost DECIMAL(12,2) DEFAULT 0,
    other_expenses DECIMAL(12,2) DEFAULT 0,
    total_production DECIMAL(12,2) DEFAULT NULL,
    selling_price DECIMAL(12,2) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_crops_active_category ON crops(active, category);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_orders_farmer ON orders(farmer_id);
CREATE INDEX idx_financial_farmer ON financial_records(farmer_id);
