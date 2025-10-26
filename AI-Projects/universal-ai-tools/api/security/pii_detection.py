"""
PII Detection and Anonymization Service
Uses Microsoft Presidio for detecting and protecting personal information
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import presidio, but don't fail if not installed
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    logger.warning("⚠️  Presidio not installed. PII detection will be limited.")
    PRESIDIO_AVAILABLE = False


class PIIDetectionService:
    """
    Detects and anonymizes personally identifiable information (PII)
    
    Detects:
    - Email addresses
    - Phone numbers
    - Credit card numbers
    - SSN
    - IP addresses
    - Names (with ML)
    - Addresses
    """
    
    def __init__(self):
        if PRESIDIO_AVAILABLE:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            self.enabled = True
            logger.info("✅ PII detection enabled (Presidio)")
        else:
            self.analyzer = None
            self.anonymizer = None
            self.enabled = False
            logger.warning("⚠️  PII detection disabled (Presidio not available)")
    
    def detect(self, text: str, language: str = 'en') -> List[Dict[str, Any]]:
        """
        Detect PII in text
        
        Args:
            text: Text to analyze
            language: Language code (default: 'en')
            
        Returns:
            List of detected PII entities with type, score, start, end
        """
        if not self.enabled or not text:
            return []
        
        try:
            results = self.analyzer.analyze(text=text, language=language)
            return [
                {
                    'type': r.entity_type,
                    'start': r.start,
                    'end': r.end,
                    'score': r.score,
                    'text': text[r.start:r.end]
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"PII detection failed: {e}")
            return []
    
    def anonymize(
        self, 
        text: str, 
        mask_char: str = '*',
        language: str = 'en'
    ) -> str:
        """
        Anonymize PII in text by replacing with mask characters
        
        Args:
            text: Text to anonymize
            mask_char: Character to use for masking (default: '*')
            language: Language code (default: 'en')
            
        Returns:
            Text with PII masked
        """
        if not self.enabled or not text:
            return text
        
        try:
            # Analyze text
            results = self.analyzer.analyze(text=text, language=language)
            
            if not results:
                return text
            
            # Configure anonymization operators
            operators = {
                "DEFAULT": OperatorConfig("mask", {"chars_to_mask": 100, "masking_char": mask_char})
            }
            
            # Anonymize
            anonymized = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators=operators
            )
            
            return anonymized.text
        except Exception as e:
            logger.error(f"PII anonymization failed: {e}")
            return text
    
    def has_pii(self, text: str, threshold: float = 0.5) -> bool:
        """
        Check if text contains PII above confidence threshold
        
        Args:
            text: Text to check
            threshold: Minimum confidence score (0.0-1.0)
            
        Returns:
            True if PII detected above threshold
        """
        if not self.enabled or not text:
            return False
        
        results = self.detect(text)
        return any(r['score'] >= threshold for r in results)
    
    def get_pii_summary(self, text: str) -> Dict[str, int]:
        """
        Get summary of PII types detected
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary mapping PII type to count
        """
        if not self.enabled or not text:
            return {}
        
        results = self.detect(text)
        summary = {}
        for r in results:
            pii_type = r['type']
            summary[pii_type] = summary.get(pii_type, 0) + 1
        
        return summary


# Global instance
_pii_service: Optional[PIIDetectionService] = None


def get_pii_service() -> PIIDetectionService:
    """Get or create global PII detection service instance"""
    global _pii_service
    if _pii_service is None:
        _pii_service = PIIDetectionService()
    return _pii_service
