# Data Dictionary
## MoMo SMS Data Processing System Database

### Team: CodeCrafters
**Date:** September 19, 2025  
**Database Version:** 1.0.0  
**Database Engine:** MySQL 8.0+  

---

## Table of Contents
1. [Database Overview](#database-overview)
2. [Table Definitions](#table-definitions)
3. [Relationships and Constraints](#relationships-and-constraints)
4. [Indexes and Performance](#indexes-and-performance)
5. [Sample Queries](#sample-queries)
6. [Security Rules](#security-rules)

---

## Database Overview

The MoMo SMS database (`momo_sms_db`) is designed to efficiently store and process mobile money transaction data extracted from SMS messages. The database follows Third Normal Form (3NF) principles while maintaining performance optimization through strategic denormalization where necessary.

### Database Configuration
- **Character Set:** utf8mb4
- **Collation:** utf8mb4_unicode_ci
- **Engine:** InnoDB (all tables)
- **Timezone Support:** Yes (all timestamps with timezone awareness)

---

## Table Definitions

### 1. users
**Purpose:** Stores mobile money user/customer information

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| user_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for each user |
| phone_number | VARCHAR(20) | NOT NULL, UNIQUE | Mobile number in normalized format (+250XXXXXXXXX) |
| full_name | VARCHAR(255) | NOT NULL | Complete user name |
| account_status | ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED') | NOT NULL, DEFAULT 'ACTIVE' | Current account status |
| registration_date | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Account creation date |
| last_activity_date | TIMESTAMP | NULL | Latest transaction timestamp |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE | Last modification timestamp |

**Constraints:**
- `chk_phone_format`: Phone number must match pattern `^[+]?[0-9]{10,15}$`
- `chk_registration_date`: Registration date cannot be in the future

**Indexes:**
- `idx_phone_number` (phone_number)
- `idx_account_status` (account_status)
- `idx_last_activity` (last_activity_date)
- `idx_created_at` (created_at)

---

### 2. transaction_categories
**Purpose:** Categorizes different types of mobile money operations

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| category_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique category identifier |
| category_name | VARCHAR(100) | NOT NULL, UNIQUE | Human-readable category name |
| category_code | VARCHAR(20) | NOT NULL, UNIQUE | Short code for API usage |
| description | TEXT | NULL | Detailed category description |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether category is currently used |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Category creation timestamp |

**Constraints:**
- `chk_category_code_format`: Category code must match pattern `^[A-Z_]{2,20}$`

**Indexes:**
- `idx_category_code` (category_code)
- `idx_is_active` (is_active)

**Predefined Categories:**
- `TRANSFER` - Money Transfer
- `PAYMENT` - Mobile Payment
- `DEPOSIT` - Cash Deposit
- `WITHDRAW` - Cash Withdrawal
- `BILL_PAY` - Bill Payment
- `AIRTIME` - Airtime Purchase
- `LOAN_DISB` - Loan Disbursement
- `LOAN_REPAY` - Loan Repayment

---

### 3. transactions
**Purpose:** Main transaction records with all transaction details

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| transaction_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique transaction identifier |
| sender_user_id | INT | NULL, FK to users(user_id) | Reference to sending user |
| receiver_user_id | INT | NULL, FK to users(user_id) | Reference to receiving user |
| category_id | INT | NOT NULL, FK to transaction_categories(category_id) | Reference to transaction category |
| amount | DECIMAL(15,2) | NOT NULL | Transaction amount with precision |
| currency_code | CHAR(3) | NOT NULL, DEFAULT 'RWF' | Currency code (ISO 4217) |
| transaction_date | TIMESTAMP | NOT NULL | When transaction occurred |
| status | ENUM('SUCCESS', 'FAILED', 'PENDING', 'CANCELLED') | NOT NULL, DEFAULT 'PENDING' | Transaction status |
| reference_number | VARCHAR(50) | UNIQUE, NULL | External system reference |
| description | TEXT | NULL | Transaction description from SMS |
| fee_amount | DECIMAL(10,2) | NULL, DEFAULT 0.00 | Associated transaction fee |
| balance_before | DECIMAL(15,2) | NULL | Account balance before transaction |
| balance_after | DECIMAL(15,2) | NULL | Account balance after transaction |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| processed_at | TIMESTAMP | NULL | When system processed the record |

**Constraints:**
- `chk_amount_positive`: Amount must be > 0
- `chk_fee_non_negative`: Fee amount must be >= 0
- `chk_different_users`: Sender and receiver cannot be the same (unless one is NULL)
- `chk_currency_code`: Currency code must match pattern `^[A-Z]{3}$`
- `chk_transaction_date`: Transaction date cannot be in the future
- `chk_processed_after_created`: Processed date must be >= created date

**Foreign Keys:**
- `fk_transactions_sender`: sender_user_id → users(user_id) ON DELETE SET NULL
- `fk_transactions_receiver`: receiver_user_id → users(user_id) ON DELETE SET NULL
- `fk_transactions_category`: category_id → transaction_categories(category_id) ON DELETE RESTRICT

**Indexes:**
- `idx_sender_user` (sender_user_id)
- `idx_receiver_user` (receiver_user_id)
- `idx_category` (category_id)
- `idx_transaction_date` (transaction_date)
- `idx_status` (status)
- `idx_amount` (amount)
- `idx_composite_user_date` (sender_user_id, transaction_date)
- `idx_composite_status_date` (status, transaction_date)

---

### 4. system_logs
**Purpose:** Tracks data processing activities and system events

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| log_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique log entry identifier |
| log_level | ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') | NOT NULL | Log severity level |
| log_source | VARCHAR(100) | NOT NULL | System component generating log |
| message | TEXT | NOT NULL | Log message content |
| transaction_id | INT | NULL, FK to transactions(transaction_id) | Associated transaction if applicable |
| processing_batch_id | VARCHAR(50) | NULL | Groups related processing activities |
| timestamp | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When log entry was created |
| additional_data | JSON | NULL | Extra context in JSON format |

**Foreign Keys:**
- `fk_system_logs_transaction`: transaction_id → transactions(transaction_id) ON DELETE SET NULL

**Indexes:**
- `idx_log_level` (log_level)
- `idx_log_source` (log_source)
- `idx_timestamp` (timestamp)
- `idx_processing_batch` (processing_batch_id)
- `idx_transaction_logs` (transaction_id)
- `idx_json_batch_id` (JSON extract of batch_id from additional_data)

---

### 5. user_transaction_roles
**Purpose:** Many-to-many relationship resolution between users and transactions

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| role_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique role assignment identifier |
| user_id | INT | NOT NULL, FK to users(user_id) | Reference to user |
| transaction_id | INT | NOT NULL, FK to transactions(transaction_id) | Reference to transaction |
| role_type | ENUM('SENDER', 'RECEIVER', 'AGENT', 'MERCHANT') | NOT NULL | User role in transaction |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Role assignment timestamp |

**Constraints:**
- `uk_user_transaction_role`: UNIQUE(user_id, transaction_id, role_type)

**Foreign Keys:**
- `fk_user_roles_user`: user_id → users(user_id) ON DELETE CASCADE
- `fk_user_roles_transaction`: transaction_id → transactions(transaction_id) ON DELETE CASCADE

**Indexes:**
- `idx_user_roles` (user_id)
- `idx_transaction_roles` (transaction_id)
- `idx_role_type` (role_type)

---

### 6. transaction_tags
**Purpose:** Flexible tagging system for transaction classification

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| tag_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique tag identifier |
| tag_name | VARCHAR(50) | NOT NULL, UNIQUE | Tag name for classification |
| description | TEXT | NULL | Tag description |
| is_system_generated | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether tag is auto-generated |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Tag creation timestamp |

**Indexes:**
- `idx_tag_name` (tag_name)
- `idx_is_system_generated` (is_system_generated)

**Predefined Tags:**
- `high-value` - Transactions above 100,000 RWF
- `weekend` - Transactions occurring on weekends
- `agent-transaction` - Transactions involving agents
- `recurring` - Regular recurring transactions
- `failed-retry` - Retry of previously failed transaction

---

### 7. transaction_tag_assignments
**Purpose:** Many-to-many junction table for transaction tags

| Column | Data Type | Constraints | Description |
|--------|-----------|-------------|-------------|
| assignment_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique assignment identifier |
| transaction_id | INT | NOT NULL, FK to transactions(transaction_id) | Reference to transaction |
| tag_id | INT | NOT NULL, FK to transaction_tags(tag_id) | Reference to tag |
| assigned_by | VARCHAR(100) | NOT NULL, DEFAULT 'SYSTEM' | Who assigned the tag |
| assigned_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Assignment timestamp |

**Constraints:**
- `uk_transaction_tag`: UNIQUE(transaction_id, tag_id)

**Foreign Keys:**
- `fk_tag_assignments_transaction`: transaction_id → transactions(transaction_id) ON DELETE CASCADE
- `fk_tag_assignments_tag`: tag_id → transaction_tags(tag_id) ON DELETE CASCADE

**Indexes:**
- `idx_assignment_transaction` (transaction_id)
- `idx_assignment_tag` (tag_id)
- `idx_assigned_by` (assigned_by)

---

## Views

### v_transaction_details
Complete transaction information with all related entities joined.

```sql
CREATE VIEW v_transaction_details AS
SELECT 
    t.transaction_id, t.reference_number, t.amount, t.currency_code,
    t.fee_amount, t.transaction_date, t.status, t.description,
    s.full_name AS sender_name, s.phone_number AS sender_phone,
    r.full_name AS receiver_name, r.phone_number AS receiver_phone,
    c.category_name, c.category_code, t.created_at, t.processed_at
FROM transactions t
LEFT JOIN users s ON t.sender_user_id = s.user_id
LEFT JOIN users r ON t.receiver_user_id = r.user_id
JOIN transaction_categories c ON t.category_id = c.category_id;
```

### v_user_transaction_summary
User transaction summary with aggregated statistics.

```sql
CREATE VIEW v_user_transaction_summary AS
SELECT 
    u.user_id, u.phone_number, u.full_name,
    COUNT(DISTINCT CASE WHEN t.sender_user_id = u.user_id THEN t.transaction_id END) AS sent_count,
    COUNT(DISTINCT CASE WHEN t.receiver_user_id = u.user_id THEN t.transaction_id END) AS received_count,
    COALESCE(SUM(CASE WHEN t.sender_user_id = u.user_id THEN t.amount END), 0) AS total_sent,
    COALESCE(SUM(CASE WHEN t.receiver_user_id = u.user_id THEN t.amount END), 0) AS total_received,
    MAX(t.transaction_date) AS last_transaction_date
FROM users u
LEFT JOIN transactions t ON (u.user_id = t.sender_user_id OR u.user_id = t.receiver_user_id)
GROUP BY u.user_id, u.phone_number, u.full_name;
```

---

## Sample Queries

### 1. Basic Transaction Queries

```sql
-- Find all transactions for a specific user
SELECT * FROM v_transaction_details 
WHERE sender_phone = '+250788123456' OR receiver_phone = '+250788123456'
ORDER BY transaction_date DESC;

-- Get successful transactions in the last 30 days
SELECT transaction_id, amount, sender_name, receiver_name, category_name, transaction_date
FROM v_transaction_details 
WHERE status = 'SUCCESS' 
AND transaction_date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
ORDER BY transaction_date DESC;
```

### 2. Analytics Queries

```sql
-- Daily transaction volume by category
SELECT 
    DATE(transaction_date) as date,
    category_name,
    COUNT(*) as transaction_count,
    SUM(amount) as total_volume,
    AVG(amount) as avg_amount
FROM v_transaction_details
WHERE transaction_date >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)
GROUP BY DATE(transaction_date), category_name
ORDER BY date DESC, total_volume DESC;

-- Top 10 users by transaction volume
SELECT 
    sender_name as user_name,
    sender_phone as phone_number,
    COUNT(*) as transaction_count,
    SUM(amount) as total_sent,
    AVG(amount) as avg_transaction
FROM v_transaction_details
WHERE sender_name IS NOT NULL
AND status = 'SUCCESS'
GROUP BY sender_name, sender_phone
ORDER BY total_sent DESC
LIMIT 10;
```

### 3. System Monitoring Queries

```sql
-- Error analysis for the last 24 hours
SELECT 
    log_level,
    log_source,
    COUNT(*) as error_count,
    MIN(timestamp) as first_occurrence,
    MAX(timestamp) as last_occurrence
FROM system_logs
WHERE log_level IN ('ERROR', 'CRITICAL')
AND timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY log_level, log_source
ORDER BY error_count DESC;

-- Transaction processing performance
SELECT 
    processing_batch_id,
    COUNT(*) as transaction_count,
    MIN(created_at) as batch_start,
    MAX(processed_at) as batch_end,
    AVG(TIMESTAMPDIFF(SECOND, created_at, processed_at)) as avg_processing_time_seconds
FROM transactions
WHERE processed_at IS NOT NULL
AND processing_batch_id IS NOT NULL
GROUP BY processing_batch_id
ORDER BY batch_start DESC
LIMIT 10;
```

### 4. Business Intelligence Queries

```sql
-- Monthly growth analysis
SELECT 
    YEAR(transaction_date) as year,
    MONTH(transaction_date) as month,
    COUNT(*) as transaction_count,
    SUM(amount) as total_volume,
    COUNT(DISTINCT sender_user_id) as unique_senders,
    COUNT(DISTINCT receiver_user_id) as unique_receivers
FROM transactions
WHERE status = 'SUCCESS'
GROUP BY YEAR(transaction_date), MONTH(transaction_date)
ORDER BY year DESC, month DESC;

-- High-value transactions analysis
SELECT 
    t.transaction_id,
    t.amount,
    t.transaction_date,
    t.status,
    s.full_name as sender_name,
    r.full_name as receiver_name,
    c.category_name,
    GROUP_CONCAT(tg.tag_name) as tags
FROM transactions t
LEFT JOIN users s ON t.sender_user_id = s.user_id
LEFT JOIN users r ON t.receiver_user_id = r.user_id
JOIN transaction_categories c ON t.category_id = c.category_id
LEFT JOIN transaction_tag_assignments tta ON t.transaction_id = tta.transaction_id
LEFT JOIN transaction_tags tg ON tta.tag_id = tg.tag_id
WHERE t.amount >= 100000
GROUP BY t.transaction_id
ORDER BY t.amount DESC;
```

---

## Security Rules and Constraints

### 1. Data Access Control
- **Application User** (`momo_app`): Limited SELECT, INSERT, UPDATE permissions
- **Read-Only User** (`momo_readonly`): SELECT permissions only
- **Admin Access**: Full database privileges (restricted to database administrators)

### 2. Data Integrity Rules
1. **Phone Number Validation**: Must follow international format with country code
2. **Amount Validation**: All monetary amounts must be positive
3. **Date Validation**: Transaction dates cannot be in the future
4. **Reference Integrity**: All foreign key relationships are enforced
5. **Unique Constraints**: Prevent duplicate phone numbers and reference numbers

### 3. Audit and Compliance
- **Complete Audit Trail**: All transactions maintain creation and modification timestamps
- **System Logging**: All processing activities are logged with appropriate detail
- **Data Retention**: System logs are automatically archived after 90 days
- **Error Tracking**: All processing errors are captured with context

### 4. Performance Security
- **Index Strategy**: All frequently queried columns are indexed
- **Query Optimization**: Complex queries use appropriate indexes and views
- **Connection Limits**: Database connections are pooled and limited
- **Memory Management**: Large result sets use pagination

### 5. Business Logic Constraints
- **Transaction Consistency**: Sender and receiver cannot be the same user
- **Status Workflow**: Transaction status follows defined workflow (PENDING → SUCCESS/FAILED/CANCELLED)
- **Category Validation**: All transactions must have valid categories
- **Role Assignment**: Users can have multiple roles per transaction

---

## Maintenance and Monitoring

### Automated Maintenance Tasks
1. **Log Archival**: Old system logs are automatically deleted after 90 days
2. **Index Optimization**: Database statistics are updated regularly
3. **Performance Monitoring**: Query performance is tracked and optimized

### Manual Monitoring Points
1. **Transaction Volume**: Monitor daily transaction volumes for anomalies
2. **Error Rates**: Track error rates and processing failures
3. **Performance Metrics**: Monitor query execution times and resource usage
4. **Data Quality**: Regular validation of data integrity and consistency

### Backup and Recovery
1. **Daily Backups**: Full database backups are performed daily
2. **Transaction Log Backups**: Continuous transaction log backups for point-in-time recovery
3. **Disaster Recovery**: Hot standby database for immediate failover
4. **Data Validation**: Regular checks of backup integrity and restoration procedures