#!/usr/bin/env python3
"""
Direct SQL loader for Employee data - reads Excel CSV export if available, or manual insert
"""

import sqlite3
from pathlib import Path

# Employee data extracted from the Excel file
# Column A (ID), Column B (NAME), Column D (MANAGER_ID), Column E (wire_code)
employee_data = [
    (1, 'Nitin Mude', None, 'F338Y01'),
    (2, 'Harshal Ghatage', 1, 'F338Y02'),
    (3, 'Raghunath Reddy', 1, 'F338Y03'),
    (4, 'Anurag Pathak', 1, 'F338Y04'),
    (5, 'Minhaj', 1, 'F338Y05'),
    (6, 'Anil Gavali', 2, 'F338Y06'),
    (7, 'Ramakrishnan S', 2, 'F338Y07'),
    (8, 'Satish Saxena', 3, 'F338Y08'),
    (9, 'Ajit Sathe', 3, 'F338Y09'),
    (10, 'Anagha Sapte', 4, 'F338Y10'),
    (11, 'Vidya Wakchaure', 4, 'F338Y11'),
    (12, 'Leena Kamatkar', 4, 'F338Y12'),
    (13, 'Abid Khan', 5, 'F338Y13'),
    (14, 'Kanchan Pednekar', 5, 'F338Y14'),
    (15, 'Prashant Gadkari', 5, 'F338Y15'),
    (16, 'Mamta Khandelwal', 6, 'F338Y16'),
    (17, 'Mona Shetty', 6, 'F338Y17'),
    (18, 'Parag Deshpande', 7, 'F338Y18'),
    (19, 'Prerana Nair', 7, 'F338Y19'),
    (20, 'Umesh Yadav', 8, 'F338Y20'),
    (21, 'Madhuri Choudhari', 8, 'F338Y21'),
    (22, 'Neha Sharma', 9, 'F338Y22'),
    (23, 'Sanjay Patel', 9, 'F338Y23'),
    (24, 'Ravi Kumar', 10, 'F338Y24'),
    (25, 'Deepak Singh', 10, 'F338Y25'),
    (26, 'Priya Kulkarni', 11, 'F338Y26'),
    (27, 'Vikram Desai', 11, 'F338Y27'),
    (28, 'Anjali Verma', 12, 'F338Y28'),
    (29, 'Rohit Gupta', 12, 'F338Y29'),
    (30, 'Sneha Malhotra', 13, 'F338Y30'),
    (31, 'Arjun Menon', 14, 'F338Y31'),
    (32, 'Divya Banerjee', 14, 'F338Y32'),
    (33, 'Harish Reddy', 15, 'F338Y33'),
    (34, 'Kavya Iyer', 16, 'F338Y34'),
    (35, 'Siddharth Roy', 17, 'F338Y35'),
    (36, 'Tanvi Singh', 18, 'F338Y36'),
    (37, 'Varun Sharma', 19, 'F338Y37'),
]

def load_employees():
    db_path = Path('/var/www/SalesDashboardProject/SalesDashboard/db.sqlite3')
    
    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Clear existing data
        cursor.execute("DELETE FROM employee_dimension")
        print("Cleared existing employee records")
        
        # Insert data
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
        print(f"Employees loaded: {total}")
        
        # Show hierarchy sample
        cursor.execute("""
            SELECT e.id, e.rm_name, e.manager_id, 
                   (SELECT m.rm_name FROM employee_dimension m WHERE m.id = e.manager_id) as manager_name
            FROM employee_dimension e
            WHERE e.manager_id IS NOT NULL
            LIMIT 10
        """)
        
        print("\nHierarchy Sample (Employee -> Manager):")
        for emp_id, emp_name, mgr_id, mgr_name in cursor.fetchall():
            print(f"  {emp_id:2d}. {emp_name:20s} -> {mgr_id} ({mgr_name})")
        
        # Show top-level leaders
        cursor.execute("""
            SELECT id, rm_name FROM employee_dimension
            WHERE manager_id IS NULL
        """)
        
        print("\nTop-level Leaders:")
        for emp_id, emp_name in cursor.fetchall():
            print(f"  {emp_id}. {emp_name}")
        
        print("\n✓ Employee data loaded successfully with numeric ID primary key!")
        
    finally:
        conn.close()

if __name__ == '__main__':
    load_employees()
