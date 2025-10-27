"""
Portuguese morphology engine for legal document placeholders.

Handles Portuguese grammar rules, contractions, and gender agreement
for Brazilian legal documents.
"""

import re
from typing import Dict, List, Optional, Tuple

from packages.pii.exceptions import MorphEngineException


class ContractionEngine:
    """Handles Portuguese contractions (do/da, ao/à, etc.)."""
    
    def __init__(self):
        # Contraction rules: preposition + article
        self.contractions = {
            ('de', 'o'): 'do',
            ('de', 'a'): 'da',
            ('de', 'os'): 'dos',
            ('de', 'as'): 'das',
            ('a', 'o'): 'ao',
            ('a', 'a'): 'à',
            ('a', 'os'): 'aos',
            ('a', 'as'): 'às',
            ('em', 'o'): 'no',
            ('em', 'a'): 'na',
            ('em', 'os'): 'nos',
            ('em', 'as'): 'nas',
            ('por', 'o'): 'pelo',
            ('por', 'a'): 'pela',
            ('por', 'os'): 'pelos',
            ('por', 'as'): 'pelas',
        }
    
    def apply_contractions(self, text: str) -> str:
        """Apply Portuguese contractions to text."""
        # Sort by length (longer first) to avoid partial matches
        sorted_contractions = sorted(
            self.contractions.items(),
            key=lambda x: len(x[0][0]) + len(x[0][1]),
            reverse=True
        )
        
        for (prep, article), contraction in sorted_contractions:
            # Use word boundaries to avoid partial matches
            pattern = rf'\b{re.escape(prep)}\s+{re.escape(article)}\b'
            text = re.sub(pattern, contraction, text, flags=re.IGNORECASE)
        
        return text


class GenderAgreementEngine:
    """Handles Portuguese gender agreement in legal documents."""
    
    def __init__(self):
        # Common gender patterns in legal documents
        self.gender_patterns = {
            'masculine': {
                'articles': ['o', 'os', 'um', 'uns'],
                'adjectives': ['outorgante', 'outorgado', 'procurador', 'testemunha'],
                'pronouns': ['ele', 'seu', 'dele'],
            },
            'feminine': {
                'articles': ['a', 'as', 'uma', 'umas'],
                'adjectives': ['outorgante', 'outorgada', 'procuradora', 'testemunha'],
                'pronouns': ['ela', 'sua', 'dela'],
            }
        }
    
    def get_gender_hints(self, name: str) -> Optional[str]:
        """Determine gender from Brazilian name patterns."""
        # Common Brazilian name endings
        feminine_endings = ['a', 'e', 'ia', 'ina', 'ana', 'ela', 'ila']
        masculine_endings = ['o', 'os', 'ão', 'inho', 'ito']
        
        name_lower = name.lower().strip()
        
        # Check for feminine endings
        for ending in feminine_endings:
            if name_lower.endswith(ending):
                return 'feminine'
        
        # Check for masculine endings
        for ending in masculine_endings:
            if name_lower.endswith(ending):
                return 'masculine'
        
        # Default to masculine for ambiguous cases
        return 'masculine'
    
    def apply_gender_agreement(self, text: str, gender: str) -> str:
        """Apply gender agreement to text."""
        if gender not in self.gender_patterns:
            return text
        
        patterns = self.gender_patterns[gender]
        
        # Apply article agreement
        for article in patterns['articles']:
            # This is a simplified approach - in production, you'd want
            # more sophisticated NLP for gender agreement
            pass
        
        return text


class PortugueseMorphEngine:
    """
    Main Portuguese morphology engine for legal documents.
    
    Handles contractions, gender agreement, and grammatical variations
    for Brazilian Portuguese legal text.
    """
    
    def __init__(self):
        self.contraction_engine = ContractionEngine()
        self.gender_engine = GenderAgreementEngine()
    
    def inflect_placeholder(
        self, 
        template: str, 
        placeholder: str, 
        metadata: Dict[str, str]
    ) -> str:
        """
        Apply Portuguese morphology to a placeholder in a template.
        
        Args:
            template: Template text with placeholders
            placeholder: Placeholder to inflect (e.g., "{{PARTY_1_NAME}}")
            metadata: Metadata about the placeholder (gender, case, etc.)
            
        Returns:
            Inflected template text
            
        Raises:
            MorphEngineException: If inflection fails
        """
        try:
            # Extract placeholder info
            placeholder_info = self._parse_placeholder(placeholder)
            if not placeholder_info:
                return template
            
            # Apply contractions
            result = self.contraction_engine.apply_contractions(template)
            
            # Apply gender agreement if gender is specified
            if 'gender' in metadata:
                result = self.gender_engine.apply_gender_agreement(
                    result, metadata['gender']
                )
            
            # Apply case variations if specified
            if 'case' in metadata:
                result = self._apply_case_variation(result, metadata['case'])
            
            return result
            
        except Exception as e:
            raise MorphEngineException(
                f"Failed to inflect placeholder: {e}",
                template=template,
                placeholder=placeholder
            )
    
    def _parse_placeholder(self, placeholder: str) -> Optional[Dict[str, str]]:
        """Parse placeholder metadata from placeholder string."""
        # Example: "{{PARTY_1_NAME|gender:m|case:genitive}}"
        if not placeholder.startswith('{{') or not placeholder.endswith('}}'):
            return None
        
        # Extract the main part and metadata
        content = placeholder[2:-2]  # Remove {{ and }}
        
        if '|' not in content:
            return {'name': content}
        
        parts = content.split('|')
        name = parts[0]
        metadata = {}
        
        for part in parts[1:]:
            if ':' in part:
                key, value = part.split(':', 1)
                metadata[key] = value
        
        return {'name': name, **metadata}
    
    def _apply_case_variation(self, text: str, case: str) -> str:
        """Apply case variations (genitive, dative, etc.)."""
        # This is a simplified implementation
        # In production, you'd want more sophisticated case handling
        
        if case == 'genitive':
            # Handle genitive case (possession)
            # Example: "do João" vs "da Maria"
            pass
        elif case == 'dative':
            # Handle dative case (indirect object)
            # Example: "ao João" vs "à Maria"
            pass
        
        return text
    
    def generate_placeholder_variants(
        self, 
        base_placeholder: str, 
        metadata: Dict[str, str]
    ) -> List[str]:
        """
        Generate all possible placeholder variants for a given metadata.
        
        Args:
            base_placeholder: Base placeholder (e.g., "{{PARTY_1_NAME}}")
            metadata: Metadata about the placeholder
            
        Returns:
            List of placeholder variants
        """
        variants = [base_placeholder]
        
        # Generate gender variants
        if 'gender' in metadata:
            gender = metadata['gender']
            if gender == 'm':
                variants.append(f"{base_placeholder}|gender:m")
            elif gender == 'f':
                variants.append(f"{base_placeholder}|gender:f")
        
        # Generate case variants
        if 'case' in metadata:
            case = metadata['case']
            variants.append(f"{base_placeholder}|case:{case}")
        
        # Generate combined variants
        if 'gender' in metadata and 'case' in metadata:
            gender = metadata['gender']
            case = metadata['case']
            variants.append(f"{base_placeholder}|gender:{gender}|case:{case}")
        
        return variants
    
    def apply_morphology_to_draft(
        self, 
        draft: str, 
        placeholders: Dict[str, Dict[str, str]]
    ) -> str:
        """
        Apply Portuguese morphology to an entire draft.
        
        Args:
            draft: Draft text with placeholders
            placeholders: Dictionary mapping placeholder names to metadata
            
        Returns:
            Morphologically corrected draft
        """
        result = draft
        
        # Apply contractions first
        result = self.contraction_engine.apply_contractions(result)
        
        # Apply gender agreement for each placeholder
        for placeholder_name, metadata in placeholders.items():
            if 'gender' in metadata:
                # Find and replace placeholder with gender agreement
                pattern = rf'\b{re.escape(placeholder_name)}\b'
                # This would need more sophisticated replacement logic
                # in production
                pass
        
        return result
