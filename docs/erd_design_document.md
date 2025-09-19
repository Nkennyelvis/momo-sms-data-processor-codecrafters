# Entity Relationship Diagram (ERD) Design Document
## MoMo SMS Data Processing System

### Team: CodeCrafters
**Date:** September 19, 2025
**Members:** Elvis Kenny Nsengimana Ishema, Lydivine Umutesi Munyampundu, Seth Iradukunda

---

## 1. Executive Summary

This document outlines the database design for our Mobile Money (MoMo) SMS data processing system. The design supports efficient storage, querying, and analysis of mobile money transaction data while maintaining data integrity and supporting future scalability requirements.

## 2. Business Requirements Analysis

Based on our analysis of MoMo SMS data patterns, we identified these key business requirements:

- **Transaction Processing**: Store and track various types of mobile money transactions
- **User Management**: Maintain sender and receiver information with privacy considerations
- **Category Classification**: Organize transactions by type (payment, transfer, deposit, withdrawal)
- **System Monitoring**: Track data processing activities and system performance
- **Audit Trail**: Maintain historical records for compliance and analysis
- **Performance**: Support high-volume transaction processing with efficient queries

## 3. Entity Identification and Design

### 3.1 Core Entities

#### **USERS** (Customer/Account Holder Information)
- **Purpose**: Stores information about mobile money users (senders/receivers)
- **Key Attributes**:
  - `user_id` (PK) - Unique identifier for each user
  - `phone_number` - Mobile number (normalized format)
  - `full_name` - User's complete name
  - `account_status` - Active/Inactive/Suspended
  - `registration_date` - Account creation timestamp
  - `last_activity_date` - Latest transaction timestamp
  - `created_at` - Record creation timestamp
  - `updated_at` - Last modification timestamp

#### **TRANSACTIONS** (Main Transaction Records)
- **Purpose**: Central entity storing all mobile money transaction details
- **Key Attributes**:
  - `transaction_id` (PK) - Unique transaction identifier
  - `sender_user_id` (FK) - Reference to sending user
  - `receiver_user_id` (FK) - Reference to receiving user
  - `category_id` (FK) - Reference to transaction category
  - `amount` - Transaction amount (decimal precision)
  - `currency_code` - Currency (default: RWF)
  - `transaction_date` - When transaction occurred
  - `status` - Success/Failed/Pending/Cancelled
  - `reference_number` - External system reference
  - `description` - Transaction description from SMS
  - `fee_amount` - Associated transaction fee
  - `balance_before` - Account balance before transaction
  - `balance_after` - Account balance after transaction
  - `created_at` - Record creation timestamp
  - `processed_at` - When system processed the record

#### **TRANSACTION_CATEGORIES** (Payment/Transfer Types)
- **Purpose**: Categorizes different types of mobile money operations
- **Key Attributes**:
  - `category_id` (PK) - Unique category identifier
  - `category_name` - Human-readable category name
  - `category_code` - Short code for API usage
  - `description` - Detailed category description
  - `is_active` - Whether category is currently used
  - `created_at` - Category creation timestamp

#### **SYSTEM_LOGS** (Data Processing Tracking)
- **Purpose**: Tracks ETL operations and system activities
- **Key Attributes**:
  - `log_id` (PK) - Unique log entry identifier
  - `log_level` - INFO/WARNING/ERROR/DEBUG
  - `log_source` - System component generating log
  - `message` - Log message content
  - `transaction_id` (FK, nullable) - Associated transaction if applicable
  - `processing_batch_id` - Groups related processing activities
  - `timestamp` - When log entry was created
  - `additional_data` - JSON field for extra context

### 3.2 Junction/Relationship Tables

#### **USER_TRANSACTION_ROLES** (Many-to-Many Resolution)
- **Purpose**: Handles the many-to-many relationship between users and transactions
- **Justification**: A user can be involved in multiple transactions, and a transaction can involve multiple users in different roles
- **Key Attributes**:
  - `role_id` (PK) - Unique role assignment identifier
  - `user_id` (FK) - Reference to user
  - `transaction_id` (FK) - Reference to transaction
  - `role_type` - SENDER/RECEIVER/AGENT/MERCHANT
  - `created_at` - Role assignment timestamp

#### **TRANSACTION_TAGS** (Flexible Classification)
- **Purpose**: Allows flexible tagging system for transactions
- **Key Attributes**:
  - `tag_id` (PK) - Unique tag identifier
  - `tag_name` - Tag name (e.g., 'high-value', 'international', 'recurring')
  - `description` - Tag description
  - `is_system_generated` - Whether tag is auto-generated
  - `created_at` - Tag creation timestamp

#### **TRANSACTION_TAG_ASSIGNMENTS** (Many-to-Many Junction)
- **Purpose**: Links transactions to their assigned tags
- **Key Attributes**:
  - `assignment_id` (PK) - Unique assignment identifier
  - `transaction_id` (FK) - Reference to transaction
  - `tag_id` (FK) - Reference to tag
  - `assigned_by` - System/User who assigned the tag
  - `assigned_at` - Assignment timestamp

## 4. Relationship Analysis

### 4.1 Relationship Cardinalities

1. **USERS ↔ TRANSACTIONS**
   - **Cardinality**: Many-to-Many (M:N)
   - **Implementation**: Through USER_TRANSACTION_ROLES junction table
   - **Rationale**: Users can participate in multiple transactions in different roles

2. **TRANSACTION_CATEGORIES ↔ TRANSACTIONS**
   - **Cardinality**: One-to-Many (1:M)
   - **Implementation**: Direct foreign key in TRANSACTIONS table
   - **Rationale**: Each transaction belongs to exactly one category

3. **TRANSACTIONS ↔ SYSTEM_LOGS**
   - **Cardinality**: One-to-Many (1:M)
   - **Implementation**: Direct foreign key in SYSTEM_LOGS table
   - **Rationale**: One transaction can generate multiple log entries

4. **TRANSACTIONS ↔ TRANSACTION_TAGS**
   - **Cardinality**: Many-to-Many (M:N)
   - **Implementation**: Through TRANSACTION_TAG_ASSIGNMENTS junction table
   - **Rationale**: Transactions can have multiple tags, tags can apply to multiple transactions

## 5. Design Decisions and Rationale

### 5.1 Data Type Choices
- **DECIMAL(15,2)** for monetary amounts - Ensures precision for financial calculations
- **VARCHAR(20)** for phone numbers - Accommodates international formats with country codes
- **TIMESTAMP WITH TIME ZONE** - Handles multi-timezone operations
- **JSON** for additional_data - Provides flexibility for evolving data requirements

### 5.2 Indexing Strategy
- **Primary Keys**: Clustered indexes for efficient lookup
- **Foreign Keys**: Non-clustered indexes for join operations
- **Phone Numbers**: Index for user lookup performance
- **Transaction Dates**: Index for time-based queries and reporting
- **Status Fields**: Index for filtering active/completed transactions

### 5.3 Security and Privacy Considerations
- **Phone Number Hashing**: Option to hash sensitive phone numbers
- **PII Encryption**: Capability to encrypt user names and sensitive data
- **Audit Trail**: Complete transaction history maintenance
- **Role-Based Access**: User roles determine data access levels

### 5.4 Scalability Features
- **Partitioning**: Transaction table can be partitioned by date
- **Archival Strategy**: Old transactions can be moved to archive tables
- **Caching Layer**: Frequently accessed data can be cached
- **Read Replicas**: Support for read-only database replicas

## 6. Data Integrity Constraints

### 6.1 Primary Key Constraints
- All tables have surrogate primary keys using auto-incrementing integers
- Natural keys (like phone numbers) are enforced as unique constraints

### 6.2 Foreign Key Constraints
- All relationships enforced with proper foreign key constraints
- CASCADE and RESTRICT rules defined based on business requirements

### 6.3 Check Constraints
- Transaction amounts must be positive
- Phone numbers must match valid format patterns
- Status fields limited to predefined values
- Dates must be within reasonable ranges

### 6.4 Unique Constraints
- Phone numbers must be unique within user table
- Transaction reference numbers must be unique
- Category codes must be unique

## 7. Sample Queries for Validation

### 7.1 Basic CRUD Operations
```sql
-- Find all transactions for a specific user
SELECT t.*, c.category_name 
FROM TRANSACTIONS t
JOIN TRANSACTION_CATEGORIES c ON t.category_id = c.category_id
WHERE t.sender_user_id = ? OR t.receiver_user_id = ?;

-- Get transaction summary by category
SELECT c.category_name, COUNT(*) as transaction_count, SUM(t.amount) as total_amount
FROM TRANSACTIONS t
JOIN TRANSACTION_CATEGORIES c ON t.category_id = c.category_id
GROUP BY c.category_name;
```

### 7.2 Complex Analytical Queries
```sql
-- Monthly transaction trends
SELECT DATE_FORMAT(transaction_date, '%Y-%m') as month,
       COUNT(*) as transactions,
       AVG(amount) as avg_amount,
       SUM(amount) as total_volume
FROM TRANSACTIONS 
WHERE transaction_date >= DATE_SUB(CURRENT_DATE, INTERVAL 12 MONTH)
GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')
ORDER BY month;
```

## 8. Future Enhancements

### 8.1 Planned Extensions
- **Merchant Management**: Additional entities for merchant account handling
- **Loyalty Programs**: Points and rewards tracking
- **International Transfers**: Multi-currency and exchange rate support
- **Risk Management**: Fraud detection and risk scoring tables
- **API Usage Tracking**: Monitor external API usage patterns

### 8.2 Performance Optimizations
- **Database Sharding**: Horizontal scaling across multiple databases
- **Column Store Indexes**: For analytical workloads
- **Materialized Views**: Pre-computed aggregations for reporting
- **Connection Pooling**: Efficient database connection management

---

## Conclusion

This ERD design provides a robust foundation for the MoMo SMS data processing system while maintaining flexibility for future enhancements. The design emphasizes data integrity, performance, and scalability to support both current requirements and anticipated growth.

**Note**: This design follows standard database normalization principles (3NF) while introducing controlled denormalization where performance benefits justify the trade-offs.