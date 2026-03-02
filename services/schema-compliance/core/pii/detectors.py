"""
PII Detectors - Pattern matching for various PII types
"""
import re
from typing import List, Optional, Dict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PIIType(str, Enum):
    """PII types matching compliance_models"""
    EMAIL_ADDRESS = "email_address"
    PHONE_NUMBER = "phone_number"
    SOCIAL_SECURITY_NUMBER = "social_security_number"
    CREDIT_CARD = "credit_card_number"
    IP_ADDRESS = "ip_address"
    PHYSICAL_ADDRESS = "physical_address"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    FULL_NAME = "full_name"
    DATE_OF_BIRTH = "date_of_birth"


class PIIDetector:
    """Base class for PII detectors"""
    
    pii_type: PIIType
    severity: str = "medium"
    frameworks: List[str] = []
    
    def matches(self, column_name: str, column_type: str) -> bool:
        """Check if column matches this PII type"""
        raise NotImplementedError
    
    def get_confidence(self, column_name: str, column_type: str) -> float:
        """Calculate confidence score (0.0-1.0)"""
        raise NotImplementedError
    
    def get_recommendations(self) -> List[str]:
        """Get compliance recommendations"""
        return [
            "Enable encryption at rest",
            "Implement access controls",
            "Add audit logging"
        ]


class EmailDetector(PIIDetector):
    """Detect email address fields"""
    
    pii_type = PIIType.EMAIL_ADDRESS
    severity = "high"
    frameworks = ["GDPR", "CCPA"]
    
    # Column names that typically contain emails
    EMAIL_PATTERNS = [
        r"^email",
        r"^e_?mail",
        r"email$",
        r"_email$",
        r"^user_?email",
        r"^contact_?email",
        r"^customer_?email"
    ]
    
    def matches(self, column_name: str, column_type: str) -> bool:
        """Check if column likely contains emails"""
        column_lower = column_name.lower()
        
        # Check column name patterns
        for pattern in self.EMAIL_PATTERNS:
            if re.search(pattern, column_lower):
                return True
        
        return False
    
    def get_confidence(self, column_name: str, column_type: str) -> float:
        """Calculate confidence score"""
        column_lower = column_name.lower()
        
        # High confidence matches
        if column_lower in ["email", "email_address", "user_email"]:
            return 0.99
        
        # Medium confidence matches
        for pattern in self.EMAIL_PATTERNS:
            if re.search(pattern, column_lower):
                return 0.85
        
        return 0.0
    
    def get_recommendations(self) -> List[str]:
        return [
            "Enable encryption at rest",
            "Add data retention policy",
            "Implement consent tracking",
            "Add email verification"
        ]


class PhoneDetector(PIIDetector):
    """Detect phone number fields"""
    
    pii_type = PIIType.PHONE_NUMBER
    severity = "high"
    frameworks = ["GDPR", "CCPA"]
    
    PHONE_PATTERNS = [
        r"^phone",
        r"^tel",
        r"^mobile",
        r"phone$",
        r"_phone$",
        r"^contact_?number"
    ]
    
    def matches(self, column_name: str, column_type: str) -> bool:
        column_lower = column_name.lower()
        for pattern in self.PHONE_PATTERNS:
            if re.search(pattern, column_lower):
                return True
        return False
    
    def get_confidence(self, column_name: str, column_type: str) -> float:
        column_lower = column_name.lower()
        if column_lower in ["phone", "phone_number", "mobile", "telephone"]:
            return 0.95
        for pattern in self.PHONE_PATTERNS:
            if re.search(pattern, column_lower):
                return 0.80
        return 0.0
    
    def get_recommendations(self) -> List[str]:
        return [
            "Enable encryption at rest",
            "Add opt-out mechanism",
            "Implement phone verification"
        ]


class SSNDetector(PIIDetector):
    """Detect Social Security Number fields"""
    
    pii_type = PIIType.SOCIAL_SECURITY_NUMBER
    severity = "critical"
    frameworks = ["GDPR", "HIPAA", "PCI-DSS"]
    
    SSN_PATTERNS = [
        r"^ssn",
        r"^social_?security",
        r"ssn$",
        r"_ssn$"
    ]
    
    def matches(self, column_name: str, column_type: str) -> bool:
        column_lower = column_name.lower()
        for pattern in self.SSN_PATTERNS:
            if re.search(pattern, column_lower):
                return True
        return False
    
    def get_confidence(self, column_name: str, column_type: str) -> float:
        column_lower = column_name.lower()
        if column_lower in ["ssn", "social_security_number", "social_security"]:
            return 0.98
        for pattern in self.SSN_PATTERNS:
            if re.search(pattern, column_lower):
                return 0.90
        return 0.0
    
    def get_recommendations(self) -> List[str]:
        return [
            "Enable encryption at rest and in transit",
            "Implement audit logging",
            "Restrict access to authorized personnel only",
            "Use tokenization for storage"
        ]


class CreditCardDetector(PIIDetector):
    """Detect credit card number fields"""
    
    pii_type = PIIType.CREDIT_CARD
    severity = "critical"
    frameworks = ["PCI-DSS", "GDPR"]
    
    CC_PATTERNS = [
        r"^cc",
        r"^credit_?card",
        r"card_?number",
        r"^payment_?card"
    ]
    
    def matches(self, column_name: str, column_type: str) -> bool:
        column_lower = column_name.lower()
        for pattern in self.CC_PATTERNS:
            if re.search(pattern, column_lower):
                return True
        return False
    
    def get_confidence(self, column_name: str, column_type: str) -> float:
        column_lower = column_name.lower()
        if column_lower in ["credit_card", "card_number", "cc_number"]:
            return 0.97
        for pattern in self.CC_PATTERNS:
            if re.search(pattern, column_lower):
                return 0.85
        return 0.0
    
    def get_recommendations(self) -> List[str]:
        return [
            "Use PCI-DSS compliant tokenization",
            "Never store CVV",
            "Enable encryption at rest and in transit",
            "Implement strict access controls",
            "Regular PCI compliance audits"
        ]


class IPAddressDetector(PIIDetector):
    """Detect IP address fields"""
    
    pii_type = PIIType.IP_ADDRESS
    severity = "medium"
    frameworks = ["GDPR"]
    
    IP_PATTERNS = [
        r"^ip",
        r"ip_?address",
        r"_ip$"
    ]
    
    def matches(self, column_name: str, column_type: str) -> bool:
        column_lower = column_name.lower()
        for pattern in self.IP_PATTERNS:
            if re.search(pattern, column_lower):
                return True
        return False
    
    def get_confidence(self, column_name: str, column_type: str) -> float:
        column_lower = column_name.lower()
        if column_lower in ["ip", "ip_address", "ipaddress"]:
            return 0.90
        for pattern in self.IP_PATTERNS:
            if re.search(pattern, column_lower):
                return 0.75
        return 0.0


class NameDetector(PIIDetector):
    """Detect name fields"""
    
    pii_type = PIIType.FULL_NAME
    severity = "high"
    frameworks = ["GDPR", "CCPA"]
    
    NAME_PATTERNS = {
        "first_name": [r"^first_?name", r"^fname", r"^given_?name"],
        "last_name": [r"^last_?name", r"^lname", r"^surname", r"^family_?name"],
        "full_name": [r"^name$", r"^full_?name", r"^display_?name", r"^user_?name"]
    }
    
    def matches(self, column_name: str, column_type: str) -> bool:
        column_lower = column_name.lower()
        for patterns in self.NAME_PATTERNS.values():
            for pattern in patterns:
                if re.search(pattern, column_lower):
                    return True
        return False
    
    def get_confidence(self, column_name: str, column_type: str) -> float:
        column_lower = column_name.lower()
        
        # High confidence
        high_conf = ["first_name", "last_name", "full_name", "name"]
        if column_lower in high_conf:
            return 0.95
        
        # Medium confidence
        for patterns in self.NAME_PATTERNS.values():
            for pattern in patterns:
                if re.search(pattern, column_lower):
                    return 0.80
        
        return 0.0


class DateOfBirthDetector(PIIDetector):
    """Detect date of birth fields"""
    
    pii_type = PIIType.DATE_OF_BIRTH
    severity = "high"
    frameworks = ["GDPR", "HIPAA", "CCPA"]
    
    DOB_PATTERNS = [
        r"^dob",
        r"^birth_?date",
        r"^date_?of_?birth",
        r"birthday"
    ]
    
    def matches(self, column_name: str, column_type: str) -> bool:
        column_lower = column_name.lower()
        for pattern in self.DOB_PATTERNS:
            if re.search(pattern, column_lower):
                return True
        return False
    
    def get_confidence(self, column_name: str, column_type: str) -> float:
        column_lower = column_name.lower()
        if column_lower in ["dob", "date_of_birth", "birth_date"]:
            return 0.96
        for pattern in self.DOB_PATTERNS:
            if re.search(pattern, column_lower):
                return 0.82
        return 0.0


class PIIDetectorRegistry:
    """Registry of all PII detectors"""
    
    def __init__(self):
        self.detectors: List[PIIDetector] = [
            EmailDetector(),
            PhoneDetector(),
            SSNDetector(),
            CreditCardDetector(),
            IPAddressDetector(),
            NameDetector(),
            DateOfBirthDetector()
        ]
    
    def detect_pii(self, column_name: str, column_type: str) -> Optional[Dict]:
        """
        Detect PII in a column
        
        Returns:
            Dict with detection results or None if no PII detected
        """
        for detector in self.detectors:
            if detector.matches(column_name, column_type):
                confidence = detector.get_confidence(column_name, column_type)
                
                if confidence > 0.7:  # Confidence threshold
                    return {
                        "pii_type": detector.pii_type.value,
                        "confidence": confidence,
                        "severity": detector.severity,
                        "frameworks": detector.frameworks,
                        "recommendations": detector.get_recommendations()
                    }
        
        return None
