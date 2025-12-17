"""
Comprehensive data validation layer for PDF parsing.

This module provides validation for extracted fine data to ensure data quality
and catch extraction errors early.
"""
import re
from datetime import date, datetime
from typing import Dict, List, Tuple, Any, Optional, Union
from trafficfines.utils.logger import get_logger

logger = get_logger(__name__)


class FineDataValidator:
    """Validates extracted fine data for format, range, and logical consistency."""
    
    def __init__(self):
        """Initialize validator with default rules."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate fine data comprehensively.
        
        Args:
            data: Dictionary containing extracted fine data
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Required field validation
        self._validate_required_fields(data)
        
        # Format validations
        self._validate_fine_number(data)
        self._validate_license_plate(data)
        self._validate_amount(data)
        self._validate_dates(data)
        self._validate_document(data)
        self._validate_speed_data(data)
        
        # Logical validations
        self._validate_date_consistency(data)
        self._validate_amount_range(data)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _validate_required_fields(self, data: Dict[str, Any]) -> None:
        """Validate that required fields are present."""
        required_fields = ['fine_number', 'license_plate', 'violation_date']
        
        for field in required_fields:
            if not data.get(field):
                self.errors.append(f"Required field '{field}' is missing")
    
    def _validate_fine_number(self, data: Dict[str, Any]) -> None:
        """Validate fine number format."""
        fine_number = data.get('fine_number')
        if not fine_number:
            return
        
        # Fine number should be alphanumeric, typically contains digits
        # Brazilian fine numbers can be quite long and may contain letters
        if not isinstance(fine_number, str):
            self.errors.append(f"Fine number must be a string, got {type(fine_number)}")
            return
        
        # Remove common separators for validation
        cleaned = fine_number.replace('-', '').replace('.', '').replace(' ', '')
        
        # Should be at least 5 characters (minimum reasonable length)
        if len(cleaned) < 5:
            self.warnings.append(f"Fine number seems too short: {fine_number}")
        
        # Should contain at least some digits
        if not re.search(r'\d', cleaned):
            self.warnings.append(f"Fine number doesn't contain digits: {fine_number}")
    
    def _validate_license_plate(self, data: Dict[str, Any]) -> None:
        """Validate license plate format (Brazilian format: ABC1234 or ABC1D23)."""
        license_plate = data.get('license_plate')
        if not license_plate:
            return
        
        if not isinstance(license_plate, str):
            self.errors.append(f"License plate must be a string, got {type(license_plate)}")
            return
        
        # Remove common separators
        cleaned = license_plate.replace('-', '').replace(' ', '').upper()
        
        # Brazilian license plate formats:
        # Old: ABC1234 (3 letters + 4 digits)
        # New: ABC1D23 (3 letters + 1 digit + 1 letter + 2 digits)
        old_format = re.match(r'^[A-Z]{3}\d{4}$', cleaned)
        new_format = re.match(r'^[A-Z]{3}\d[A-Z]\d{2}$', cleaned)
        
        if not (old_format or new_format):
            self.warnings.append(f"License plate format may be invalid: {license_plate}")
    
    def _validate_amount(self, data: Dict[str, Any]) -> None:
        """Validate fine amount."""
        amount = data.get('amount')
        
        if amount is None:
            return
        
        # Amount should be numeric
        if not isinstance(amount, (int, float)):
            try:
                amount = float(amount)
            except (ValueError, TypeError):
                self.errors.append(f"Amount must be numeric, got {type(amount)}")
                return
        
        # Amount cannot be negative
        if amount < 0:
            self.errors.append(f"Amount cannot be negative: {amount}")
        
        # Amount should be reasonable (not zero, not extremely high)
        if amount == 0:
            self.warnings.append("Amount is zero - this may indicate a parsing error")
        elif amount > 100000:  # Very high fine amount
            self.warnings.append(f"Amount seems unusually high: {amount}")
    
    def _validate_dates(self, data: Dict[str, Any]) -> None:
        """Validate date fields."""
        date_fields = {
            'notification_date': 'Notification date',
            'defense_due_date': 'Defense due date',
            'driver_id_due_date': 'Driver ID due date',
            'violation_date': 'Violation date'
        }
        
        today = date.today()
        
        for field, field_name in date_fields.items():
            date_value = data.get(field)
            if not date_value:
                continue
            
            # Check if it's a date object
            if not isinstance(date_value, date):
                self.errors.append(f"{field_name} must be a date object, got {type(date_value)}")
                continue
            
            # Violation date cannot be in the future
            if field == 'violation_date' and date_value > today:
                self.errors.append(f"Violation date cannot be in the future: {date_value}")
            
            # Dates should not be too old (more than 10 years)
            if date_value < date(today.year - 10, 1, 1):
                self.warnings.append(f"{field_name} seems very old: {date_value}")
    
    def _validate_document(self, data: Dict[str, Any]) -> None:
        """Validate CPF/CNPJ format."""
        document = data.get('owner_document')
        if not document:
            return
        
        if not isinstance(document, str):
            return
        
        # Remove common separators
        cleaned = document.replace('.', '').replace('-', '').replace('/', '').replace(' ', '')
        
        # CPF: 11 digits, CNPJ: 14 digits
        if not re.match(r'^\d+$', cleaned):
            self.warnings.append(f"Document format may be invalid: {document}")
            return
        
        if len(cleaned) not in [11, 14]:
            self.warnings.append(f"Document length is unusual (expected 11 for CPF or 14 for CNPJ): {len(cleaned)}")
    
    def _validate_speed_data(self, data: Dict[str, Any]) -> None:
        """Validate speed-related fields for logical consistency."""
        measured = data.get('measured_speed')
        considered = data.get('considered_speed')
        speed_limit = data.get('speed_limit')
        
        # If we have speed data, validate it
        if measured or considered or speed_limit:
            speeds = []
            
            for field_name, value in [('measured_speed', measured), 
                                     ('considered_speed', considered),
                                     ('speed_limit', speed_limit)]:
                if value:
                    # Extract numeric value from string if needed
                    if isinstance(value, str):
                        # Try to extract number from string like "80 km/h" or "80"
                        match = re.search(r'(\d+)', value)
                        if match:
                            speeds.append((field_name, int(match.group(1))))
                    elif isinstance(value, (int, float)):
                        speeds.append((field_name, value))
            
            # Check logical consistency
            if len(speeds) >= 2:
                speed_values = [v for _, v in speeds]
                if max(speed_values) > 300:  # Unreasonably high speed
                    self.warnings.append(f"Speed values seem unusually high: {speeds}")
                
                # Measured speed should typically be >= considered speed
                if measured and considered:
                    measured_val = int(re.search(r'(\d+)', str(measured)).group(1)) if isinstance(measured, str) else measured
                    considered_val = int(re.search(r'(\d+)', str(considered)).group(1)) if isinstance(considered, str) else considered
                    if measured_val < considered_val:
                        self.warnings.append("Measured speed is less than considered speed - may indicate data issue")
    
    def _validate_date_consistency(self, data: Dict[str, Any]) -> None:
        """Validate logical consistency between dates."""
        violation_date = data.get('violation_date')
        notification_date = data.get('notification_date')
        defense_due_date = data.get('defense_due_date')
        driver_id_due_date = data.get('driver_id_due_date')
        
        if not all([violation_date, notification_date]):
            return
        
        # Notification date should be after violation date
        if isinstance(violation_date, date) and isinstance(notification_date, date):
            if notification_date < violation_date:
                self.warnings.append("Notification date is before violation date - may indicate data issue")
        
        # Defense due date should be after notification date
        if notification_date and defense_due_date:
            if isinstance(notification_date, date) and isinstance(defense_due_date, date):
                if defense_due_date < notification_date:
                    self.warnings.append("Defense due date is before notification date - may indicate data issue")
    
    def _validate_amount_range(self, data: Dict[str, Any]) -> None:
        """Validate that amount is within reasonable range for traffic fines."""
        amount = data.get('amount')
        if not amount or not isinstance(amount, (int, float)):
            return
        
        # Brazilian traffic fines typically range from ~R$ 50 to ~R$ 3000
        # But can be higher for serious violations
        if amount < 50:
            self.warnings.append(f"Amount seems unusually low for a traffic fine: {amount}")
        elif amount > 10000:
            self.warnings.append(f"Amount seems unusually high for a traffic fine: {amount}")


def validate_fine_data(data: Dict[str, Any], strict: bool = False) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function to validate fine data.
    
    Args:
        data: Dictionary containing extracted fine data
        strict: If True, warnings are treated as errors
    
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    validator = FineDataValidator()
    is_valid, errors, warnings = validator.validate(data)
    
    if strict and warnings:
        errors.extend(warnings)
        warnings = []
        is_valid = len(errors) == 0
    
    return is_valid, errors, warnings

