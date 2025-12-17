# db/models.py
from trafficfines.db.database import DatabaseManager
from trafficfines.utils.logger import get_logger

logger = get_logger(__name__)

class FineModel:
    def __init__(self):
        self.db = DatabaseManager()
    
    def save_fine(self, fine_data):
        """Save or update fine data in database"""
        try:
            fine_number = fine_data.get('fine_number', 'Unknown')
            logger.debug(f"Attempting to save fine: {fine_number}")
            
            self.db.cursor.execute('''
            INSERT OR REPLACE INTO fines 
            (fine_number, notification_date, defense_due_date, driver_id_due_date,
             license_plate, vehicle_model, violation_location, violation_date,
             violation_time, violation_code, amount, description, measured_speed,
             considered_speed, speed_limit, owner_name, owner_document, pdf_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fine_data['fine_number'],
                fine_data['notification_date'],
                fine_data['defense_due_date'],
                fine_data['driver_id_due_date'],
                fine_data['license_plate'],
                fine_data['vehicle_model'],
                fine_data['violation_location'],
                fine_data['violation_date'],
                fine_data['violation_time'],
                fine_data['violation_code'],
                fine_data['amount'],
                fine_data['description'],
                fine_data['measured_speed'],
                fine_data['considered_speed'],
                fine_data['speed_limit'],
                fine_data['owner_name'],
                fine_data['owner_document'],
                fine_data['pdf_path']
            ))
            self.db.conn.commit()
            logger.info(f"Successfully saved fine to database: {fine_number}")
            return True
        except Exception as e:
            fine_number = fine_data.get('fine_number', 'Unknown')
            logger.error(
                f"Error saving fine to database (fine_number={fine_number}): {e}",
                exc_info=True
            )
            return False
    
    def get_all_fines(self):
        """Retrieve all fines from database"""
        self.db.cursor.execute('''
        SELECT fine_number, notification_date, defense_due_date, driver_id_due_date,
               license_plate, vehicle_model, violation_location, violation_date,
               violation_time, violation_code, amount, description, measured_speed,
               considered_speed, speed_limit, owner_name, owner_document, pdf_path,
               payment_event_created, driver_id_event_created
        FROM fines ORDER BY violation_date DESC
        ''')
        return self.db.cursor.fetchall()
    
    def get_fines_without_payment_events(self):
        """Retrieve fines without payment events"""
        self.db.cursor.execute('''
        SELECT id, fine_number, defense_due_date, amount
        FROM fines 
        WHERE payment_event_created = 0 AND defense_due_date IS NOT NULL
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