"""
Golden Q&A sets for RAG evaluation
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class GoldenQuery:
    """Represents a golden query for evaluation."""
    query: str
    expected_act_type: str
    expected_entities: List[str]
    expected_jurisdiction: str
    expected_document_type: str
    expected_confidence_threshold: float
    expected_citations_count: int
    expected_grounding_confidence: float
    expected_pii_types: List[str]
    expected_metadata: Dict[str, Any]
    difficulty: str  # "easy", "medium", "hard"
    category: str  # "procuração", "contrato", "testamento", etc.


@dataclass
class GoldenAnswer:
    """Represents a golden answer for evaluation."""
    query_id: str
    expected_draft_structure: Dict[str, Any]
    expected_citations: List[Dict[str, Any]]
    expected_confidence_score: float
    expected_grounding_confidence: float
    expected_pii_tokenization: Dict[str, str]
    expected_metadata: Dict[str, Any]


class GoldenQASets:
    """Collection of golden Q&A sets for RAG evaluation."""
    
    def __init__(self):
        self.queries = self._create_queries()
        self.answers = self._create_answers()
    
    def _create_queries(self) -> List[GoldenQuery]:
        """Create golden queries for evaluation."""
        return [
            # Procuração queries
            GoldenQuery(
                query="Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel em São Paulo.",
                expected_act_type="procuração",
                expected_entities=["João Silva", "123.456.789-00", "vender", "imóvel", "São Paulo"],
                expected_jurisdiction="sp",
                expected_document_type="procuração",
                expected_confidence_threshold=0.9,
                expected_citations_count=3,
                expected_grounding_confidence=0.85,
                expected_pii_types=["cpf", "name", "address"],
                expected_metadata={"purpose": "venda de imóvel", "jurisdiction": "sp"},
                difficulty="easy",
                category="procuração"
            ),
            GoldenQuery(
                query="Procuração para Maria Santos, CPF 987.654.321-00, outorgar poderes para comprar imóvel no Rio de Janeiro.",
                expected_act_type="procuração",
                expected_entities=["Maria Santos", "987.654.321-00", "comprar", "imóvel", "Rio de Janeiro"],
                expected_jurisdiction="rj",
                expected_document_type="procuração",
                expected_confidence_threshold=0.9,
                expected_citations_count=3,
                expected_grounding_confidence=0.85,
                expected_pii_types=["cpf", "name", "address"],
                expected_metadata={"purpose": "compra de imóvel", "jurisdiction": "rj"},
                difficulty="easy",
                category="procuração"
            ),
            GoldenQuery(
                query="Fazer procuração para Pedro Costa, CPF 111.222.333-44, outorgar poderes para representar em processos judiciais.",
                expected_act_type="procuração",
                expected_entities=["Pedro Costa", "111.222.333-44", "representar", "processos", "judiciais"],
                expected_jurisdiction="rj",
                expected_document_type="procuração",
                expected_confidence_threshold=0.8,
                expected_citations_count=2,
                expected_grounding_confidence=0.75,
                expected_pii_types=["cpf", "name"],
                expected_metadata={"purpose": "representação judicial", "jurisdiction": "rj"},
                difficulty="medium",
                category="procuração"
            ),
            
            # Contrato queries
            GoldenQuery(
                query="Fazer contrato de compra e venda de imóvel entre João Silva e Maria Santos.",
                expected_act_type="contrato",
                expected_entities=["João Silva", "Maria Santos", "compra", "venda", "imóvel"],
                expected_jurisdiction="rj",
                expected_document_type="contrato",
                expected_confidence_threshold=0.9,
                expected_citations_count=4,
                expected_grounding_confidence=0.85,
                expected_pii_types=["name", "name"],
                expected_metadata={"purpose": "compra e venda de imóvel", "jurisdiction": "rj"},
                difficulty="easy",
                category="contrato"
            ),
            GoldenQuery(
                query="Contrato de locação de imóvel residencial entre proprietário e inquilino.",
                expected_act_type="contrato",
                expected_entities=["locação", "imóvel", "residencial", "proprietário", "inquilino"],
                expected_jurisdiction="rj",
                expected_document_type="contrato",
                expected_confidence_threshold=0.8,
                expected_citations_count=3,
                expected_grounding_confidence=0.75,
                expected_pii_types=[],
                expected_metadata={"purpose": "locação de imóvel", "jurisdiction": "rj"},
                difficulty="medium",
                category="contrato"
            ),
            
            # Testamento queries
            GoldenQuery(
                query="Fazer testamento de Ana Costa, CPF 555.666.777-88, deixando bens para filhos.",
                expected_act_type="testamento",
                expected_entities=["Ana Costa", "555.666.777-88", "bens", "filhos"],
                expected_jurisdiction="rj",
                expected_document_type="testamento",
                expected_confidence_threshold=0.9,
                expected_citations_count=2,
                expected_grounding_confidence=0.8,
                expected_pii_types=["cpf", "name"],
                expected_metadata={"purpose": "disposição de bens", "jurisdiction": "rj"},
                difficulty="easy",
                category="testamento"
            ),
            
            # Escritura queries
            GoldenQuery(
                query="Fazer escritura de compra e venda de imóvel em São Paulo.",
                expected_act_type="escritura",
                expected_entities=["compra", "venda", "imóvel", "São Paulo"],
                expected_jurisdiction="sp",
                expected_document_type="escritura",
                expected_confidence_threshold=0.8,
                expected_citations_count=3,
                expected_grounding_confidence=0.75,
                expected_pii_types=["address"],
                expected_metadata={"purpose": "compra e venda de imóvel", "jurisdiction": "sp"},
                difficulty="medium",
                category="escritura"
            ),
            
            # Certidão queries
            GoldenQuery(
                query="Fazer certidão de nascimento de João Silva, filho de Maria Santos e Pedro Costa.",
                expected_act_type="certidão",
                expected_entities=["João Silva", "Maria Santos", "Pedro Costa", "nascimento"],
                expected_jurisdiction="rj",
                expected_document_type="certidão",
                expected_confidence_threshold=0.9,
                expected_citations_count=1,
                expected_grounding_confidence=0.8,
                expected_pii_types=["name", "name", "name"],
                expected_metadata={"purpose": "certidão de nascimento", "jurisdiction": "rj"},
                difficulty="easy",
                category="certidão"
            ),
            
            # Complex queries
            GoldenQuery(
                query="Fazer procuração para empresa ABC Ltda, CNPJ 12.345.678/0001-90, outorgar poderes para representar em processos administrativos e judiciais, com poderes especiais para transigir e receber valores.",
                expected_act_type="procuração",
                expected_entities=["ABC Ltda", "12.345.678/0001-90", "representar", "processos", "administrativos", "judiciais", "transigir", "receber", "valores"],
                expected_jurisdiction="rj",
                expected_document_type="procuração",
                expected_confidence_threshold=0.8,
                expected_citations_count=4,
                expected_grounding_confidence=0.75,
                expected_pii_types=["cnpj", "company_name"],
                expected_metadata={"purpose": "representação judicial e administrativa", "jurisdiction": "rj", "powers": ["transigir", "receber valores"]},
                difficulty="hard",
                category="procuração"
            ),
            
            # Edge cases
            GoldenQuery(
                query="Fazer procuração para pessoa física com poderes gerais.",
                expected_act_type="procuração",
                expected_entities=["pessoa física", "poderes", "gerais"],
                expected_jurisdiction="rj",
                expected_document_type="procuração",
                expected_confidence_threshold=0.7,
                expected_citations_count=2,
                expected_grounding_confidence=0.6,
                expected_pii_types=[],
                expected_metadata={"purpose": "poderes gerais", "jurisdiction": "rj"},
                difficulty="hard",
                category="procuração"
            ),
            
            # Invalid queries (should have low confidence)
            GoldenQuery(
                query="Como fazer um bolo de chocolate?",
                expected_act_type="",
                expected_entities=[],
                expected_jurisdiction="",
                expected_document_type="",
                expected_confidence_threshold=0.1,
                expected_citations_count=0,
                expected_grounding_confidence=0.1,
                expected_pii_types=[],
                expected_metadata={},
                difficulty="hard",
                category="invalid"
            ),
            GoldenQuery(
                query="Qual é a capital do Brasil?",
                expected_act_type="",
                expected_entities=[],
                expected_jurisdiction="",
                expected_document_type="",
                expected_confidence_threshold=0.1,
                expected_citations_count=0,
                expected_grounding_confidence=0.1,
                expected_pii_types=[],
                expected_metadata={},
                difficulty="hard",
                category="invalid"
            )
        ]
    
    def _create_answers(self) -> List[GoldenAnswer]:
        """Create golden answers for evaluation."""
        return [
            # Procuração answers
            GoldenAnswer(
                query_id="procuração_001",
                expected_draft_structure={
                    "title": "PROCURAÇÃO",
                    "sections": ["outorgante", "outorgado", "poderes", "cláusulas", "assinaturas"],
                    "required_clauses": ["identificação das partes", "poderes outorgados", "cláusula de irrevogabilidade"]
                },
                expected_citations=[
                    {
                        "uri": "https://www.planalto.gov.br/ccivil_03/leis/l2002compilada.htm",
                        "anchor": "Art. 653",
                        "title": "Código Civil - Procuração",
                        "snippet": "A procuração é o instrumento do mandato.",
                        "score": 0.9
                    },
                    {
                        "uri": "https://www.cnj.jus.br/",
                        "anchor": "Resolução 125/2010",
                        "title": "CNJ - Procuração em Cartório",
                        "snippet": "A procuração pode ser feita em cartório.",
                        "score": 0.8
                    }
                ],
                expected_confidence_score=0.9,
                expected_grounding_confidence=0.85,
                expected_pii_tokenization={
                    "PARTY_1_NAME": "token_joao_silva",
                    "PARTY_1_CPF": "token_cpf_12345678900",
                    "PROPERTY_ADDRESS": "token_sao_paulo"
                },
                expected_metadata={
                    "purpose": "venda de imóvel",
                    "jurisdiction": "sp",
                    "document_type": "procuração"
                }
            ),
            
            # Contrato answers
            GoldenAnswer(
                query_id="contrato_001",
                expected_draft_structure={
                    "title": "CONTRATO DE COMPRA E VENDA",
                    "sections": ["partes", "objeto", "preço", "condições", "assinaturas"],
                    "required_clauses": ["identificação das partes", "descrição do imóvel", "preço e forma de pagamento"]
                },
                expected_citations=[
                    {
                        "uri": "https://www.planalto.gov.br/ccivil_03/leis/l2002compilada.htm",
                        "anchor": "Art. 481",
                        "title": "Código Civil - Compra e Venda",
                        "snippet": "Pelo contrato de compra e venda, um dos contratantes se obriga a transferir o domínio de certa coisa.",
                        "score": 0.9
                    }
                ],
                expected_confidence_score=0.9,
                expected_grounding_confidence=0.85,
                expected_pii_tokenization={
                    "PARTY_1_NAME": "token_joao_silva",
                    "PARTY_2_NAME": "token_maria_santos"
                },
                expected_metadata={
                    "purpose": "compra e venda de imóvel",
                    "jurisdiction": "rj",
                    "document_type": "contrato"
                }
            ),
            
            # Testamento answers
            GoldenAnswer(
                query_id="testamento_001",
                expected_draft_structure={
                    "title": "TESTAMENTO",
                    "sections": ["testador", "herdeiros", "disposições", "assinaturas"],
                    "required_clauses": ["identificação do testador", "identificação dos herdeiros", "disposição dos bens"]
                },
                expected_citations=[
                    {
                        "uri": "https://www.planalto.gov.br/ccivil_03/leis/l2002compilada.htm",
                        "anchor": "Art. 1857",
                        "title": "Código Civil - Testamento",
                        "snippet": "O testamento é o negócio jurídico pelo qual alguém, em conformidade com a lei, dispõe de todo o seu patrimônio.",
                        "score": 0.9
                    }
                ],
                expected_confidence_score=0.9,
                expected_grounding_confidence=0.8,
                expected_pii_tokenization={
                    "TESTATOR_NAME": "token_ana_costa",
                    "TESTATOR_CPF": "token_cpf_55566677788"
                },
                expected_metadata={
                    "purpose": "disposição de bens",
                    "jurisdiction": "rj",
                    "document_type": "testamento"
                }
            )
        ]
    
    def get_queries_by_category(self, category: str) -> List[GoldenQuery]:
        """Get queries by category."""
        return [q for q in self.queries if q.category == category]
    
    def get_queries_by_difficulty(self, difficulty: str) -> List[GoldenQuery]:
        """Get queries by difficulty."""
        return [q for q in self.queries if q.difficulty == difficulty]
    
    def get_queries_by_jurisdiction(self, jurisdiction: str) -> List[GoldenQuery]:
        """Get queries by jurisdiction."""
        return [q for q in self.queries if q.expected_jurisdiction == jurisdiction]
    
    def get_query_by_id(self, query_id: str) -> GoldenQuery:
        """Get query by ID."""
        for query in self.queries:
            if query.query == query_id:
                return query
        raise ValueError(f"Query with ID {query_id} not found")
    
    def get_answer_by_query_id(self, query_id: str) -> GoldenAnswer:
        """Get answer by query ID."""
        for answer in self.answers:
            if answer.query_id == query_id:
                return answer
        raise ValueError(f"Answer with query ID {query_id} not found")
    
    def get_all_categories(self) -> List[str]:
        """Get all categories."""
        return list(set(q.category for q in self.queries))
    
    def get_all_difficulties(self) -> List[str]:
        """Get all difficulties."""
        return list(set(q.difficulty for q in self.queries))
    
    def get_all_jurisdictions(self) -> List[str]:
        """Get all jurisdictions."""
        return list(set(q.expected_jurisdiction for q in self.queries if q.expected_jurisdiction))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the golden Q&A sets."""
        return {
            "total_queries": len(self.queries),
            "total_answers": len(self.answers),
            "categories": {
                category: len(self.get_queries_by_category(category))
                for category in self.get_all_categories()
            },
            "difficulties": {
                difficulty: len(self.get_queries_by_difficulty(difficulty))
                for difficulty in self.get_all_difficulties()
            },
            "jurisdictions": {
                jurisdiction: len(self.get_queries_by_jurisdiction(jurisdiction))
                for jurisdiction in self.get_all_jurisdictions()
            },
            "average_confidence_threshold": sum(q.expected_confidence_threshold for q in self.queries) / len(self.queries),
            "average_grounding_confidence": sum(q.expected_grounding_confidence for q in self.queries) / len(self.queries),
            "average_citations_count": sum(q.expected_citations_count for q in self.queries) / len(self.queries)
        }


# Global instance
golden_qa_sets = GoldenQASets()


def get_golden_qa_sets() -> GoldenQASets:
    """Get the global golden Q&A sets instance."""
    return golden_qa_sets
