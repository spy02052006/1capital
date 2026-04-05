#!/usr/bin/env python3
"""
Load CORRECT employee hierarchy with only 3 managers:
- Suhas Tare
- Abhijeet Mane  
- Harshal Ghatage

All reporting to Nitin Mude (Leader)
"""

import sqlite3
from pathlib import Path

# Correct employee data based on actual organization
employee_data = [
    # ID, Name, Manager_ID, Wire_Code
    (1, 'Nitin Mude', None, 'F338Y01'),  # Top Leader
    
    # === 3 MANAGERS ===
    (2, 'Harshal Ghatage', 1, 'F338Y02'),      # Manager under Nitin
    (3, 'Suhas Tare', 1, 'F338Y03'),           # Manager under Nitin
    (4, 'Abhijeet Mane', 1, 'F338Y04'),        # Manager under Nitin
    
    # === HARSHAL GHATAGE'S TEAM ===
    (5, 'Avishek Kumar', 2, 'F338Y12'),
    (6, 'Rohit Patokar', 2, 'F338Y14'),
    (7, 'Ganesh Shankar', 2, 'F338Y15'),
    (8, 'Rakesh Bhamare', 2, 'F338Y13'),
    (9, 'Harshal Bavaskar', 2, 'FY746'),
    
    # === SUHAS TARE'S TEAM ===
    (10, 'Devashish Upadhyaya', 3, 'F338Y10'),
    (11, 'Amit Nawale', 3, 'F338Y07'),
    (12, 'Amol Patekar', 3, 'F338Y09'),
    (13, 'Abhay Aouti', 3, 'F338Y08'),
    
    # === ABHIJEET MANE'S TEAM ===
    (14, 'Anil Gavali', 4, 'F338Y06'),
    (15, 'Dhananjay Yadav', 4, 'F338Y05'),
    (16, 'Ramakrishnan S', 4, 'F338Y11'),
]

def load_employees():
    db_path = Path('/var/www/SalesDashboardProject/SalesDashboard/db.sqlite3')
    
    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Clear existing data
        cursor.execute("DELETE FROM employee_dimension")
        print("✓ Cleared existing employee records")
        
        # Insert correct data
        for emp_id, name, manager_id, wire_code in employee_data:
            cursor.execute("""
                INSERT INTO employee_dimension 
                (id, wire_code, rm_name, manager_id, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, datetime('now'), datetime('now'))
            """, (emp_id, wire_code, name, manager_id))
        
        conn.commit()
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM employee_dimension")
        total = cursor.fetchone()[0]
        print(f"✓ Loaded {total} employees")
        
        # Show hierarchy
        print("\n=== CORRECT HIERARCHY ===")
        print("Nitin Mude (Leader - ID=1)")
        
        for mgr_id, mgr_name, _, _ in employee_data[1:4]:
            print(f"  ├─ {mgr_name} (Manager - ID={mgr_id})")
            subordinates = [row for row in employee_data if row[2] == mgr_id and mgr_id != 1]
            for emp_id, emp_name, _, wire in subordinates:
                print(f"  │  ├─ {emp_name} ({wire})")
        
        # Show managers only
        print("\n=== MANAGERS (for dropdown) ===")
        cursor.execute("""
            SELECT id, rm_name FROM employee_dimension
            WHERE id IN (SELECT DISTINCT manager_id FROM employee_dimension WHERE manager_id IS NOT NULL)
            ORDER BY rm_name
        """)
        managers = cursor.fetchall()
        print(f"Count: {len(managers)}")
        for emp_id, name in managers:
            print(f"  - {name}")
        
        print("\n✅ Employee data loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    load_employees()
