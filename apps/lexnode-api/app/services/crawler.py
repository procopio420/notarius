"""
Legal document crawler service.
"""

import logging
import httpx
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class CrawlerService:
    """Crawls legal document sources."""
    
    def __init__(self):
        self.sources = {
            "cnj": "https://atos.cnj.jus.br",
            "cgj_rj": "https://www.tjrj.jus.br/web/guest/corregedoria",
        }
    
    async def crawl_source(
        self,
        source: str,
        max_documents: int = 100
    ) -> List[Dict]:
        """
        Crawl legal documents from source.
        
        Args:
            source: Source name (cnj, cgj_rj, etc.)
            max_documents: Maximum documents to crawl
            
        Returns:
            List of crawled documents
        """
        logger.info(f"Crawling source: {source}")
        
        if source not in self.sources:
            logger.error(f"Unknown source: {source}")
            return []
        
        # For MVP, return mock legal documents
        # In production, implement actual web scraping
        return await self._get_mock_legal_documents(source, max_documents)
    
    async def crawl_url(self, url: str) -> Optional[Dict]:
        """
        Crawl a specific URL.
        
        Args:
            url: URL to crawl
            
        Returns:
            Crawled document or None
        """
        logger.info(f"Crawling URL: {url}")
        
        try:
            from packages.core.http_client import get_http_client
            http_client = get_http_client()
            response = await http_client.get(url, timeout=30.0)
            
            if response.status_code != 200:
                logger.warning(f"Failed to crawl {url}: {response.status_code}")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text() if title else "Untitled"
            
            # Extract main content
            content = soup.get_text()
            
            return {
                "url": url,
                "title": title_text,
                "content": content[:10000],  # Limit size
                "source": "web",
                "metadata": {
                    "content_type": response.headers.get("content-type"),
                    "status_code": response.status_code,
                }
            }
                
        except Exception as e:
            logger.error(f"Failed to crawl {url}: {e}")
            return None
    
    async def _get_mock_legal_documents(self, source: str, limit: int) -> List[Dict]:
        """
        Get mock legal documents for development.
        In production, this would be replaced with actual web scraping.
        """
        mock_documents = [
            {
                "id": "lei_8935_1994",
                "title": "Lei 8.935/1994 - Lei dos Cartórios",
                "content": """LEI Nº 8.935, DE 18 DE NOVEMBRO DE 1994

Regulamenta o art. 236 da Constituição Federal, dispondo sobre serviços notariais e de registro.

Art. 1º Serviços notariais e de registro são os de organização técnica e administrativa destinados a garantir a publicidade, autenticidade, segurança e eficácia dos atos jurídicos.

Art. 2º É livre a escolha do tabelião de notas, qualquer que seja o domicílio das partes ou o lugar de situação dos bens objeto do ato ou negócio.

Art. 3º Notário, ou tabelião, e oficial de registro, ou registrador, são profissionais do direito, dotados de fé pública, a quem é delegado o exercício da atividade notarial e de registro.

Art. 6º Aos notários compete:
I - formalizar juridicamente a vontade das partes;
II - intervir nos atos e negócios jurídicos a que as partes devam ou queiram dar forma legal ou autenticidade, autorizando a redação ou redigindo os instrumentos adequados, conservando os originais e expedindo cópias fidedignas de seu conteúdo;
III - autenticar fatos.

Art. 7º Aos tabeliães de notas compete com exclusividade:
I - lavrar escrituras e procurações, públicas;
II - lavrar testamentos públicos e aprovar os cerrados;
III - lavrar atas notariais;
IV - reconhecer firmas;
V - autenticar cópias.""",
                "url": "http://www.planalto.gov.br/ccivil_03/leis/l8935.htm",
                "source": source,
                "type": "lei",
                "jurisdiction": "federal",
                "metadata": {
                    "year": 1994,
                    "number": "8.935",
                    "articles": ["1", "2", "3", "6", "7"]
                }
            },
            {
                "id": "codigo_civil_procuracao",
                "title": "Código Civil - Procuração (Arts. 653-692)",
                "content": """CÓDIGO CIVIL - LIVRO I - DO DIREITO DAS OBRIGAÇÕES
TÍTULO VI - DAS VÁRIAS ESPÉCIES DE CONTRATO
CAPÍTULO XIII - DO MANDATO

Art. 653. Opera-se o mandato quando alguém recebe de outrem poderes para, em seu nome, praticar atos ou administrar interesses. A procuração é o instrumento do mandato.

Art. 654. Todas as pessoas capazes são aptas para dar procuração mediante instrumento particular, que valerá desde que tenha a assinatura do outorgante.

Art. 655. Ainda quando se outorgue mandato por instrumento público, podem substabelecer-se mediante instrumento particular.

Art. 656. O mandato pode ser expresso ou tácito, verbal ou escrito.

Art. 657. A outorga do mandato está sujeita à forma exigida por lei para o ato a ser praticado. Não se admite mandato verbal quando o ato deva ser celebrado por escrito.

Art. 658. O mandato presume-se gratuito quando não houver sido estipulada retribuição, exceto se o seu objeto corresponder ao daqueles que o mandatário trata por ofício ou profissão lucrativa.

Art. 661. O mandatário não pode, em regra, sem procuração especial, representar o mandante perante foro ou tribunal.""",
                "url": "http://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm",
                "source": source,
                "type": "codigo",
                "jurisdiction": "federal",
                "metadata": {
                    "code": "civil",
                    "articles": ["653", "654", "655", "656", "657", "658", "661"]
                }
            },
            {
                "id": "provimento_cgj_rj_procuracao",
                "title": "CGJ-RJ - Provimento sobre Procurações",
                "content": """PROVIMENTO CGJ Nº 25/2020 - Dispõe sobre lavratura de procurações

Art. 1º A procuração pública lavrada em cartório de notas deve conter:
I - qualificação completa do outorgante e do outorgado;
II - objeto e extensão dos poderes conferidos;
III - prazo de validade, se houver;
IV - local e data da lavratura;
V - assinatura do outorgante ou, a seu rogo, de duas testemunhas.

Art. 2º Na procuração para compra e venda de imóveis, devem constar:
I - descrição do imóvel com matrícula atualizada;
II - poderes específicos para alienar, dar e receber quitação;
III - valor do negócio ou forma de pagamento;
IV - condições especiais pactuadas entre as partes.

Art. 3º É vedado lavrar procuração com poderes excessivamente amplos que possam gerar dúvida quanto à vontade do outorgante.

Art. 4º O tabelião deve verificar a identidade e a capacidade do outorgante.""",
                "url": "https://cgj.tjrj.jus.br/provimentos",
                "source": source,
                "type": "provimento",
                "jurisdiction": "RJ",
                "metadata": {
                    "year": 2020,
                    "number": "25",
                    "cgj": "RJ"
                }
            }
        ]
        
        return mock_documents[:limit]

