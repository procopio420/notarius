"""
Rules endpoint for legal knowledge retrieval.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, cast
from sqlalchemy.dialects.postgresql import JSONB, array

from ..services.database import get_db
from ..models.lexnode import LegalRule

router = APIRouter()
logger = logging.getLogger(__name__)


class RuleResponse(BaseModel):
    """Response model for a single rule."""
    artigo: Optional[str] = Field(None, description="Article reference")
    fonte: str = Field(..., description="Source (e.g., 'Lei 6.015/73')")
    checklist_item: Optional[str] = Field(None, description="Checklist item")
    citation: str = Field(..., description="Full citation")
    precedence: str = Field(..., description="Precedence level (federal, state, internal)")
    content: str = Field(..., description="Rule content")


class RulesResponse(BaseModel):
    """Response model for rules endpoint."""
    rules: List[RuleResponse] = Field(..., description="List of applicable rules")
    checklist: List[str] = Field(..., description="Aggregated checklist items")
    citacoes: List[str] = Field(..., description="List of citations")


@router.get("/rules", response_model=RulesResponse)
async def get_rules(
    doctype: Optional[str] = Query(None, description="Document type (e.g., 'escritura_compra_venda')"),
    uf: Optional[str] = Query(None, description="State jurisdiction (e.g., 'SP', 'RJ')"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get applicable legal rules for a document type and jurisdiction.
    
    Returns rules with citations, checklist items, and precedence ordering.
    Precedence: CNJ (federal) > CGJ/UF (state) > notas internas (internal)
    """
    try:
        # Build query
        query = select(LegalRule).where(LegalRule.is_active == True)
        
        # Filter by document type if provided
        if doctype:
            # Use JSONB contains operator for document_types array
            # Check if doctype is in the document_types JSONB array
            # Use raw SQL with JSONB @> operator
            from sqlalchemy import text
            import json
            doctype_json = json.dumps([doctype])
            query = query.where(
                text("document_types @> :doctype_json::jsonb").bindparams(doctype_json=doctype_json)
            )
        
        # Filter by UF if provided
        if uf:
            query = query.where(
                or_(
                    LegalRule.uf == uf,
                    LegalRule.uf.is_(None),  # Federal rules apply to all UFs
                    LegalRule.precedence == "federal"  # Federal rules apply to all
                )
            )
        
        # Execute query
        result = await db.execute(query)
        rules = result.scalars().all()
        
        # Sort by precedence: federal > state > internal
        precedence_order = {"federal": 0, "state": 1, "internal": 2}
        rules_sorted = sorted(
            rules,
            key=lambda r: (precedence_order.get(r.precedence, 3), r.fonte, r.artigo or "")
        )
        
        # Build response
        rule_responses = []
        checklist_items = set()
        citacoes = set()
        
        for rule in rules_sorted:
            # Add checklist items
            if rule.checklist_items:
                for item in rule.checklist_items:
                    checklist_items.add(item)
            
            # Add citation
            citacoes.add(rule.citation)
            
            # Create rule response
            # Use first checklist item if available
            checklist_item = rule.checklist_items[0] if rule.checklist_items else None
            
            rule_responses.append(RuleResponse(
                artigo=rule.artigo,
                fonte=rule.fonte,
                checklist_item=checklist_item,
                citation=rule.citation,
                precedence=rule.precedence,
                content=rule.content[:500]  # Limit content length
            ))
        
        logger.info(
            f"Retrieved {len(rule_responses)} rules for doctype={doctype}, uf={uf}"
        )
        
        return RulesResponse(
            rules=rule_responses,
            checklist=sorted(list(checklist_items)),
            citacoes=sorted(list(citacoes))
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve rules: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve rules")

