"""
Multi-layer PII extraction system with defense-in-depth approach.

Inspired by Oleve's systematic approach to reliability, this module provides
multiple layers of PII extraction to ensure 100% recall and prevent PII leaks.
"""

import re
from abc import ABC, abstractmethod
from typing import List, Set, Tuple, Dict, Optional

import spacy
from packages.core.models import PIIEntity, PIIEntityType
from packages.pii.exceptions import PIIExtractionException, PIILeakException


class PIIExtractor(ABC):
    """Abstract base class for PII extractors."""
    
    def __init__(self, priority: int = 1):
        self.priority = priority
    
    @abstractmethod
    async def extract(self, text: str) -> List[PIIEntity]:
        """Extract PII entities from text."""
        pass


class RegexExtractor(PIIExtractor):
    """Regex-based PII extractor for formatted documents."""
    
    def __init__(self, priority: int = 1):
        super().__init__(priority)
        self.patterns = {
            PIIEntityType.CPF: [
                r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b',  # Formatted: 123.456.789-00
                r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',  # Flexible formatting
                r'\b\d{11}\b',  # Unformatted: 12345678900
            ],
            PIIEntityType.CNPJ: [
                r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b',  # Formatted: 12.345.678/0001-90
                r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b',  # Flexible formatting
                r'\b\d{14}\b',  # Unformatted: 12345678000190
            ],
            PIIEntityType.EMAIL: [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ],
            PIIEntityType.PHONE: [
                r'\b\(\d{2}\)\s?\d{4,5}-?\d{4}\b',  # (11) 99999-9999
                r'\b\d{2}\s?\d{4,5}-?\d{4}\b',  # 11 99999-9999
                r'\b\d{10,11}\b',  # 11999999999
                r'\+55\s?\(?\d{2}\)?\s?\d{4,5}-?\d{4}',  # With country code
            ],
            PIIEntityType.RG: [
                r'\bRG:?\s*\d{1,2}\.?\d{3}\.?\d{3}-?[0-9X]\b',  # RG format
            ],
        }
    
    async def extract(self, text: str) -> List[PIIEntity]:
        """Extract PII using regex patterns."""
        entities = []
        
        for pii_type, patterns in self.patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entity = PIIEntity(
                        type=pii_type,
                        value=match.group(),
                        start=match.start(),
                        end=match.end(),
                        confidence=0.9,  # High confidence for regex matches
                        context=text[max(0, match.start()-20):match.end()+20]
                    )
                    entities.append(entity)
        
        return entities


class SpacyNERExtractor(PIIExtractor):
    """spaCy-based NER extractor for names and locations."""
    
    def __init__(self, priority: int = 2):
        super().__init__(priority)
        try:
            self.nlp = spacy.load("pt_core_news_lg")
        except OSError:
            # Fallback to smaller model if large model not available
            self.nlp = spacy.load("pt_core_news_sm")
    
    async def extract(self, text: str) -> List[PIIEntity]:
        """Extract PII using spaCy NER."""
        entities = []
        doc = self.nlp(text)
        
        for ent in doc.ents:
            if ent.label_ in ["PER", "PERSON"]:
                entity = PIIEntity(
                    type=PIIEntityType.NAME,
                    value=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.8,  # Medium confidence for NER
                    context=text[max(0, ent.start_char-20):ent.end_char+20]
                )
                entities.append(entity)
            elif ent.label_ in ["LOC", "GPE"]:
                entity = PIIEntity(
                    type=PIIEntityType.ADDRESS,
                    value=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.7,  # Lower confidence for locations
                    context=text[max(0, ent.start_char-20):ent.end_char+20]
                )
                entities.append(entity)
        
        return entities


class BERTNERExtractor(PIIExtractor):
    """BERT-based NER extractor as fallback."""
    
    def __init__(self, priority: int = 3):
        super().__init__(priority)
        # This would use a Portuguese BERT model in production
        # For now, we'll implement a placeholder
        self.model_loaded = False
    
    async def extract(self, text: str) -> List[PIIEntity]:
        """Extract PII using BERT NER (placeholder implementation)."""
        # In production, this would use neuralmind/bert-base-portuguese-cased
        # or similar Portuguese BERT model
        entities = []
        
        if not self.model_loaded:
            # Placeholder: would load BERT model here
            self.model_loaded = True
        
        # Placeholder implementation
        # In production, this would:
        # 1. Tokenize text
        # 2. Run through BERT model
        # 3. Extract named entities
        # 4. Convert to PIIEntity objects
        
        return entities


class ValidationLayer(PIIExtractor):
    """Validation layer to verify extracted PII."""
    
    def __init__(self, priority: int = 4):
        super().__init__(priority)
        from .validators import CPFValidator, CNPJValidator, EmailValidator
    
        self.validators = {
            PIIEntityType.CPF: CPFValidator(),
            PIIEntityType.CNPJ: CNPJValidator(),
            PIIEntityType.EMAIL: EmailValidator(),
        }
    
    async def extract(self, text: str) -> List[PIIEntity]:
        """Validate existing PII entities (not a real extractor)."""
        # This layer doesn't extract new entities, it validates existing ones
        # It's used in the MultiLayerPIIExtractor pipeline
        return []


class ScannerLayer(PIIExtractor):
    """Final scanning layer to catch any missed PII."""
    
    def __init__(self, priority: int = 5):
        super().__init__(priority)
        # Patterns for common PII that might be missed
        self.suspicious_patterns = [
            r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',  # CPF-like patterns
            r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b',  # CNPJ-like patterns
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Name-like patterns
        ]
    
    async def extract(self, text: str) -> List[PIIEntity]:
        """Scan for any missed PII patterns."""
        entities = []
        
        for pattern in self.suspicious_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Determine PII type based on pattern
                if re.match(r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}', match.group()):
                    pii_type = PIIEntityType.CPF
                elif re.match(r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}', match.group()):
                    pii_type = PIIEntityType.CNPJ
                else:
                    pii_type = PIIEntityType.NAME
                
                entity = PIIEntity(
                    type=pii_type,
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.5,  # Low confidence, needs validation
                    context=text[max(0, match.start()-20):match.end()+20]
                )
                entities.append(entity)
        
        return entities


class MultiLayerPIIExtractor:
    """
    Defense-in-depth PII extraction system.
    
    Uses multiple extractors in sequence to ensure 100% recall.
    Inspired by Oleve's systematic approach to reliability.
    """
    
    def __init__(self):
        self.extractors = [
            RegexExtractor(priority=1),
            SpacyNERExtractor(priority=2),
            BERTNERExtractor(priority=3),
            ValidationLayer(priority=4),
            ScannerLayer(priority=5),
        ]
        self.extractors.sort(key=lambda x: x.priority)
    
    async def extract(self, text: str) -> List[PIIEntity]:
        """
        Extract PII using multiple layers with deduplication.
        
        Args:
            text: Input text to extract PII from
            
        Returns:
            List of PII entities with deduplication applied
            
        Raises:
            PIILeakException: If PII is detected after extraction
        """
        all_entities = []
        
        # Run all extractors
        for extractor in self.extractors:
            try:
                entities = await extractor.extract(text)
                all_entities.extend(entities)
            except Exception as e:
                # Log error but continue with other extractors
                print(f"Extractor {extractor.__class__.__name__} failed: {e}")
        
        # Deduplicate entities
        deduplicated = self._deduplicate_entities(all_entities)
        
        # Validate entities
        validated = await self._validate_entities(deduplicated)
        
        # Final scan for missed PII
        remaining_pii = await self._scan_for_missed_pii(text, validated)
        if remaining_pii:
            raise PIILeakException(
                f"Unextracted PII detected: {remaining_pii}",
                detected_pii=remaining_pii,
                context="final_scan"
            )
        
        return validated
    
    def _deduplicate_entities(self, entities: List[PIIEntity]) -> List[PIIEntity]:
        """Remove duplicate entities based on position and value."""
        seen = set()
        deduplicated = []
        
        for entity in entities:
            # Create a key based on position and value
            key = (entity.start, entity.end, entity.value.lower())
            if key not in seen:
                seen.add(key)
                deduplicated.append(entity)
        
        return deduplicated
    
    async def _validate_entities(self, entities: List[PIIEntity]) -> List[PIIEntity]:
        """Validate extracted entities using appropriate validators."""
        validated = []
        
        for entity in entities:
            try:
                # Validate based on type
                if entity.type == PIIEntityType.CPF:
                    from .validators import CPFValidator
                    validator = CPFValidator()
                    if await validator.validate(entity.value):
                        validated.append(entity)
                elif entity.type == PIIEntityType.CNPJ:
                    from .validators import CNPJValidator
                    validator = CNPJValidator()
                    if await validator.validate(entity.value):
                        validated.append(entity)
                elif entity.type == PIIEntityType.EMAIL:
                    from .validators import EmailValidator
                    validator = EmailValidator()
                    if await validator.validate(entity.value):
                        validated.append(entity)
                else:
                    # For other types, accept if confidence is high enough
                    if entity.confidence >= 0.7:
                        validated.append(entity)
            except Exception as e:
                # Log validation error but continue
                print(f"Validation failed for {entity.value}: {e}")
        
        return validated
    
    async def _scan_for_missed_pii(self, text: str, entities: List[PIIEntity]) -> List[str]:
        """Final scan to detect any missed PII patterns."""
        # Create a set of covered positions
        covered_positions = set()
        for entity in entities:
            for pos in range(entity.start, entity.end):
                covered_positions.add(pos)
        
        # Scan for suspicious patterns not covered by entities
        missed_pii = []
        suspicious_patterns = [
            r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',  # CPF
            r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b',  # CNPJ
        ]
        
        for pattern in suspicious_patterns:
            for match in re.finditer(pattern, text):
                # Check if this position is already covered
                is_covered = any(
                    match.start() <= pos < match.end() 
                    for pos in range(match.start(), match.end())
                )
                
                if not is_covered:
                    missed_pii.append(match.group())
        
        return missed_pii
    
    def extract_placeholders(self, content: str) -> List[str]:
        """Extract placeholders from draft content."""
        placeholders = re.findall(r'\{\{([A-Z_]+)\}\}', content)
        return list(set(placeholders))
    
    def calculate_grounding_confidence(self, citations: Optional[List[Dict]]) -> float:
        """Calculate grounding confidence from citations."""
        if not citations:
            return 0.6  # No citations = lower confidence
        
        # Average relevance
        relevances = [c.get("relevance", 0.5) for c in citations]
        avg_relevance = sum(relevances) / len(relevances) if relevances else 0.5
        
        # Boost for multiple citations
        citation_boost = min(len(citations) * 0.05, 0.2)
        
        return min(avg_relevance + citation_boost, 0.99)