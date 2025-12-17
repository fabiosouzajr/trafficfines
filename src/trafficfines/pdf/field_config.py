"""
Configuration-based field mapping system for PDF parsing.

This module loads field mappings from JSON configuration files, allowing
easy adaptation to different PDF formats and jurisdictions without code changes.
"""
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from trafficfines.utils.logger import get_logger

logger = get_logger(__name__)


class FieldMappingConfig:
    """Manages field mappings loaded from configuration files."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize field mapping configuration.
        
        Args:
            config_file: Path to JSON configuration file. If None, uses default.
        """
        if config_file is None:
            # Use default config file in same directory as this module
            from pathlib import Path
            config_file = str(Path(__file__).parent / 'field_mappings.json')
        
        self.config_file = config_file
        self.mappings: Dict[str, Dict[str, str]] = {}
        self.current_jurisdiction: str = 'brazil'
        self.load_config()
    
    def load_config(self) -> bool:
        """
        Load field mappings from configuration file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.config_file):
                logger.warning(f"Configuration file not found: {self.config_file}")
                return False
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.mappings = json.load(f)
            
            logger.info(f"Loaded field mappings from {self.config_file}")
            logger.debug(f"Available jurisdictions: {list(self.mappings.keys())}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file {self.config_file}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading configuration file {self.config_file}: {e}", exc_info=True)
            return False
    
    def get_mapping(self, jurisdiction: Optional[str] = None) -> Dict[str, str]:
        """
        Get field mapping for specified jurisdiction.
        
        Args:
            jurisdiction: Jurisdiction name. If None, uses current jurisdiction.
        
        Returns:
            Dictionary mapping PDF field names to canonical field names
        """
        if jurisdiction is None:
            jurisdiction = self.current_jurisdiction
        
        if jurisdiction not in self.mappings:
            logger.warning(f"Jurisdiction '{jurisdiction}' not found, using 'brazil'")
            jurisdiction = 'brazil'
        
        mapping = self.mappings.get(jurisdiction, {})
        logger.debug(f"Using field mapping for jurisdiction: {jurisdiction} ({len(mapping)} fields)")
        return mapping
    
    def set_jurisdiction(self, jurisdiction: str) -> bool:
        """
        Set current jurisdiction.
        
        Args:
            jurisdiction: Jurisdiction name
        
        Returns:
            True if jurisdiction exists, False otherwise
        """
        if jurisdiction in self.mappings:
            self.current_jurisdiction = jurisdiction
            logger.info(f"Set jurisdiction to: {jurisdiction}")
            return True
        else:
            logger.warning(f"Jurisdiction '{jurisdiction}' not found in configuration")
            return False
    
    def list_jurisdictions(self) -> list:
        """
        List available jurisdictions.
        
        Returns:
            List of jurisdiction names
        """
        return list(self.mappings.keys())
    
    def add_mapping(self, jurisdiction: str, pdf_field: str, canonical_field: str) -> None:
        """
        Add a new field mapping (runtime modification).
        
        Args:
            jurisdiction: Jurisdiction name
            pdf_field: PDF field name as it appears in document
            canonical_field: Canonical field name
        """
        if jurisdiction not in self.mappings:
            self.mappings[jurisdiction] = {}
        
        self.mappings[jurisdiction][pdf_field] = canonical_field
        logger.debug(f"Added mapping: {pdf_field} -> {canonical_field} for {jurisdiction}")
    
    def save_config(self, output_file: Optional[str] = None) -> bool:
        """
        Save current mappings to configuration file.
        
        Args:
            output_file: Output file path. If None, uses original config file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        if output_file is None:
            output_file = self.config_file
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.mappings, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved field mappings to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration file {output_file}: {e}", exc_info=True)
            return False
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        Validate configuration file structure.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.mappings:
            errors.append("No mappings found in configuration")
            return False, errors
        
        for jurisdiction, mapping in self.mappings.items():
            if not isinstance(mapping, dict):
                errors.append(f"Jurisdiction '{jurisdiction}' mapping must be a dictionary")
                continue
            
            for pdf_field, canonical_field in mapping.items():
                if not isinstance(pdf_field, str) or not isinstance(canonical_field, str):
                    errors.append(f"Invalid mapping in '{jurisdiction}': {pdf_field} -> {canonical_field}")
        
        is_valid = len(errors) == 0
        return is_valid, errors


# Global instance for easy access
_default_config: Optional[FieldMappingConfig] = None


def get_field_mapping_config(config_file: Optional[str] = None) -> FieldMappingConfig:
    """
    Get or create default field mapping configuration instance.
    
    Args:
        config_file: Optional path to configuration file
    
    Returns:
        FieldMappingConfig instance
    """
    global _default_config
    
    if _default_config is None:
        _default_config = FieldMappingConfig(config_file)
    
    return _default_config

