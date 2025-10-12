CREATE DATABASE IF NOT EXISTS gojek_clone;
USE gojek_clone;

-- --------------------------------------------------------
-- Table: user
-- --------------------------------------------------------
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role ENUM('user', 'driver', 'admin') DEFAULT 'user',
    password VARCHAR(255) NOT NULL,
    address TEXT
);

-- --------------------------------------------------------
-- Table: balance
-- --------------------------------------------------------
CREATE TABLE balance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    handphone_number VARCHAR(20) UNIQUE,
    balance DECIMAL(12,2) DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- --------------------------------------------------------
-- Table: top_up
-- --------------------------------------------------------
CREATE TABLE top_up (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- --------------------------------------------------------
-- Table: transfer
-- --------------------------------------------------------
CREATE TABLE transfer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    handphone_number VARCHAR(20) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- --------------------------------------------------------
-- Table: orders_driver
-- --------------------------------------------------------
CREATE TABLE orders_driver (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pickup VARCHAR(255),
    destination VARCHAR(255),
    total DECIMAL(12,2),
    status ENUM('pending', 'confirmed', 'rejected', 'completed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- --------------------------------------------------------
-- Table: payment
-- --------------------------------------------------------
CREATE TABLE payment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    driver_id INT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES user(id) ON DELETE CASCADE
);
