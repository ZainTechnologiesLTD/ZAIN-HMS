#!/usr/bin/env python3
"""
Fix Laboratory Tables Script
Creates missing laboratory tables in the database
"""
import os
import sys
import django
import sqlite3

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

def create_laboratory_tables():
    """Create missing laboratory tables"""
    
    # Connect to database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    print("🔧 Creating laboratory tables...")
    
    try:
        # Create TestCategory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laboratory_testcategory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create LabTest table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laboratory_labtest (
                id VARCHAR(36) PRIMARY KEY,
                test_code VARCHAR(20) UNIQUE,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                category_id INTEGER DEFAULT 1,
                sample_type VARCHAR(20) DEFAULT 'BLOOD',
                normal_range TEXT,
                unit VARCHAR(50),
                price DECIMAL(10,2) DEFAULT 0.00,
                turnaround_time INTEGER DEFAULT 24,
                preparation_instructions TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES laboratory_testcategory (id)
            )
        ''')
        
        # Create LabTestOrder table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laboratory_labtestorder (
                id VARCHAR(36) PRIMARY KEY,
                order_number VARCHAR(20) UNIQUE,
                patient_id VARCHAR(36),
                doctor_id VARCHAR(36),
                order_date DATE,
                status VARCHAR(20) DEFAULT 'PENDING',
                priority VARCHAR(20) DEFAULT 'NORMAL',
                notes TEXT,
                created_by_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create LabTestResult table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laboratory_labtestresult (
                id VARCHAR(36) PRIMARY KEY,
                order_id VARCHAR(36),
                test_id VARCHAR(36),
                result_value TEXT,
                reference_range VARCHAR(100),
                unit VARCHAR(50),
                status VARCHAR(20) DEFAULT 'PENDING',
                is_abnormal BOOLEAN DEFAULT 0,
                comments TEXT,
                tested_by_id INTEGER,
                verified_by_id INTEGER,
                tested_at TIMESTAMP,
                verified_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES laboratory_labtestorder (id),
                FOREIGN KEY (test_id) REFERENCES laboratory_labtest (id)
            )
        ''')
        
        # Insert default test category
        cursor.execute('''
            INSERT OR IGNORE INTO laboratory_testcategory (id, name, description, is_active)
            VALUES (1, 'General', 'General laboratory tests', 1)
        ''')
        
        # Insert some sample lab tests
        sample_tests = [
            ('b8a7c4d5-e6f7-8901-2345-6789abcdef01', 'CBC001', 'Complete Blood Count', 'Basic blood test', 1, 'BLOOD', '4.5-11.0 x10³/µL', 'x10³/µL', 25.00, 24),
            ('b8a7c4d5-e6f7-8901-2345-6789abcdef02', 'GLU001', 'Blood Glucose', 'Fasting blood glucose', 1, 'BLOOD', '70-100 mg/dL', 'mg/dL', 15.00, 6),
            ('b8a7c4d5-e6f7-8901-2345-6789abcdef03', 'UR001', 'Urinalysis', 'Complete urine analysis', 1, 'URINE', 'Various', 'Various', 20.00, 12),
        ]
        
        for test in sample_tests:
            cursor.execute('''
                INSERT OR IGNORE INTO laboratory_labtest 
                (id, test_code, name, description, category_id, sample_type, normal_range, unit, price, turnaround_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', test)
        
        conn.commit()
        print("✅ Laboratory tables created successfully!")
        
        # Check what tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'laboratory_%'")
        tables = cursor.fetchall()
        print("📋 Created tables:", [table[0] for table in tables])
        
        # Check if records exist
        cursor.execute("SELECT COUNT(*) FROM laboratory_labtest")
        test_count = cursor.fetchone()[0]
        print(f"📊 Lab tests available: {test_count}")
        
    except Exception as e:
        print(f"❌ Error creating laboratory tables: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    create_laboratory_tables()
