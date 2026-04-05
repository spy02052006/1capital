#!/usr/bin/env python3
"""
Load correct employee hierarchy with 3 managers:
- Nitin Mude (Leader)
  - Harshal Ghatage (Manager)
  - Suhas Tare (Manager)
  - Abhijeet Mane (Manager)
"""

import sqlite3
from pathlib import Path

# Correct employee hierarchy based on QUICK_START.md
correct_employees = [
    # ID, Name, Manager_ID, Wire_Code
    (1, 'Nitin Mude', None, 'F338Y01'),  # Leader - top
    
    # 3 Managers reporting to Nitin
    (2, 'Harshal Ghatage', 1, 'F338Y02'),
    (3, 'Suhas Tare', 1, 'F338Y03'),
    (4, 'Abhijeet Mane', 1, 'F338Y04'),
    
    # RMs reporting to Harshal Ghatage
    (5, 'Avishek Kumar', 2, 'F338Y12'),
    (6, 'Rohit Patokar', 2, 'F338Y14'),
    (7, 'Ganesh Shankar', 2, 'F338Y15'),
    (8, 'Rakesh Bhamare', 2, 'F338Y13'),
    (9, 'Harshal Bavaskar', 2, 'FY746'),
    
    # RMs reporting to Suhas Tare
    (10, 'Devashish Upadhyaya', 3, 'F338Y10'),
    (11, 'Amit Nawale', 3, 'F338Y07'),
    (12, 'Amol Patekar', 3, 'F338Y09'),
    (13, 'Abhay Aouti', 3, 'F338Y08'),
    
    # RMs reporting to Abhijeet Mane
    (14, 'Anil Gavali', 4, 'F338Y06'),
    (15, 'Ramakrishnan S', 4, 'F338Y11'),
    (16, 'Satish Saxena', 4, 'F338Y16'),
]

def load_employees():
    """Load correct employee data into database"""
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
        
        # Insert correct employee hierarchy
        for emp_id, name, manager_id, wire_code in correct_employees:
            cursor.execute("""
                INSERT INTO employee_dimension 
                (id, wire_code, rm_name, manager_id, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, datetime('now'), datetime('now'))
            """, (emp_id, wire_code, name, manager_id))
        
        conn.commit()
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM employee_dimension")
        total = cursor.fetchone()[0]
        print(f"✓ Employees loaded: {total}")
        
        # Show hierarchy
        print("\n✓ Correct Hierarchy Structure:")
        print("  Nitin Mude (ID=1) [LEADER]")
        print("  ├─ Harshal Ghatage (ID=2) [MANAGER]")
        print("  │  ├─ Avishek Kumar (ID=5)")
        print("  │  ├─ Rohit Patokar (ID=6)")
        print("  │  ├─ Ganesh Shankar (ID=7)")
        print("  │  ├─ Rakesh Bhamare (ID=8)")
        print("  │  └─ Harshal Bavaskar (ID=9)")
        print("  ├─ Suhas Tare (ID=3) [MANAGER]")
        print("  │  ├─ Devashish Upadhyaya (ID=10)")
        print("  │  ├─ Amit Nawale (ID=11)")
        print("  │  ├─ Amol Patekar (ID=12)")
        print("  │  └─ Abhay Aouti (ID=13)")
        print("  └─ Abhijeet Mane (ID=4) [MANAGER]")
        print("     ├─ Anil Gavali (ID=14)")
        print("     ├─ Ramakrishnan S (ID=15)")
        print("     └─ Satish Saxena (ID=16)")
        
        # Verify managers
        print("\n✓ Managers (show in dropdown):")
        cursor.execute("""
            SELECT e.id, e.rm_name 
            FROM employee_dimension e
            WHERE e.id IN (
                SELECT DISTINCT manager_id FROM employee_dimension 
                WHERE manager_id IS NOT NULL
            )
            ORDER BY e.id
        """)
        for emp_id, name in cursor.fetchall():
            print(f"  {emp_id}. {name}")
        
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
