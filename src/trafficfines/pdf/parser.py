# pdf/parser.py
import os
try:
    from icecream import ic
except ImportError:
    # Fallback if icecream is not installed
    def ic(*args, **kwargs):
        pass

from trafficfines.utils.logger import get_logger
from trafficfines.utils.error_messages import ErrorMessageMapper
from trafficfines.pdf.field_config import get_field_mapping_config
from trafficfines.pdf.parsing_strategies import MultiStrategyParser
from trafficfines.pdf.validator import FineDataValidator, validate_fine_data
from typing import Dict, List, Tuple

logger = get_logger(__name__)


class PDFParser:
    """
    Enhanced PDF parser with multiple parsing strategies, configuration-based
    field mapping, and comprehensive data validation.
    """
    
    def __init__(self, jurisdiction: str = 'brazil', strict_validation: bool = False):
        """
        Initialize PDF parser.
        
        Args:
            jurisdiction: Jurisdiction name for field mapping (default: 'brazil')
            strict_validation: If True, warnings are treated as errors in validation
        """
        self.jurisdiction = jurisdiction
        self.strict_validation = strict_validation
        self.field_config = get_field_mapping_config()
        self.multi_strategy_parser = MultiStrategyParser()
        self.validator = FineDataValidator()
        
        # Set jurisdiction in config
        if not self.field_config.set_jurisdiction(jurisdiction):
            logger.warning(f"Jurisdiction '{jurisdiction}' not found, using default 'brazil'")
            self.jurisdiction = 'brazil'
    
    def parse_pdf(self, pdf_path: str, validate: bool = True) -> dict:
        """
        Extract relevant data from traffic fine PDF using multiple strategies.
        
        Args:
            pdf_path: Path to PDF file
            validate: If True, validate extracted data
        
        Returns:
            Dictionary with extracted fine data or None if parsing fails
        """
        try:
            logger.info(f"Parsing PDF: {pdf_path}")
            ic(f"Parsing PDF: {pdf_path}")
            
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Use multi-strategy parser (Solution A)
            fine_data = self.multi_strategy_parser.parse(pdf_path, self.jurisdiction)
            
            if not fine_data:
                raise ValueError("Could not extract fine number from PDF - file may not be a valid traffic fine document")
            
            ic(fine_data)
            
            # Validate extracted data (Solution C)
            if validate:
                is_valid, errors, warnings = validate_fine_data(fine_data, strict=self.strict_validation)
                
                if errors:
                    error_msg = f"Validation errors: {', '.join(errors)}"
                    logger.warning(f"{error_msg} for {pdf_path}")
                    # Log each error
                    for error in errors:
                        logger.warning(f"  - {error}")
                
                if warnings:
                    logger.info(f"Validation warnings for {pdf_path}:")
                    for warning in warnings:
                        logger.info(f"  - {warning}")
                
                if not is_valid:
                    logger.error(f"Data validation failed for {pdf_path}")
                    # Still return data, but log the issues
                    # In strict mode, we might want to return None here
            
            logger.info(f"Successfully parsed PDF: {pdf_path} (fine_number: {fine_data.get('fine_number')})")
            ic(f"Successfully parsed PDF: {pdf_path}")
            return fine_data
            
        except FileNotFoundError as e:
            logger.error(ErrorMessageMapper.get_log_message(e, {'pdf_path': pdf_path}), exc_info=True)
            return None
        except ValueError as e:
            logger.error(ErrorMessageMapper.get_log_message(e, {'pdf_path': pdf_path}), exc_info=True)
            return None
        except Exception as e:
            logger.error(ErrorMessageMapper.get_log_message(e, {'pdf_path': pdf_path}), exc_info=True)
            return None

    def scan_folder_for_pdfs(self, folder_path):
        """Scan a folder for PDF files and process them"""
        from trafficfines.db.models import FineModel
        
        fine_model = FineModel()
        processed_files = []
        errors = []
        
        logger.info(f"Scanning folder for PDFs: {folder_path}")
        ic(f"Scanning folder for PDFs: {folder_path}")

        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(folder_path, filename)
                logger.info(f"Processing file: {filename}")
                ic(f"Processing file: {filename}")
                fine_data = self.parse_pdf(pdf_path)
                
                if fine_data and fine_data['fine_number']:
                    try:
                        ic(f"Attempting to save fine data: {fine_data}")  # Log the data being saved
                        if fine_model.save_fine(fine_data):
                            processed_files.append(filename)
                            logger.info(f"Saved fine data for: {filename}")
                            ic(f"Saved fine data for: {filename}")
                        else:
                            error_msg = f"Failed to save {filename} to database"
                            errors.append(error_msg)
                            logger.error(error_msg)
                            ic(error_msg)
                    except Exception as e:
                        error_msg = f"Exception while saving {filename}: {e}"
                        errors.append(error_msg)
                        logger.error(ErrorMessageMapper.get_log_message(e, {'filename': filename}), exc_info=True)
                        ic(error_msg)
                else:
                    error_msg = f"Failed to parse {filename}"
                    errors.append(error_msg)
                    logger.warning(f"Failed to parse {filename} - no fine number extracted")
                    ic(error_msg)
        
        logger.info(f"Scan complete. Processed: {len(processed_files)}, Errors: {len(errors)}")
        ic(f"Scan complete. Processed: {len(processed_files)}, Errors: {len(errors)}")
        return {
            'processed': processed_files,
            'errors': errors
        }

    def validate_fine_data(self, fine_data: dict, strict: bool = None) -> Tuple[bool, List[str], List[str]]:
        """
        Validate fine data using comprehensive validation layer.
        
        Args:
            fine_data: Dictionary containing extracted fine data
            strict: If True, warnings are treated as errors. If None, uses instance default.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        if strict is None:
            strict = self.strict_validation
        
        return validate_fine_data(fine_data, strict=strict)
    
    def set_jurisdiction(self, jurisdiction: str) -> bool:
        """
        Change jurisdiction for field mapping.
        
        Args:
            jurisdiction: Jurisdiction name
        
        Returns:
            True if jurisdiction was set successfully
        """
        if self.field_config.set_jurisdiction(jurisdiction):
            self.jurisdiction = jurisdiction
            logger.info(f"Changed jurisdiction to: {jurisdiction}")
            return True
        return False
    
    def get_available_jurisdictions(self) -> list:
        """
        Get list of available jurisdictions.
        
        Returns:
            List of jurisdiction names
        """
        return self.field_config.list_jurisdictions()