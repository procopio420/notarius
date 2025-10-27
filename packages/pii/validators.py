"""
Brazilian document validators for PII entities.

Provides validation for CPF, CNPJ, and other Brazilian documents
with proper checksum verification.
"""

import re
from abc import ABC, abstractmethod
from typing import List

from packages.pii.exceptions import PIIValidationException


class DocumentValidator(ABC):
    """Abstract base class for document validators."""
    
    @abstractmethod
    async def validate(self, value: str) -> bool:
        """Validate a document value."""
        pass
    
    @abstractmethod
    def clean(self, value: str) -> str:
        """Clean and normalize a document value."""
        pass


class CPFValidator(DocumentValidator):
    """CPF (Cadastro de Pessoas Físicas) validator."""
    
    def clean(self, value: str) -> str:
        """Remove formatting from CPF."""
        return re.sub(r'[^\d]', '', value)
    
    async def validate(self, value: str) -> bool:
        """Validate CPF with checksum verification."""
        try:
            # Clean the value
            cpf = self.clean(value)
            
            # Check length
            if len(cpf) != 11:
                return False
            
            # Check for invalid sequences (all same digits)
            if cpf == cpf[0] * 11:
                return False
            
            # Calculate first check digit
            sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
            digit1 = 11 - (sum1 % 11)
            if digit1 >= 10:
                digit1 = 0
            
            # Calculate second check digit
            sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
            digit2 = 11 - (sum2 % 11)
            if digit2 >= 10:
                digit2 = 0
            
            # Verify check digits
            return int(cpf[9]) == digit1 and int(cpf[10]) == digit2
            
        except (ValueError, IndexError):
            return False


class CNPJValidator(DocumentValidator):
    """CNPJ (Cadastro Nacional da Pessoa Jurídica) validator."""
    
    def clean(self, value: str) -> str:
        """Remove formatting from CNPJ."""
        return re.sub(r'[^\d]', '', value)
    
    async def validate(self, value: str) -> bool:
        """Validate CNPJ with checksum verification."""
        try:
            # Clean the value
            cnpj = self.clean(value)
            
            # Check length
            if len(cnpj) != 14:
                return False
            
            # Check for invalid sequences (all same digits)
            if cnpj == cnpj[0] * 14:
                return False
            
            # Calculate first check digit
            weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
            sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
            digit1 = 11 - (sum1 % 11)
            if digit1 >= 10:
                digit1 = 0
            
            # Calculate second check digit
            weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
            sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
            digit2 = 11 - (sum2 % 11)
            if digit2 >= 10:
                digit2 = 0
            
            # Verify check digits
            return int(cnpj[12]) == digit1 and int(cnpj[13]) == digit2
            
        except (ValueError, IndexError):
            return False


class EmailValidator(DocumentValidator):
    """Email validator with Brazilian domain awareness."""
    
    def clean(self, value: str) -> str:
        """Normalize email (lowercase, trim)."""
        return value.strip().lower()
    
    async def validate(self, value: str) -> bool:
        """Validate email format."""
        try:
            email = self.clean(value)
            
            # Basic regex validation
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, email):
                return False
            
            # Check for common Brazilian domains
            brazilian_domains = [
                'gmail.com', 'hotmail.com', 'yahoo.com.br', 'uol.com.br',
                'bol.com.br', 'terra.com.br', 'ig.com.br', 'globo.com',
                'outlook.com', 'live.com'
            ]
            
            domain = email.split('@')[1]
            return domain in brazilian_domains or domain.endswith('.br')
            
        except (ValueError, IndexError):
            return False


class PhoneValidator(DocumentValidator):
    """Brazilian phone number validator."""
    
    def clean(self, value: str) -> str:
        """Remove formatting from phone number."""
        return re.sub(r'[^\d]', '', value)
    
    async def validate(self, value: str) -> bool:
        """Validate Brazilian phone number."""
        try:
            phone = self.clean(value)
            
            # Brazilian mobile numbers: 11 digits (2 area code + 9 digits)
            # Brazilian landline: 10 digits (2 area code + 8 digits)
            if len(phone) == 11:
                # Mobile number
                area_code = phone[:2]
                number = phone[2:]
                
                # Valid area codes (major cities)
                valid_area_codes = [
                    '11', '12', '13', '14', '15', '16', '17', '18', '19',  # SP
                    '21', '22', '24',  # RJ
                    '31', '32', '33', '34', '35', '37', '38',  # MG
                    '41', '42', '43', '44', '45', '46',  # PR
                    '47', '48', '49',  # SC
                    '51', '53', '54', '55',  # RS
                    '61',  # DF
                    '62', '64',  # GO
                    '63',  # TO
                    '65', '66',  # MT
                    '67',  # MS
                    '68',  # AC
                    '69',  # RO
                    '71', '73', '74', '75', '77',  # BA
                    '79',  # SE
                    '81', '87',  # PE
                    '82',  # AL
                    '83',  # PB
                    '84',  # RN
                    '85', '88',  # CE
                    '86', '89',  # PI
                    '91', '93', '94',  # PA
                    '92', '97',  # AM
                    '95',  # RR
                    '96',  # AP
                    '98', '99',  # MA
                ]
                
                return area_code in valid_area_codes and number.startswith('9')
                
            elif len(phone) == 10:
                # Landline number
                area_code = phone[:2]
                number = phone[2:]
                
                # Valid area codes (same as mobile)
                valid_area_codes = [
                    '11', '12', '13', '14', '15', '16', '17', '18', '19',  # SP
                    '21', '22', '24',  # RJ
                    '31', '32', '33', '34', '35', '37', '38',  # MG
                    '41', '42', '43', '44', '45', '46',  # PR
                    '47', '48', '49',  # SC
                    '51', '53', '54', '55',  # RS
                    '61',  # DF
                    '62', '64',  # GO
                    '63',  # TO
                    '65', '66',  # MT
                    '67',  # MS
                    '68',  # AC
                    '69',  # RO
                    '71', '73', '74', '75', '77',  # BA
                    '79',  # SE
                    '81', '87',  # PE
                    '82',  # AL
                    '83',  # PB
                    '84',  # RN
                    '85', '88',  # CE
                    '86', '89',  # PI
                    '91', '93', '94',  # PA
                    '92', '97',  # AM
                    '95',  # RR
                    '96',  # AP
                    '98', '99',  # MA
                ]
                
                return area_code in valid_area_codes and not number.startswith('9')
            
            return False
            
        except (ValueError, IndexError):
            return False


class BrazilianDocumentValidator:
    """Composite validator for Brazilian documents."""
    
    def __init__(self):
        self.validators = {
            'cpf': CPFValidator(),
            'cnpj': CNPJValidator(),
            'email': EmailValidator(),
            'phone': PhoneValidator(),
        }
    
    async def validate(self, doc_type: str, value: str) -> bool:
        """Validate a Brazilian document."""
        if doc_type not in self.validators:
            raise PIIValidationException(
                f"Unknown document type: {doc_type}",
                pii_type=doc_type,
                value=value
            )
        
        validator = self.validators[doc_type]
        return await validator.validate(value)
    
    def clean(self, doc_type: str, value: str) -> str:
        """Clean a Brazilian document value."""
        if doc_type not in self.validators:
            raise PIIValidationException(
                f"Unknown document type: {doc_type}",
                pii_type=doc_type,
                value=value
            )
        
        validator = self.validators[doc_type]
        return validator.clean(value)
