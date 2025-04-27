# pdf/parser.py
import fitz  # PyMuPDF
import re
import os
from utils.helpers import parse_date, extract_with_regex

class PDFParser:
    def parse_pdf(self, pdf_path):
        """Extract relevant data from traffic fine PDF"""
        fine_data = {
            'fine_number': None,
            'issue_date': None,
            'due_date': None,
            'amount': 0.0,
            'violation_type': None,
            'license_plate': None,
            'driver_id_due_date': None,
            'description': None,
            'pdf_path': pdf_path
        }
        
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            
            # Extract fine number
            fine_data['fine_number'] = extract_with_regex(text, r'Fine Number:\s*([A-Za-z0-9-]+)')
            
            # Extract amount
            amount_str = extract_with_regex(text, r'Amount:\s*\$?(\d+\.\d{2})')
            if amount_str:
                fine_data['amount'] = float(amount_str)
            
            # Extract dates
            issue_date_str = extract_with_regex(text, r'Issue Date:\s*(\d{2}/\d{2}/\d{4})')
            fine_data['issue_date'] = parse_date(issue_date_str)
            
            due_date_str = extract_with_regex(text, r'Payment Due:\s*(\d{2}/\d{2}/\d{4})')
            fine_data['due_date'] = parse_date(due_date_str)
            
            driver_id_due_str = extract_with_regex(text, r'Driver ID Due:\s*(\d{2}/\d{2}/\d{4})')
            fine_data['driver_id_due_date'] = parse_date(driver_id_due_str)
            
            # Extract other fields
            fine_data['violation_type'] = extract_with_regex(text, r'Violation Type:\s*(.+?)(?=\n)')
            fine_data['license_plate'] = extract_with_regex(text, r'License Plate:\s*([A-Z0-9]+)')
            fine_data['description'] = extract_with_regex(text, r'Description:\s*(.+?)(?=\n)')
            
            return fine_data
            
        except Exception as e:
            print(f"Error parsing PDF {pdf_path}: {e}")
            return None
    
    def scan_folder_for_pdfs(self, folder_path):
        """Scan a folder for PDF files and process them"""
        from db.models import FineModel
        
        fine_model = FineModel()
        processed_files = []
        errors = []
        
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(folder_path, filename)
                fine_data = self.parse_pdf(pdf_path)
                
                if fine_data and fine_data['fine_number']:
                    if fine_model.save_fine(fine_data):
                        processed_files.append(filename)
                    else:
                        errors.append(f"Failed to save {filename} to database")
                else:
                    errors.append(f"Failed to parse {filename}")
        
        return {
            'processed': processed_files,
            'errors': errors
        }
