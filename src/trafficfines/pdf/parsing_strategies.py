"""
Multiple parsing strategies for PDF extraction.

This module implements different parsing strategies with fallback mechanisms
to handle various PDF formats and layouts.
"""
import re
import fitz  # PyMuPDF
from typing import Dict, List, Optional, Any
from trafficfines.utils.logger import get_logger
from trafficfines.utils.helpers import parse_date
from trafficfines.pdf.field_config import get_field_mapping_config

logger = get_logger(__name__)


class ParsingStrategy:
    """Base class for parsing strategies."""
    
    def parse(self, pdf_path: str, text: str, field_mapping: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Parse PDF text using this strategy.
        
        Args:
            pdf_path: Path to PDF file
            text: Extracted text from PDF
            field_mapping: Field mapping dictionary
        
        Returns:
            Dictionary with extracted data or None if parsing fails
        """
        raise NotImplementedError


class StructuredParsingStrategy(ParsingStrategy):
    """
    Structured parsing strategy - assumes fields are followed by values on next line.
    This is the original parsing method.
    """
    
    def parse(self, pdf_path: str, text: str, field_mapping: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse using structured line-by-line approach."""
        try:
            logger.debug(f"Attempting structured parsing for {pdf_path}")
            
            # Initialize result dictionary
            fine_data = self._initialize_fine_data(pdf_path)
            
            # Split text into lines and clean up
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Create a dictionary of field-value pairs
            field_value_pairs = {}
            current_field = None
            
            for line in lines:
                # Detect field header
                for pdf_field, canonical_key in field_mapping.items():
                    if line.startswith(pdf_field):
                        current_field = canonical_key
                        field_value_pairs[current_field] = []
                        break
                else:
                    if current_field and not field_value_pairs.get(current_field):
                        # Only take the first value after the field header
                        field_value_pairs[current_field].append(line)
            
            # Process the extracted fields
            fine_data = self._process_field_values(fine_data, field_value_pairs)
            
            # Check if we got at least the fine number
            if fine_data.get('fine_number'):
                logger.debug(f"Structured parsing successful for {pdf_path}")
                return fine_data
            else:
                logger.debug(f"Structured parsing failed - no fine number extracted")
                return None
                
        except Exception as e:
            logger.warning(f"Structured parsing failed: {e}")
            return None
    
    def _initialize_fine_data(self, pdf_path: str) -> Dict[str, Any]:
        """Initialize fine data dictionary with default values."""
        return {
            'fine_number': None,
            'notification_date': None,
            'defense_due_date': None,
            'driver_id_due_date': None,
            'license_plate': None,
            'vehicle_model': None,
            'violation_location': None,
            'violation_date': None,
            'violation_time': None,
            'violation_code': None,
            'amount': 0.0,
            'description': None,
            'measured_speed': None,
            'considered_speed': None,
            'speed_limit': None,
            'owner_name': None,
            'owner_document': None,
            'pdf_path': pdf_path
        }
    
    def _process_field_values(self, fine_data: Dict[str, Any], field_value_pairs: Dict[str, List[str]]) -> Dict[str, Any]:
        """Process extracted field values and convert to appropriate types."""
        for key, values in field_value_pairs.items():
            value = values[0] if values else ''
            if key in ["notification_date", "defense_due_date", "driver_id_due_date", "violation_date"]:
                fine_data[key] = parse_date(value)
            elif key == "amount":
                try:
                    amount_str = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
                    fine_data[key] = float(amount_str)
                except ValueError:
                    logger.warning(f"Could not parse amount value: {value}")
                    fine_data[key] = 0.0
            else:
                fine_data[key] = value
        
        return fine_data


class RegexParsingStrategy(ParsingStrategy):
    """
    Regex-based parsing strategy - uses regular expressions to find field-value pairs.
    More flexible for different layouts.
    """
    
    def parse(self, pdf_path: str, text: str, field_mapping: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse using regex patterns."""
        try:
            logger.debug(f"Attempting regex parsing for {pdf_path}")
            
            fine_data = self._initialize_fine_data(pdf_path)
            
            # Try to extract fields using regex patterns
            for pdf_field, canonical_key in field_mapping.items():
                # Create regex pattern - field name followed by optional separators and value
                # Pattern: field_name[separators]value
                pattern = rf"{re.escape(pdf_field)}\s*[:\-]?\s*([^\n]+)"
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                
                if match:
                    value = match.group(1).strip()
                    if value:
                        fine_data[canonical_key] = self._convert_value(canonical_key, value)
            
            # Check if we got at least the fine number
            if fine_data.get('fine_number'):
                logger.debug(f"Regex parsing successful for {pdf_path}")
                return fine_data
            else:
                logger.debug(f"Regex parsing failed - no fine number extracted")
                return None
                
        except Exception as e:
            logger.warning(f"Regex parsing failed: {e}")
            return None
    
    def _initialize_fine_data(self, pdf_path: str) -> Dict[str, Any]:
        """Initialize fine data dictionary."""
        return {
            'fine_number': None,
            'notification_date': None,
            'defense_due_date': None,
            'driver_id_due_date': None,
            'license_plate': None,
            'vehicle_model': None,
            'violation_location': None,
            'violation_date': None,
            'violation_time': None,
            'violation_code': None,
            'amount': 0.0,
            'description': None,
            'measured_speed': None,
            'considered_speed': None,
            'speed_limit': None,
            'owner_name': None,
            'owner_document': None,
            'pdf_path': pdf_path
        }
    
    def _convert_value(self, key: str, value: str) -> Any:
        """Convert string value to appropriate type."""
        if key in ["notification_date", "defense_due_date", "driver_id_due_date", "violation_date"]:
            return parse_date(value)
        elif key == "amount":
            try:
                amount_str = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
                return float(amount_str)
            except ValueError:
                return 0.0
        else:
            return value


class TableParsingStrategy(ParsingStrategy):
    """
    Table-based parsing strategy - attempts to extract data from tables.
    Uses PyMuPDF's table extraction capabilities.
    """
    
    def parse(self, pdf_path: str, text: str, field_mapping: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse using table extraction."""
        try:
            logger.debug(f"Attempting table parsing for {pdf_path}")
            
            fine_data = self._initialize_fine_data(pdf_path)
            
            # Open PDF to access table structure
            doc = fitz.open(pdf_path)
            
            # Try to find tables in the PDF
            for page_num, page in enumerate(doc):
                try:
                    # Extract tables from page
                    tables = page.find_tables()
                    
                    if tables:
                        logger.debug(f"Found {len(tables)} tables on page {page_num + 1}")
                        
                        # Process each table
                        for table in tables:
                            table_data = self._extract_table_data(table, field_mapping)
                            if table_data:
                                fine_data.update(table_data)
                        
                        # If we got the fine number, we're done
                        if fine_data.get('fine_number'):
                            doc.close()
                            logger.debug(f"Table parsing successful for {pdf_path}")
                            return fine_data
                
                except Exception as e:
                    logger.debug(f"Error processing page {page_num + 1} for tables: {e}")
                    continue
            
            doc.close()
            
            # If we didn't get fine number, try fallback to text-based table parsing
            fine_data = self._parse_text_table(text, field_mapping, fine_data)
            
            if fine_data.get('fine_number'):
                logger.debug(f"Text-based table parsing successful for {pdf_path}")
                return fine_data
            
            logger.debug(f"Table parsing failed - no fine number extracted")
            return None
            
        except Exception as e:
            logger.warning(f"Table parsing failed: {e}")
            return None
    
    def _initialize_fine_data(self, pdf_path: str) -> Dict[str, Any]:
        """Initialize fine data dictionary."""
        return {
            'fine_number': None,
            'notification_date': None,
            'defense_due_date': None,
            'driver_id_due_date': None,
            'license_plate': None,
            'vehicle_model': None,
            'violation_location': None,
            'violation_date': None,
            'violation_time': None,
            'violation_code': None,
            'amount': 0.0,
            'description': None,
            'measured_speed': None,
            'considered_speed': None,
            'speed_limit': None,
            'owner_name': None,
            'owner_document': None,
            'pdf_path': pdf_path
        }
    
    def _extract_table_data(self, table, field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Extract data from a PyMuPDF table object."""
        data = {}
        
        try:
            # Get table as list of lists
            table_rows = table.extract()
            
            # Look for field-value pairs in table
            for row in table_rows:
                if len(row) >= 2:
                    field_name = str(row[0]).strip() if row[0] else ""
                    field_value = str(row[1]).strip() if len(row) > 1 and row[1] else ""
                    
                    # Check if field name matches any in our mapping
                    for pdf_field, canonical_key in field_mapping.items():
                        if pdf_field.lower() in field_name.lower() or field_name.lower() in pdf_field.lower():
                            if field_value:
                                data[canonical_key] = self._convert_value(canonical_key, field_value)
                            break
        
        except Exception as e:
            logger.debug(f"Error extracting table data: {e}")
        
        return data
    
    def _parse_text_table(self, text: str, field_mapping: Dict[str, str], fine_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback: Parse text that looks like a table (field | value format)."""
        lines = text.split('\n')
        
        for line in lines:
            # Look for patterns like "Field: Value" or "Field | Value"
            for separator in [':', '|', '\t']:
                if separator in line:
                    parts = line.split(separator, 1)
                    if len(parts) == 2:
                        field_name = parts[0].strip()
                        field_value = parts[1].strip()
                        
                        # Check if field name matches any in our mapping
                        for pdf_field, canonical_key in field_mapping.items():
                            if pdf_field.lower() in field_name.lower():
                                if field_value:
                                    fine_data[canonical_key] = self._convert_value(canonical_key, field_value)
                                break
        
        return fine_data
    
    def _convert_value(self, key: str, value: str) -> Any:
        """Convert string value to appropriate type."""
        if key in ["notification_date", "defense_due_date", "driver_id_due_date", "violation_date"]:
            return parse_date(value)
        elif key == "amount":
            try:
                amount_str = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
                return float(amount_str)
            except ValueError:
                return 0.0
        else:
            return value


class MultiStrategyParser:
    """Parser that tries multiple strategies in order until one succeeds."""
    
    def __init__(self, strategies: Optional[List[ParsingStrategy]] = None):
        """
        Initialize multi-strategy parser.
        
        Args:
            strategies: List of parsing strategies to try. If None, uses default strategies.
        """
        if strategies is None:
            self.strategies = [
                StructuredParsingStrategy(),
                RegexParsingStrategy(),
                TableParsingStrategy()
            ]
        else:
            self.strategies = strategies
    
    def parse(self, pdf_path: str, jurisdiction: str = 'brazil') -> Optional[Dict[str, Any]]:
        """
        Parse PDF using multiple strategies with fallback.
        
        Args:
            pdf_path: Path to PDF file
            jurisdiction: Jurisdiction name for field mapping
        
        Returns:
            Dictionary with extracted data or None if all strategies fail
        """
        # Get field mapping for jurisdiction
        config = get_field_mapping_config()
        field_mapping = config.get_mapping(jurisdiction)
        
        # Extract text from PDF
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            if not text.strip():
                logger.warning(f"PDF appears to be empty or contains no extractable text: {pdf_path}")
                return None
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}", exc_info=True)
            return None
        
        # Try each strategy in order
        for i, strategy in enumerate(self.strategies):
            strategy_name = strategy.__class__.__name__
            logger.debug(f"Trying strategy {i+1}/{len(self.strategies)}: {strategy_name}")
            
            result = strategy.parse(pdf_path, text, field_mapping)
            
            if result and result.get('fine_number'):
                logger.info(f"Successfully parsed {pdf_path} using {strategy_name}")
                return result
            else:
                logger.debug(f"Strategy {strategy_name} did not extract fine number")
        
        logger.warning(f"All parsing strategies failed for {pdf_path}")
        return None

