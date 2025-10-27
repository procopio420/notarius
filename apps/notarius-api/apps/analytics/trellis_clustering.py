"""TRELLIS clustering service for discovering new intent patterns."""

from typing import List, Dict, Any
from collections import Counter
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import numpy as np

from .models import TRELLISInteractionLog, TRELLISClusterMetrics

class TRELLISClusteringService:
    """Service for analyzing interactions and discovering new clusters (Step 2)."""
    
    def analyze_unclustered_interactions(self, tenant_id: str, min_samples: int = 5) -> List[Dict[str, Any]]:
        """Analyze interactions that didn't match any cluster."""
        # Get interactions that used LLM fallback
        unclustered = TRELLISInteractionLog.objects.filter(
            tenant_id=tenant_id,
            used_llm_fallback=True,
            success=True
        ).values_list('original_command', 'parsed_intent')
        
        if len(unclustered) < min_samples:
            return []
        
        commands = [cmd for cmd, _ in unclustered]
        
        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 3))
        X = vectorizer.fit_transform(commands)
        
        # DBSCAN clustering
        clustering = DBSCAN(eps=0.3, min_samples=min_samples, metric='cosine')
        labels = clustering.fit_predict(X.toarray())
        
        # Analyze each cluster
        discovered_clusters = []
        for label in set(labels):
            if label == -1:  # Noise
                continue
            
            cluster_commands = [cmd for cmd, lbl in zip(commands, labels) if lbl == label]
            cluster_intents = [intent for (_, intent), lbl in zip(unclustered, labels) if lbl == label]
            
            # Extract common patterns
            pattern = self._extract_pattern(cluster_commands)
            common_act_type = Counter([i.get('act_type') for i in cluster_intents]).most_common(1)[0][0]
            
            discovered_clusters.append({
                'suggested_id': f"{common_act_type}_{label}",
                'sample_count': len(cluster_commands),
                'pattern': pattern,
                'act_type': common_act_type,
                'sample_commands': cluster_commands[:5]
            })
        
        return discovered_clusters
    
    def _extract_pattern(self, commands: List[str]) -> str:
        """Extract regex pattern from similar commands."""
        # Simple pattern extraction: find common words
        words_by_position = []
        for i in range(max(len(cmd.split()) for cmd in commands)):
            words_at_position = [cmd.split()[i] if i < len(cmd.split()) else '' for cmd in commands]
            most_common = Counter(words_at_position).most_common(1)[0]
            if most_common[1] / len(commands) > 0.7:  # 70% threshold
                words_by_position.append(most_common[0])
            else:
                words_by_position.append('.*')
        
        return ' '.join(words_by_position)
    
    def suggest_deterministic_parser(self, cluster_id: str) -> str:
        """Generate Python code for a deterministic parser (Step 3)."""
        # Get sample interactions for this cluster
        samples = TRELLISInteractionLog.objects.filter(
            matched_cluster=cluster_id
        )[:10]
        
        # Analyze patterns and generate parser code template
        code_template = f'''
async def _parse_{cluster_id}(self, command: str) -> Intent:
    """Deterministic parser for {cluster_id}."""
    # Extract PII entities
    pii_entities = await self.pii_extractor.extract(command)
    
    # TODO: Add specific extraction logic based on patterns
    # Sample commands:
{chr(10).join(f"    # - {s.original_command}" for s in samples[:3])}
    
    # Parse parties
    parties = []
    for i, entity in enumerate(pii_entities):
        if entity.type == PIIEntityType.NAME:
            parties.append({{
                "role": "TODO_ROLE",
                "pii_extracted": [entity.value]
            }})
    
    jurisdiction = self._extract_jurisdiction(command)
    
    return Intent(
        act_type=ActType.TODO,
        parties=parties,
        powers=["TODO"],
        jurisdiction=jurisdiction,
        confidence=0.95,
        intent_cluster="{cluster_id}",
        variables={{}},
        pii_entities=pii_entities,
        original_command=command,
    )
'''
        return code_template
