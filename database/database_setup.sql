-- ================================================================
-- MoMo SMS Data Processing System - Database Setup Script
-- Team: CodeCrafters
-- Created: September 19, 2025
-- Database: MySQL 8.0+
-- ================================================================

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS momo_sms_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE momo_sms_db;

-- ================================================================
-- SECTION 1: DROP EXISTING TABLES (for clean setup)
-- ================================================================
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS transaction_tag_assignments;
DROP TABLE IF EXISTS transaction_tags;
DROP TABLE IF EXISTS user_transaction_roles;
DROP TABLE IF EXISTS system_logs;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS transaction_categories;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

-- ================================================================
-- SECTION 2: CREATE CORE TABLES WITH CONSTRAINTS
-- ================================================================

-- Users table: Stores mobile money user information
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Unique identifier for each user',
    phone_number VARCHAR(20) NOT NULL UNIQUE COMMENT 'Mobile number in normalized format',
    full_name VARCHAR(255) NOT NULL COMMENT 'Complete user name',
    account_status ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED') NOT NULL DEFAULT 'ACTIVE' COMMENT 'Current account status',
    registration_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Account creation date',
    last_activity_date TIMESTAMP NULL COMMENT 'Latest transaction timestamp',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last modification timestamp',
    
    -- Constraints
    CONSTRAINT chk_phone_format CHECK (phone_number REGEXP '^[+]?[0-9]{10,15}$'),
    CONSTRAINT chk_registration_date CHECK (registration_date <= CURRENT_TIMESTAMP),
    INDEX idx_phone_number (phone_number),
    INDEX idx_account_status (account_status),
    INDEX idx_last_activity (last_activity_date),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB COMMENT='Mobile money user information';

-- Transaction Categories table: Categorizes transaction types
CREATE TABLE transaction_categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Unique category identifier',
    category_name VARCHAR(100) NOT NULL UNIQUE COMMENT 'Human-readable category name',
    category_code VARCHAR(20) NOT NULL UNIQUE COMMENT 'Short code for API usage',
    description TEXT COMMENT 'Detailed category description',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Whether category is currently used',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Category creation timestamp',
    
    -- Constraints  
    CONSTRAINT chk_category_code_format CHECK (category_code REGEXP '^[A-Z_]{2,20}$'),
    INDEX idx_category_code (category_code),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB COMMENT='Transaction type categories';

-- Transactions table: Main transaction records
CREATE TABLE transactions (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Unique transaction identifier',
    sender_user_id INT NULL COMMENT 'Reference to sending user',
    receiver_user_id INT NULL COMMENT 'Reference to receiving user',
    category_id INT NOT NULL COMMENT 'Reference to transaction category',
    amount DECIMAL(15,2) NOT NULL COMMENT 'Transaction amount with precision',
    currency_code CHAR(3) NOT NULL DEFAULT 'RWF' COMMENT 'Currency code (ISO 4217)',
    transaction_date TIMESTAMP NOT NULL COMMENT 'When transaction occurred',
    status ENUM('SUCCESS', 'FAILED', 'PENDING', 'CANCELLED') NOT NULL DEFAULT 'PENDING' COMMENT 'Transaction status',
    reference_number VARCHAR(50) UNIQUE NULL COMMENT 'External system reference',
    description TEXT COMMENT 'Transaction description from SMS',
    fee_amount DECIMAL(10,2) NULL DEFAULT 0.00 COMMENT 'Associated transaction fee',
    balance_before DECIMAL(15,2) NULL COMMENT 'Account balance before transaction',
    balance_after DECIMAL(15,2) NULL COMMENT 'Account balance after transaction',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
    processed_at TIMESTAMP NULL COMMENT 'When system processed the record',
    
    -- Foreign key constraints
    CONSTRAINT fk_transactions_sender FOREIGN KEY (sender_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    CONSTRAINT fk_transactions_receiver FOREIGN KEY (receiver_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    CONSTRAINT fk_transactions_category FOREIGN KEY (category_id) REFERENCES transaction_categories(category_id) ON DELETE RESTRICT,
    
    -- Check constraints
    CONSTRAINT chk_amount_positive CHECK (amount > 0),
    CONSTRAINT chk_fee_non_negative CHECK (fee_amount >= 0),
    CONSTRAINT chk_different_users CHECK (sender_user_id != receiver_user_id OR (sender_user_id IS NULL OR receiver_user_id IS NULL)),
    CONSTRAINT chk_currency_code CHECK (currency_code REGEXP '^[A-Z]{3}$'),
    CONSTRAINT chk_transaction_date CHECK (transaction_date <= CURRENT_TIMESTAMP),
    CONSTRAINT chk_processed_after_created CHECK (processed_at IS NULL OR processed_at >= created_at),
    
    -- Performance indexes
    INDEX idx_sender_user (sender_user_id),
    INDEX idx_receiver_user (receiver_user_id),
    INDEX idx_category (category_id),
    INDEX idx_transaction_date (transaction_date),
    INDEX idx_status (status),
    INDEX idx_amount (amount),
    INDEX idx_reference_number (reference_number),
    INDEX idx_created_at (created_at),
    INDEX idx_processed_at (processed_at),
    INDEX idx_composite_user_date (sender_user_id, transaction_date),
    INDEX idx_composite_status_date (status, transaction_date)
) ENGINE=InnoDB COMMENT='Main transaction records';

-- System Logs table: Tracks data processing activities
CREATE TABLE system_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Unique log entry identifier',
    log_level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL COMMENT 'Log severity level',
    log_source VARCHAR(100) NOT NULL COMMENT 'System component generating log',
    message TEXT NOT NULL COMMENT 'Log message content',
    transaction_id INT NULL COMMENT 'Associated transaction if applicable',
    processing_batch_id VARCHAR(50) NULL COMMENT 'Groups related processing activities',
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'When log entry was created',
    additional_data JSON NULL COMMENT 'Extra context in JSON format',
    
    -- Foreign key constraints
    CONSTRAINT fk_system_logs_transaction FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE SET NULL,
    
    -- Performance indexes
    INDEX idx_log_level (log_level),
    INDEX idx_log_source (log_source),
    INDEX idx_timestamp (timestamp),
    INDEX idx_processing_batch (processing_batch_id),
    INDEX idx_transaction_logs (transaction_id)
) ENGINE=InnoDB COMMENT='System activity and error logs';

-- User Transaction Roles table: Many-to-many relationship resolution
CREATE TABLE user_transaction_roles (
    role_id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Unique role assignment identifier',
    user_id INT NOT NULL COMMENT 'Reference to user',
    transaction_id INT NOT NULL COMMENT 'Reference to transaction',
    role_type ENUM('SENDER', 'RECEIVER', 'AGENT', 'MERCHANT') NOT NULL COMMENT 'User role in transaction',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Role assignment timestamp',
    
    -- Foreign key constraints
    CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_transaction FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    
    -- Unique constraint to prevent duplicate role assignments
    CONSTRAINT uk_user_transaction_role UNIQUE (user_id, transaction_id, role_type),
    
    -- Performance indexes
    INDEX idx_user_roles (user_id),
    INDEX idx_transaction_roles (transaction_id),
    INDEX idx_role_type (role_type)
) ENGINE=InnoDB COMMENT='User roles in transactions';

-- Transaction Tags table: Flexible tagging system
CREATE TABLE transaction_tags (
    tag_id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Unique tag identifier',
    tag_name VARCHAR(50) NOT NULL UNIQUE COMMENT 'Tag name for classification',
    description TEXT COMMENT 'Tag description',
    is_system_generated BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Whether tag is auto-generated',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Tag creation timestamp',
    
    -- Performance indexes
    INDEX idx_tag_name (tag_name),
    INDEX idx_is_system_generated (is_system_generated)
) ENGINE=InnoDB COMMENT='Flexible transaction tags';

-- Transaction Tag Assignments table: Many-to-many junction
CREATE TABLE transaction_tag_assignments (
    assignment_id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Unique assignment identifier',
    transaction_id INT NOT NULL COMMENT 'Reference to transaction',
    tag_id INT NOT NULL COMMENT 'Reference to tag',
    assigned_by VARCHAR(100) NOT NULL DEFAULT 'SYSTEM' COMMENT 'Who assigned the tag',
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Assignment timestamp',
    
    -- Foreign key constraints
    CONSTRAINT fk_tag_assignments_transaction FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    CONSTRAINT fk_tag_assignments_tag FOREIGN KEY (tag_id) REFERENCES transaction_tags(tag_id) ON DELETE CASCADE,
    
    -- Unique constraint to prevent duplicate assignments
    CONSTRAINT uk_transaction_tag UNIQUE (transaction_id, tag_id),
    
    -- Performance indexes
    INDEX idx_assignment_transaction (transaction_id),
    INDEX idx_assignment_tag (tag_id),
    INDEX idx_assigned_by (assigned_by)
) ENGINE=InnoDB COMMENT='Transaction tag assignments';

-- ================================================================
-- SECTION 3: VIEWS FOR COMMON QUERIES
-- ================================================================

-- View for complete transaction information
CREATE VIEW v_transaction_details AS
SELECT 
    t.transaction_id,
    t.reference_number,
    t.amount,
    t.currency_code,
    t.fee_amount,
    t.transaction_date,
    t.status,
    t.description,
    s.full_name AS sender_name,
    s.phone_number AS sender_phone,
    r.full_name AS receiver_name,
    r.phone_number AS receiver_phone,
    c.category_name,
    c.category_code,
    t.created_at,
    t.processed_at
FROM transactions t
LEFT JOIN users s ON t.sender_user_id = s.user_id
LEFT JOIN users r ON t.receiver_user_id = r.user_id
JOIN transaction_categories c ON t.category_id = c.category_id;

-- View for user transaction summary
CREATE VIEW v_user_transaction_summary AS
SELECT 
    u.user_id,
    u.phone_number,
    u.full_name,
    COUNT(DISTINCT CASE WHEN t.sender_user_id = u.user_id THEN t.transaction_id END) AS sent_count,
    COUNT(DISTINCT CASE WHEN t.receiver_user_id = u.user_id THEN t.transaction_id END) AS received_count,
    COALESCE(SUM(CASE WHEN t.sender_user_id = u.user_id THEN t.amount END), 0) AS total_sent,
    COALESCE(SUM(CASE WHEN t.receiver_user_id = u.user_id THEN t.amount END), 0) AS total_received,
    MAX(t.transaction_date) AS last_transaction_date
FROM users u
LEFT JOIN transactions t ON (u.user_id = t.sender_user_id OR u.user_id = t.receiver_user_id)
GROUP BY u.user_id, u.phone_number, u.full_name;

-- ================================================================
-- SECTION 4: SAMPLE DATA INSERTION
-- ================================================================

-- Insert transaction categories
INSERT INTO transaction_categories (category_name, category_code, description) VALUES
('Money Transfer', 'TRANSFER', 'Person to person money transfers'),
('Mobile Payment', 'PAYMENT', 'Payments to merchants and services'),
('Cash Deposit', 'DEPOSIT', 'Deposit cash to mobile money account'),
('Cash Withdrawal', 'WITHDRAW', 'Withdraw cash from mobile money account'),
('Bill Payment', 'BILL_PAY', 'Utility and service bill payments'),
('Airtime Purchase', 'AIRTIME', 'Mobile airtime and data purchases'),
('Loan Disbursement', 'LOAN_DISB', 'Loan amount disbursements'),
('Loan Repayment', 'LOAN_REPAY', 'Loan repayment transactions');

-- Insert sample users  
INSERT INTO users (phone_number, full_name, account_status, registration_date) VALUES
('+250788123456', 'Jean Baptiste Uwimana', 'ACTIVE', '2024-01-15 08:30:00'),
('+250722987654', 'Marie Claire Mukamana', 'ACTIVE', '2024-02-10 14:20:00'),
('+250733456789', 'Emmanuel Nkurunziza', 'ACTIVE', '2024-01-28 11:45:00'),
('+250788654321', 'Grace Ingabire Uwamahoro', 'ACTIVE', '2024-03-05 16:10:00'),
('+250722345678', 'Paul Habimana Nzeyimana', 'ACTIVE', '2024-02-18 09:55:00'),
('+250733789012', 'Immaculee Nyiramana', 'SUSPENDED', '2024-01-20 13:30:00'),
('+250788987654', 'Daniel Rugambwa Nsabimana', 'ACTIVE', '2024-03-12 07:25:00');

-- Insert sample transactions
INSERT INTO transactions (
    sender_user_id, receiver_user_id, category_id, amount, transaction_date, 
    status, reference_number, description, fee_amount, balance_before, balance_after
) VALUES
(1, 2, 1, 50000.00, '2024-09-15 10:30:00', 'SUCCESS', 'TXN001', 'Money transfer for school fees', 500.00, 125000.00, 74500.00),
(2, 3, 1, 25000.00, '2024-09-16 14:20:00', 'SUCCESS', 'TXN002', 'Payment for groceries', 250.00, 89750.00, 64500.00),
(1, NULL, 3, 100000.00, '2024-09-14 09:15:00', 'SUCCESS', 'TXN003', 'Cash deposit at agent', 1000.00, 25000.00, 124000.00),
(4, 1, 2, 75000.00, '2024-09-17 16:45:00', 'SUCCESS', 'TXN004', 'Payment for construction materials', 750.00, 180000.00, 104250.00),
(5, NULL, 4, 30000.00, '2024-09-18 11:30:00', 'SUCCESS', 'TXN005', 'Cash withdrawal for daily expenses', 300.00, 95000.00, 64700.00),
(3, 4, 1, 15000.00, '2024-09-19 08:20:00', 'PENDING', 'TXN006', 'Rent payment installment', 150.00, 49350.00, NULL),
(2, NULL, 6, 5000.00, '2024-09-17 20:10:00', 'SUCCESS', 'TXN007', 'Airtime purchase', 0.00, 64750.00, 59750.00);

-- Insert user transaction roles
INSERT INTO user_transaction_roles (user_id, transaction_id, role_type) VALUES
(1, 1, 'SENDER'), (2, 1, 'RECEIVER'),
(2, 2, 'SENDER'), (3, 2, 'RECEIVER'),
(1, 3, 'RECEIVER'), 
(4, 4, 'SENDER'), (1, 4, 'RECEIVER'),
(5, 5, 'SENDER'),
(3, 6, 'SENDER'), (4, 6, 'RECEIVER'),
(2, 7, 'SENDER');

-- Insert sample transaction tags
INSERT INTO transaction_tags (tag_name, description, is_system_generated) VALUES
('high-value', 'Transactions above 100,000 RWF', TRUE),
('weekend', 'Transactions occurring on weekends', TRUE),
('agent-transaction', 'Transactions involving agents', FALSE),
('recurring', 'Regular recurring transactions', FALSE),
('failed-retry', 'Retry of previously failed transaction', TRUE);

-- Insert tag assignments
INSERT INTO transaction_tag_assignments (transaction_id, tag_id, assigned_by) VALUES
(3, 1, 'SYSTEM'), -- high-value deposit
(1, 4, 'USER'), -- recurring school fee payment
(7, 2, 'SYSTEM'); -- weekend airtime purchase

-- Insert sample system logs
INSERT INTO system_logs (log_level, log_source, message, transaction_id, processing_batch_id, additional_data) VALUES
('INFO', 'ETL_PROCESSOR', 'Successfully processed transaction batch', 1, 'BATCH_001', '{"records_processed": 5, "processing_time": "2.3s"}'),
('WARNING', 'VALIDATION_ENGINE', 'Transaction amount exceeds daily limit', 3, 'BATCH_001', '{"limit": 500000, "amount": 100000}'),
('ERROR', 'SMS_PARSER', 'Failed to parse SMS format', NULL, 'BATCH_002', '{"sms_content": "Invalid format", "error": "Missing amount"}'),
('INFO', 'DATABASE_LOADER', 'Batch insertion completed successfully', NULL, 'BATCH_001', '{"inserted_records": 7, "updated_records": 2}'),
('DEBUG', 'CATEGORY_CLASSIFIER', 'Transaction categorized automatically', 2, 'BATCH_001', '{"confidence": 0.95, "category": "TRANSFER"}');

-- ================================================================
-- SECTION 5: STORED PROCEDURES FOR COMMON OPERATIONS
-- ================================================================

DELIMITER //

-- Procedure to get user transaction history
CREATE PROCEDURE GetUserTransactionHistory(IN p_user_id INT, IN p_limit INT)
BEGIN
    SELECT 
        t.transaction_id,
        t.amount,
        t.transaction_date,
        t.status,
        t.description,
        c.category_name,
        CASE 
            WHEN t.sender_user_id = p_user_id THEN 'OUTGOING'
            WHEN t.receiver_user_id = p_user_id THEN 'INCOMING'
            ELSE 'UNKNOWN'
        END AS direction,
        CASE 
            WHEN t.sender_user_id = p_user_id THEN r.full_name
            WHEN t.receiver_user_id = p_user_id THEN s.full_name
            ELSE NULL
        END AS other_party
    FROM transactions t
    LEFT JOIN users s ON t.sender_user_id = s.user_id
    LEFT JOIN users r ON t.receiver_user_id = r.user_id
    JOIN transaction_categories c ON t.category_id = c.category_id
    WHERE t.sender_user_id = p_user_id OR t.receiver_user_id = p_user_id
    ORDER BY t.transaction_date DESC
    LIMIT p_limit;
END //

-- Procedure to calculate daily transaction summary
CREATE PROCEDURE GetDailyTransactionSummary(IN p_date DATE)
BEGIN
    SELECT 
        c.category_name,
        COUNT(*) as transaction_count,
        SUM(t.amount) as total_amount,
        AVG(t.amount) as average_amount,
        SUM(t.fee_amount) as total_fees
    FROM transactions t
    JOIN transaction_categories c ON t.category_id = c.category_id
    WHERE DATE(t.transaction_date) = p_date
        AND t.status = 'SUCCESS'
    GROUP BY c.category_id, c.category_name
    ORDER BY total_amount DESC;
END //

DELIMITER ;

-- ================================================================
-- SECTION 6: TRIGGERS FOR AUDIT AND BUSINESS LOGIC
-- ================================================================

DELIMITER //

-- Trigger to update user last_activity_date
CREATE TRIGGER update_user_activity 
    AFTER UPDATE ON transactions
    FOR EACH ROW
BEGIN
    IF NEW.status = 'SUCCESS' AND OLD.status != 'SUCCESS' THEN
        UPDATE users SET last_activity_date = NEW.processed_at 
        WHERE user_id = NEW.sender_user_id OR user_id = NEW.receiver_user_id;
    END IF;
END //

-- Trigger to automatically tag high-value transactions
CREATE TRIGGER tag_high_value_transactions
    AFTER INSERT ON transactions
    FOR EACH ROW
BEGIN
    IF NEW.amount >= 100000 THEN
        INSERT INTO transaction_tag_assignments (transaction_id, tag_id, assigned_by)
        SELECT NEW.transaction_id, tag_id, 'SYSTEM'
        FROM transaction_tags 
        WHERE tag_name = 'high-value'
        AND NOT EXISTS (
            SELECT 1 FROM transaction_tag_assignments 
            WHERE transaction_id = NEW.transaction_id AND tag_id = transaction_tags.tag_id
        );
    END IF;
END //

DELIMITER ;

-- ================================================================
-- SECTION 7: PERFORMANCE OPTIMIZATION
-- ================================================================

-- Additional composite indexes for complex queries
CREATE INDEX idx_user_status_date ON transactions(sender_user_id, status, transaction_date);
CREATE INDEX idx_amount_date ON transactions(amount DESC, transaction_date DESC);
CREATE INDEX idx_category_status ON transactions(category_id, status);

-- Optimize for JSON queries on system_logs
ALTER TABLE system_logs ADD INDEX idx_json_batch_id ((CAST(additional_data->>'$.batch_id' AS CHAR(50))));

-- ================================================================
-- SECTION 8: SECURITY ENHANCEMENTS  
-- ================================================================

-- Create application user with limited privileges
CREATE USER IF NOT EXISTS 'momo_app'@'%' IDENTIFIED BY 'SecurePassword123!';
GRANT SELECT, INSERT, UPDATE ON momo_sms_db.* TO 'momo_app'@'%';
GRANT DELETE ON momo_sms_db.system_logs TO 'momo_app'@'%';
GRANT EXECUTE ON PROCEDURE momo_sms_db.GetUserTransactionHistory TO 'momo_app'@'%';
GRANT EXECUTE ON PROCEDURE momo_sms_db.GetDailyTransactionSummary TO 'momo_app'@'%';

-- Create read-only user for reporting
CREATE USER IF NOT EXISTS 'momo_readonly'@'%' IDENTIFIED BY 'ReadOnlyPass456!';
GRANT SELECT ON momo_sms_db.* TO 'momo_readonly'@'%';

-- ================================================================
-- SECTION 9: DATABASE MAINTENANCE
-- ================================================================

-- Event to archive old system logs (runs daily)
CREATE EVENT IF NOT EXISTS archive_old_logs
ON SCHEDULE EVERY 1 DAY
DO
    DELETE FROM system_logs 
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL 90 DAY) 
    AND log_level IN ('DEBUG', 'INFO');

-- ================================================================
-- END OF SETUP SCRIPT
-- ================================================================

-- Display setup completion message
SELECT 'MoMo SMS Database Setup Completed Successfully!' AS status,
       COUNT(*) AS total_tables
FROM information_schema.tables 
WHERE table_schema = 'momo_sms_db';

-- Display sample data counts
SELECT 'Sample Data Summary' AS info;
SELECT 'Users' AS table_name, COUNT(*) AS record_count FROM users
UNION ALL
SELECT 'Transaction Categories', COUNT(*) FROM transaction_categories
UNION ALL  
SELECT 'Transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'System Logs', COUNT(*) FROM system_logs
UNION ALL
SELECT 'User Transaction Roles', COUNT(*) FROM user_transaction_roles
UNION ALL
SELECT 'Transaction Tags', COUNT(*) FROM transaction_tags
UNION ALL
SELECT 'Tag Assignments', COUNT(*) FROM transaction_tag_assignments;