# pdf/parser.py
import fitz  # PyMuPDF
import os
import logging
from icecream import ic
from utils.helpers import parse_date

FIELD_MAP = {
    "IDENTIFICAÇÃO DO AUTO DE INFRAÇÃO (Número do AIT)": "fine_number",
    "DATA DA NOTIFICAÇÃO DA AUTUAÇÃO": "notification_date",
    "DATA LIMITE PARA INTERPOSIÇÃO DE DEFESA PRÉVIA": "defense_due_date",
    "DATA LIMITE PARA IDENTIFICAÇÃO DO CONDUTOR INFRATOR": "driver_id_due_date",
    "PLACA": "license_plate",
    "MARCA/MODELO/VERSÃO": "vehicle_model",
    "LOCAL DA INFRAÇÃO": "violation_location",
    "DATA": "violation_date",
    "HORA": "violation_time",
    "CÓDIGO DA INFRAÇÃO": "violation_code",
    "VALOR DA MULTA": "amount",
    "DESCRIÇÃO DA INFRAÇÃO": "description",
    "MEDIÇÃO REALIZADA": "measured_speed",
    "VALOR CONSIDERADO": "considered_speed",
    "LIMITE REGULAMENTADO": "speed_limit",
    "NOME DO PROPRIETÁRIO": "owner_name",
    "CPF/CNPJ": "owner_document"
}

class PDFParser:
    def parse_pdf(self, pdf_path):
        """Extract relevant data from traffic fine PDF"""
        fine_data = {
            'fine_number': None,              # IDENTIFICAÇÃO DO AUTO DE INFRAÇÃO
            'notification_date': None,        # DATA DA NOTIFICAÇÃO DA AUTUAÇÃO
            'defense_due_date': None,         # DATA LIMITE PARA INTERPOSIÇÃO DE DEFESA PRÉVIA
            'driver_id_due_date': None,       # DATA LIMITE PARA IDENTIFICAÇÃO DO CONDUTOR INFRATOR
            'license_plate': None,            # PLACA
            'vehicle_model': None,            # MARCA/MODELO/VERSÃO
            'violation_location': None,       # LOCAL DA INFRAÇÃO
            'violation_date': None,           # DATA
            'violation_time': None,           # HORA
            'violation_code': None,           # CÓDIGO DA INFRAÇÃO
            'amount': 0.0,                    # VALOR DA MULTA
            'description': None,              # DESCRIÇÃO DA INFRAÇÃO
            'measured_speed': None,           # MEDIÇÃO REALIZADA
            'considered_speed': None,         # VALOR CONSIDERADO
            'speed_limit': None,              # LIMITE REGULAMENTADO
            'owner_name': None,               # NOME DO PROPRIETÁRIO
            'owner_document': None,           # CPF/CNPJ
            'pdf_path': pdf_path
        }
        
        try:
            logging.info(f"Parsing PDF: {pdf_path}")
            ic(f"Parsing PDF: {pdf_path}")
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            
            # Split text into lines and clean up
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            ic(lines)  # See what lines are being parsed
            
            # Create a dictionary of field-value pairs
            field_value_pairs = {}
            current_field = None
            
            for line in lines:
                # Detect field header
                for pdf_field, canonical_key in FIELD_MAP.items():
                    if line.startswith(pdf_field):
                        current_field = canonical_key
                        field_value_pairs[current_field] = []
                        break
                else:
                    if current_field and not field_value_pairs[current_field]:
                        # Only take the first value after the field header
                        field_value_pairs[current_field].append(line)
            
            ic(field_value_pairs)
            
            # Process the extracted fields
            for key, values in field_value_pairs.items():
                value = values[0] if values else ''
                if key in ["notification_date", "defense_due_date", "driver_id_due_date", "violation_date"]:
                    fine_data[key] = parse_date(value)
                elif key == "amount":
                    amount_str = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
                    fine_data[key] = float(amount_str)
                else:
                    fine_data[key] = value
            
            ic(fine_data)
            
            logging.info(f"Successfully parsed PDF: {pdf_path}")
            ic(f"Successfully parsed PDF: {pdf_path}")
            return fine_data
            
        except Exception as e:
            logging.error(f"Error parsing PDF {pdf_path}: {e}", exc_info=True)
            ic(f"Error parsing PDF {pdf_path}: {e}")
            return None

    def scan_folder_for_pdfs(self, folder_path):
        """Scan a folder for PDF files and process them"""
        from db.models import FineModel
        
        fine_model = FineModel()
        processed_files = []
        errors = []
        
        logging.info(f"Scanning folder for PDFs: {folder_path}")
        ic(f"Scanning folder for PDFs: {folder_path}")

        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(folder_path, filename)
                logging.info(f"Processing file: {filename}")
                ic(f"Processing file: {filename}")
                fine_data = self.parse_pdf(pdf_path)
                
                if fine_data and fine_data['fine_number']:
                    try:
                        ic(f"Attempting to save fine data: {fine_data}")  # Log the data being saved
                        if fine_model.save_fine(fine_data):
                            processed_files.append(filename)
                            logging.info(f"Saved fine data for: {filename}")
                            ic(f"Saved fine data for: {filename}")
                        else:
                            error_msg = f"Failed to save {filename} to database"
                            errors.append(error_msg)
                            logging.error(error_msg)
                            ic(error_msg)
                    except Exception as e:
                        error_msg = f"Exception while saving {filename}: {e}"
                        errors.append(error_msg)
                        logging.error(error_msg, exc_info=True)
                        ic(error_msg)
                else:
                    error_msg = f"Failed to parse {filename}"
                    errors.append(error_msg)
                    logging.error(error_msg)
                    ic(error_msg)
        
        logging.info(f"Scan complete. Processed: {len(processed_files)}, Errors: {len(errors)}")
        ic(f"Scan complete. Processed: {len(processed_files)}, Errors: {len(errors)}")
        return {
            'processed': processed_files,
            'errors': errors
        }

    def validate_fine_data(self, fine_data):
        required = ['fine_number', 'license_plate', 'violation_date']
        missing = [field for field in required if not fine_data.get(field)]
        if missing:
            ic(f"Missing required fields: {missing}")
            logging.warning(f"Missing required fields: {missing}")
            return False
        return True