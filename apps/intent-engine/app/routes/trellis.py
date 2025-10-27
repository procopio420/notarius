"""
TRELLIS service routes for intent parsing.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from ..services.trellis import get_trellis_service

router = APIRouter()


class IntentRequest(BaseModel):
    command: str


class IntentResponse(BaseModel):
    act_type: str
    parties: List[Dict[str, Any]]
    powers: List[str]
    jurisdiction: str
    confidence: float
    intent_cluster: str
    variables: Dict[str, Any]
    pii_entities: List[Dict[str, Any]]
    original_command: str


@router.post("/parse-intent", response_model=IntentResponse)
async def parse_intent(request: IntentRequest):
    """
    Parse natural language intent using TRELLIS framework.
    
    This endpoint uses the TRELLIS (Targeted Refinement of Emergent LLM Intelligence 
    through Structured Segmentation) approach for reliable intent parsing.
    """
    try:
        trellis_service = get_trellis_service()
        intent = await trellis_service.parse_intent(request.command)
        
        return IntentResponse(
            act_type=intent.act_type.value,
            parties=intent.parties,
            powers=intent.powers,
            jurisdiction=intent.jurisdiction.value,
            confidence=intent.confidence,
            intent_cluster=intent.intent_cluster,
            variables=intent.variables,
            pii_entities=[entity.dict() for entity in intent.pii_entities],
            original_command=intent.original_command
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent parsing failed: {str(e)}")


@router.get("/clusters")
async def get_clusters():
    """Get all available TRELLIS clusters."""
    try:
        trellis_service = get_trellis_service()
        clusters = await trellis_service.get_clusters()
        return {"clusters": [cluster.dict() for cluster in clusters]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get clusters: {str(e)}")


@router.post("/clusters")
async def add_cluster(cluster_data: Dict[str, Any]):
    """Add a new TRELLIS cluster."""
    try:
        from packages.core.models import TRELLISCluster
        cluster = TRELLISCluster(**cluster_data)
        
        trellis_service = get_trellis_service()
        await trellis_service.add_cluster(cluster)
        
        return {"message": "Cluster added successfully", "cluster_id": cluster.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add cluster: {str(e)}")


@router.put("/clusters/{cluster_id}")
async def update_cluster(cluster_id: str, updates: Dict[str, Any]):
    """Update an existing TRELLIS cluster."""
    try:
        trellis_service = get_trellis_service()
        await trellis_service.update_cluster(cluster_id, updates)
        
        return {"message": "Cluster updated successfully", "cluster_id": cluster_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update cluster: {str(e)}")
