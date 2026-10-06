"""
Management command to scrape cartórios from Notariado.org.br API.
This command populates the Tenant database with real cartório data.

Data source:
- Notariado.org.br API: https://www.notariado.org.br/cartorios/search/
  Uses POST request with UF parameter to fetch cartórios by state.
"""

import httpx
import time
import csv
import io
from typing import List, Dict, Optional
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.tenancy.models import Tenant


class Command(BaseCommand):
    help = 'Scrape cartórios from CNJ and populate the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--uf',
            type=str,
            help='Filter by UF (state code). If not provided, scrapes all states.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of cartórios to import per state',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without saving to database (dry run)',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Delay between requests in seconds (default: 1.0)',
        )
        parser.add_argument(
            '--sample-data',
            action='store_true',
            help='Import sample cartório data for testing (RJ, SP, MG)',
        )

    def handle(self, *args, **options):
        uf_filter = options.get('uf')
        limit = options.get('limit')
        dry_run = options.get('dry_run', False)
        delay = options.get('delay', 1.0)
        sample_data = options.get('sample_data', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))

        if sample_data:
            # Use sample data for testing
            states = ['RJ', 'SP', 'MG']
            self.stdout.write(self.style.SUCCESS('Using sample data for RJ, SP, MG'))
        else:
            states = [uf_filter] if uf_filter else self.get_all_ufs()

        total_created = 0
        total_updated = 0
        total_errors = 0

        for uf in states:
            self.stdout.write(f'\nProcessing {uf}...')
            try:
                if sample_data:
                    cartorios = self.get_sample_cartorios(uf)
                else:
                    cartorios = self.fetch_cartorios_from_cnj(uf, delay)
                
                if limit:
                    cartorios = cartorios[:limit]

                for cartorio_data in cartorios:
                    try:
                        if not dry_run:
                            tenant, created = Tenant.objects.update_or_create(
                                nome=cartorio_data['nome'],
                                uf=cartorio_data['uf'],
                                defaults={
                                    'municipio': cartorio_data.get('municipio'),
                                    'tipo': cartorio_data.get('tipo'),
                                }
                            )
                            if created:
                                total_created += 1
                                self.stdout.write(
                                    self.style.SUCCESS(f'  ✓ Created: {cartorio_data["nome"]} - {cartorio_data.get("municipio", "")}/{cartorio_data["uf"]}')
                                )
                            else:
                                total_updated += 1
                                self.stdout.write(
                                    self.style.WARNING(f'  ~ Updated: {cartorio_data["nome"]} - {cartorio_data.get("municipio", "")}/{cartorio_data["uf"]}')
                                )
                        else:
                            self.stdout.write(
                                f'  [DRY RUN] Would create/update: {cartorio_data["nome"]} - {cartorio_data.get("municipio", "")}/{cartorio_data["uf"]}'
                            )
                            total_created += 1

                    except Exception as e:
                        total_errors += 1
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Error processing {cartorio_data.get("nome", "unknown")}: {str(e)}')
                        )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error fetching data for {uf}: {str(e)}')
                )
                total_errors += 1

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(f'  Created: {total_created}')
        self.stdout.write(f'  Updated: {total_updated}')
        self.stdout.write(f'  Errors: {total_errors}')
        if dry_run:
            self.stdout.write(self.style.WARNING('  (DRY RUN - No data was saved)'))

    def get_all_ufs(self) -> List[str]:
        """Return list of all Brazilian state codes"""
        return [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]

    def fetch_cartorios_from_cnj(self, uf: str, delay: float = 1.0) -> List[Dict]:
        """
        Fetch cartórios from CNJ for a given UF.
        
        Tries multiple data sources:
        1. CNJ Transparency Portal API/CSV
        2. Web scraping from CNJ directory
        """
        self.stdout.write(f'  Fetching cartórios for {uf}...')
        cartorios = []
        
        try:
            # Try method 1: Notariado.org.br API
            # Primary source for cartório data
            try:
                cartorios = self.fetch_from_cnj_transparency_portal(uf)
                if cartorios:
                    self.stdout.write(f'  ✓ Found {len(cartorios)} cartórios from Notariado.org.br API')
                    return cartorios
            except Exception as e:
                self.stdout.write(f'  ⚠ Notariado.org.br API method failed: {str(e)}')
            
            # Try method 2: Direct API call (if CNJ provides API)
            try:
                cartorios = self.fetch_from_cnj_api(uf)
                if cartorios:
                    self.stdout.write(f'  ✓ Found {len(cartorios)} cartórios from CNJ API')
                    return cartorios
            except Exception as e:
                self.stdout.write(f'  ⚠ CNJ API method failed: {str(e)}')
            
            # Try method 3: Web scraping (fallback)
            try:
                cartorios = self.scrape_cnj_directory(uf)
                if cartorios:
                    self.stdout.write(f'  ✓ Found {len(cartorios)} cartórios from web scraping')
                    return cartorios
            except Exception as e:
                self.stdout.write(f'  ⚠ Web scraping method failed: {str(e)}')
            
            if not cartorios:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ No cartórios found for {uf} using any method')
                )
            
            time.sleep(delay)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  Error fetching CNJ data: {str(e)}')
            )
        
        return cartorios

    def fetch_from_cnj_transparency_portal(self, uf: str) -> List[Dict]:
        """Fetch from Notariado.org.br API"""
        # Using the Notariado.org.br API endpoint
        # Reference: https://www.notariado.org.br/cartorios/search/
        api_url = "https://www.notariado.org.br/cartorios/search/"
        
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                # Prepare form data
                form_data = {
                    'uf': uf.lower(),
                    'cidade': '',
                    'cartorio': '',
                    'bairro': '',
                    'logradouro': '',
                    'cep': '',
                }
                
                # Headers to mimic browser request
                headers = {
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': 'https://www.notariado.org.br',
                    'referer': 'https://www.notariado.org.br/cartorios/',
                    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest',
                }
                
                # Make POST request
                response = client.post(
                    api_url,
                    data=form_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return self.parse_notariado_data(data, uf)
                    except Exception as e:
                        self.stdout.write(f'  ⚠ Error parsing JSON response: {str(e)}')
                        # Try to parse as text/HTML in case it's not JSON
                        if response.text:
                            self.stdout.write(f'  Response preview: {response.text[:200]}')
                else:
                    self.stdout.write(f'  ⚠ API returned status {response.status_code}')
                    
        except httpx.TimeoutException:
            self.stdout.write(f'  ⚠ Request timeout for {uf}')
        except Exception as e:
            self.stdout.write(f'  ⚠ Error fetching from Notariado API: {str(e)}')
        
        return []

    def fetch_from_cnj_api(self, uf: str) -> List[Dict]:
        """Fetch from CNJ API if available"""
        # Placeholder for CNJ API endpoint
        # Adjust based on actual CNJ API documentation
        api_url = f"https://api.cnj.jus.br/v1/cartorios?uf={uf}"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(api_url, headers={
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (compatible; Notarius/1.0)'
                })
                
                if response.status_code == 200:
                    data = response.json()
                    return self.parse_cnj_data(data)
        except Exception:
            pass
        
        return []

    def scrape_cnj_directory(self, uf: str) -> List[Dict]:
        """Scrape cartórios from CNJ directory webpage"""
        # This would require BeautifulSoup or similar
        # For now, return empty list - implement when needed
        # Example:
        # from bs4 import BeautifulSoup
        # url = f"https://www.cnj.jus.br/cartorios/{uf}"
        # response = httpx.get(url)
        # soup = BeautifulSoup(response.text, 'html.parser')
        # ... parse HTML ...
        return []

    def parse_cnj_csv(self, csv_content: str, uf: str) -> List[Dict]:
        """Parse CNJ CSV data"""
        cartorios = []
        
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            for row in csv_reader:
                # Map CSV columns to our model fields
                # Adjust column names based on actual CNJ CSV structure
                nome = (
                    row.get('nome') or 
                    row.get('razao_social') or 
                    row.get('nome_fantasia') or
                    row.get('cartorio')
                )
                
                municipio = (
                    row.get('municipio') or 
                    row.get('cidade') or
                    row.get('município')
                )
                
                tipo = (
                    row.get('tipo') or 
                    row.get('categoria') or
                    row.get('natureza') or
                    row.get('oficio')
                )
                
                if nome:
                    cartorios.append({
                        'nome': nome.strip(),
                        'municipio': municipio.strip() if municipio else None,
                        'uf': uf,
                        'tipo': tipo.strip() if tipo else None,
                    })
        except Exception as e:
            self.stdout.write(f'  ⚠ Error parsing CSV: {str(e)}')
        
        return cartorios

    def parse_notariado_data(self, data: Dict, uf: str) -> List[Dict]:
        """
        Parse Notariado.org.br API response into our Tenant model format.
        Reference: https://www.notariado.org.br/cartorios/search/
        """
        cartorios = []
        
        # Handle different response structures
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Try common keys for API responses
            items = (
                data.get('cartorios') or 
                data.get('data') or 
                data.get('results') or
                data.get('items') or
                data.get('lista') or
                [data]  # Single item
            )
        
        for item in items:
            if isinstance(item, dict):
                # Map Notariado.org.br fields to our model
                nome = (
                    item.get('nome') or 
                    item.get('razao_social') or 
                    item.get('nome_fantasia') or
                    item.get('cartorio') or
                    item.get('nome_cartorio') or
                    item.get('denominacao') or
                    item.get('nome_oficial')
                )
                
                municipio = (
                    item.get('municipio') or 
                    item.get('cidade') or
                    item.get('município') or
                    item.get('localidade')
                )
                
                # Ensure UF matches (use provided UF if not in response)
                item_uf = (
                    item.get('uf') or 
                    item.get('estado') or
                    item.get('sigla_uf') or
                    uf
                )
                
                tipo = (
                    item.get('tipo') or 
                    item.get('categoria') or
                    item.get('natureza') or
                    item.get('oficio') or
                    item.get('tipo_oficio') or
                    item.get('servico') or
                    item.get('tipo_servico')
                )
                
                if nome:
                    cartorios.append({
                        'nome': nome.strip(),
                        'municipio': municipio.strip() if municipio else None,
                        'uf': item_uf.strip().upper(),
                        'tipo': tipo.strip() if tipo else None,
                    })
        
        return cartorios

    def parse_cnj_data(self, data: Dict) -> List[Dict]:
        """
        Parse CNJ data format into our Tenant model format.
        Adjust based on actual CNJ data structure.
        """
        cartorios = []
        
        # Handle different JSON structures
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Try common keys
            items = (
                data.get('cartorios') or 
                data.get('data') or 
                data.get('results') or
                [data]  # Single item
            )
        
        for item in items:
            if isinstance(item, dict):
                nome = (
                    item.get('nome') or 
                    item.get('razao_social') or 
                    item.get('nome_fantasia') or
                    item.get('cartorio') or
                    item.get('nome_cartorio')
                )
                
                municipio = (
                    item.get('municipio') or 
                    item.get('cidade') or
                    item.get('município')
                )
                
                uf = (
                    item.get('uf') or 
                    item.get('estado') or
                    item.get('sigla_uf')
                )
                
                tipo = (
                    item.get('tipo') or 
                    item.get('categoria') or
                    item.get('natureza') or
                    item.get('oficio') or
                    item.get('tipo_oficio')
                )
                
                if nome and uf:
                    cartorios.append({
                        'nome': nome.strip(),
                        'municipio': municipio.strip() if municipio else None,
                        'uf': uf.strip().upper(),
                        'tipo': tipo.strip() if tipo else None,
                    })
        
        return cartorios

    def get_sample_cartorios(self, uf: str) -> List[Dict]:
        """Get sample cartório data for testing"""
        sample_data = {
            'RJ': [
                {'nome': '1º Cartório de Registro de Imóveis', 'municipio': 'Rio de Janeiro', 'uf': 'RJ', 'tipo': '1º Ofício'},
                {'nome': '2º Cartório de Registro de Imóveis', 'municipio': 'Rio de Janeiro', 'uf': 'RJ', 'tipo': '2º Ofício'},
                {'nome': '3º Cartório de Registro de Imóveis', 'municipio': 'Rio de Janeiro', 'uf': 'RJ', 'tipo': '3º Ofício'},
                {'nome': 'Cartório de Notas de Copacabana', 'municipio': 'Rio de Janeiro', 'uf': 'RJ', 'tipo': 'Notas'},
                {'nome': 'Cartório de Notas de Ipanema', 'municipio': 'Rio de Janeiro', 'uf': 'RJ', 'tipo': 'Notas'},
                {'nome': 'Cartório de Registro Civil de Botafogo', 'municipio': 'Rio de Janeiro', 'uf': 'RJ', 'tipo': 'Registro Civil'},
                {'nome': 'Cartório de Registro Civil de Tijuca', 'municipio': 'Rio de Janeiro', 'uf': 'RJ', 'tipo': 'Registro Civil'},
                {'nome': 'Cartório de Registro de Imóveis de Niterói', 'municipio': 'Niterói', 'uf': 'RJ', 'tipo': '1º Ofício'},
                {'nome': 'Cartório de Notas de Niterói', 'municipio': 'Niterói', 'uf': 'RJ', 'tipo': 'Notas'},
                {'nome': 'Cartório de Registro Civil de Duque de Caxias', 'municipio': 'Duque de Caxias', 'uf': 'RJ', 'tipo': 'Registro Civil'},
            ],
            'SP': [
                {'nome': '1º Cartório de Registro de Imóveis', 'municipio': 'São Paulo', 'uf': 'SP', 'tipo': '1º Ofício'},
                {'nome': '2º Cartório de Registro de Imóveis', 'municipio': 'São Paulo', 'uf': 'SP', 'tipo': '2º Ofício'},
                {'nome': '3º Cartório de Registro de Imóveis', 'municipio': 'São Paulo', 'uf': 'SP', 'tipo': '3º Ofício'},
                {'nome': 'Cartório de Notas da Sé', 'municipio': 'São Paulo', 'uf': 'SP', 'tipo': 'Notas'},
                {'nome': 'Cartório de Notas de Pinheiros', 'municipio': 'São Paulo', 'uf': 'SP', 'tipo': 'Notas'},
                {'nome': 'Cartório de Registro Civil de Vila Mariana', 'municipio': 'São Paulo', 'uf': 'SP', 'tipo': 'Registro Civil'},
                {'nome': 'Cartório de Registro Civil de Santana', 'municipio': 'São Paulo', 'uf': 'SP', 'tipo': 'Registro Civil'},
                {'nome': 'Cartório de Registro de Imóveis de Campinas', 'municipio': 'Campinas', 'uf': 'SP', 'tipo': '1º Ofício'},
                {'nome': 'Cartório de Notas de Campinas', 'municipio': 'Campinas', 'uf': 'SP', 'tipo': 'Notas'},
                {'nome': 'Cartório de Registro Civil de Guarulhos', 'municipio': 'Guarulhos', 'uf': 'SP', 'tipo': 'Registro Civil'},
            ],
            'MG': [
                {'nome': '1º Cartório de Registro de Imóveis', 'municipio': 'Belo Horizonte', 'uf': 'MG', 'tipo': '1º Ofício'},
                {'nome': '2º Cartório de Registro de Imóveis', 'municipio': 'Belo Horizonte', 'uf': 'MG', 'tipo': '2º Ofício'},
                {'nome': 'Cartório de Notas Centro', 'municipio': 'Belo Horizonte', 'uf': 'MG', 'tipo': 'Notas'},
                {'nome': 'Cartório de Notas Savassi', 'municipio': 'Belo Horizonte', 'uf': 'MG', 'tipo': 'Notas'},
                {'nome': 'Cartório de Registro Civil de Belo Horizonte', 'municipio': 'Belo Horizonte', 'uf': 'MG', 'tipo': 'Registro Civil'},
                {'nome': 'Cartório de Registro de Imóveis de Uberlândia', 'municipio': 'Uberlândia', 'uf': 'MG', 'tipo': '1º Ofício'},
                {'nome': 'Cartório de Notas de Uberlândia', 'municipio': 'Uberlândia', 'uf': 'MG', 'tipo': 'Notas'},
                {'nome': 'Cartório de Registro Civil de Contagem', 'municipio': 'Contagem', 'uf': 'MG', 'tipo': 'Registro Civil'},
                {'nome': 'Cartório de Registro de Imóveis de Juiz de Fora', 'municipio': 'Juiz de Fora', 'uf': 'MG', 'tipo': '1º Ofício'},
                {'nome': 'Cartório de Notas de Juiz de Fora', 'municipio': 'Juiz de Fora', 'uf': 'MG', 'tipo': 'Notas'},
            ],
        }
        
        return sample_data.get(uf, [])

