# db/models.py
from db.database import DatabaseManager

class FineModel:
    def __init__(self):
        self.db = DatabaseManager()
    
    def save_fine(self, fine_data):
        """Save or update fine data in database"""
        try:
            self.db.cursor.execute('''
            INSERT OR REPLACE INTO fines 
            (fine_number, issue_date, due_date, amount, violation_type, 
             license_plate, driver_id_due_date, description, violation_location,
             violation_time, person_name, equipment_number, agent_id, pdf_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fine_data['fine_number'],
                fine_data['issue_date'],
                fine_data['due_date'],
                fine_data['amount'],
                fine_data['violation_type'],
                fine_data['license_plate'],
                fine_data['driver_id_due_date'],
                fine_data['description'],
                fine_data.get('violation_location'),  
                fine_data.get('violation_time'),     
                fine_data.get('person_name'),        
                fine_data.get('equipment_number'),   
                fine_data.get('agent_id'),           
                fine_data['pdf_path']
            ))
            self.db.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving fine to database: {e}")
            return False
    
    def get_all_fines(self):
        """Retrieve all fines from database"""
        self.db.cursor.execute('''
        SELECT fine_number, issue_date, due_date, amount, violation_type, 
               license_plate, driver_id_due_date, description, violation_location,
               violation_time, person_name, equipment_number, agent_id, pdf_path, 
               payment_event_created, driver_id_event_created
        FROM fines ORDER BY due_date DESC
        ''')
        return self.db.cursor.fetchall()
    
    def get_fines_without_payment_events(self):
        """Retrieve fines without payment events"""
        self.db.cursor.execute('''
        SELECT id, fine_number, due_date, amount
        FROM fines 
        WHERE payment_event_created = 0 AND due_date IS NOT NULL
        ''')
        return self.db.cursor.fetchall()
    
    def get_fines_without_driver_id_events(self):
        """Retrieve fines without driver ID events"""
        self.db.cursor.execute('''
        SELECT id, fine_number, driver_id_due_date
        FROM fines 
        WHERE driver_id_event_created = 0 AND driver_id_due_date IS NOT NULL
        ''')
        return self.db.cursor.fetchall()
    
    def mark_payment_event_created(self, fine_id):
        """Mark payment event as created for a fine"""
        self.db.cursor.execute('''
        UPDATE fines SET payment_event_created = 1 WHERE id = ?
        ''', (fine_id,))
        self.db.conn.commit()
    
    def mark_driver_id_event_created(self, fine_id):
        """Mark driver ID event as created for a fine"""
        self.db.cursor.execute('''
        UPDATE fines SET driver_id_event_created = 1 WHERE id = ?
        ''', (fine_id,))
        self.db.conn.commit()
    
    def get_fine_by_number(self, fine_number):
        """Retrieve a fine by its number"""
        self.db.cursor.execute('''
        SELECT * FROM fines WHERE fine_number = ?
        ''', (fine_number,))
        return self.db.cursor.fetchone()