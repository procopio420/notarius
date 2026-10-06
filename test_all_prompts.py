#!/usr/bin/env python3
"""
Test all document generation prompts via the Intent Engine API.
This tests the core functionality without requiring authentication.
"""

import requests
import json
import sys
from typing import Dict, List

INTENT_ENGINE_URL = "http://localhost:8003/api/v1/parse-intent"
TENANT_ID = "5c3c87a5-a3db-437d-ab0f-7e5670b1dbb9"
USER_ID = "1"

# All prompts from the user's request
PROMPTS = [
    # Procurações
    {
        "category": "Procurações",
        "name": "Procuração para venda de imóvel",
        "prompt": "Procuração para venda de imóvel. Outorgante: João Silva, CPF 123.456.789-00; Outorgado: Maria Souza, CPF 987.654.321-00. Imóvel localizado na Rua das Flores, 100, São Paulo/SP. Validade de 90 dias."
    },
    {
        "category": "Procurações",
        "name": "Procuração para representação bancária",
        "prompt": "Procuração para representação bancária. Outorgante: Fernanda Lopes, CPF 222.333.444-55; Outorgado: Carlos Pinto, CPF 111.222.333-44. Autoriza movimentar conta no Banco do Brasil, agência 1234, conta 56789-0."
    },
    {
        "category": "Procurações",
        "name": "Procuração ad judicia",
        "prompt": "Procuração ad judicia. Outorgante: Pedro Mendes, CPF 987.111.222-33; Outorgado: Dra. Ana Beatriz Rocha, OAB/SP 123456. Concede poderes para representá-lo em processo de separação judicial."
    },
    # Reconhecimento de Firma / Autorização
    {
        "category": "Reconhecimento de Firma / Autorização",
        "name": "Autorização para transferência de veículo",
        "prompt": "Autorização para transferência de veículo. Proprietário: Marcos Lima, CPF 456.789.123-00; Veículo: Honda Civic 2018, placa ABC-1234; Comprador: Paula Ramos, CPF 789.654.321-00."
    },
    {
        "category": "Reconhecimento de Firma / Autorização",
        "name": "Autorização para viagem de menor",
        "prompt": "Autorização para viagem de menor. Menor: Lucas Almeida, 12 anos, RG 1234567; Pais: Bruno Almeida e Carla Almeida; Destino: Lisboa, Portugal; Período: 10/12/2025 a 10/01/2026."
    },
    # Declarações
    {
        "category": "Declarações",
        "name": "Declaração de união estável",
        "prompt": "Declaração de união estável. Declarante 1: Gustavo Nogueira, CPF 321.654.987-00; Declarante 2: Carolina Figueira, CPF 987.321.654-00. União iniciada em 15/03/2020, com residência comum em Belo Horizonte/MG."
    },
    {
        "category": "Declarações",
        "name": "Declaração de residência",
        "prompt": "Declaração de residência. Declarante: Juliana Ferreira, CPF 654.321.987-00; Endereço: Rua das Laranjeiras, 250, Rio de Janeiro/RJ."
    },
    {
        "category": "Declarações",
        "name": "Declaração de herdeiro",
        "prompt": "Declaração de herdeiro. Declarante: André Souza, CPF 123.123.123-00; Declara ser filho legítimo de José Souza, falecido em 10/01/2024, conforme certidão de óbito."
    },
    # Atas e Certidões
    {
        "category": "Atas e Certidões",
        "name": "Ata notarial de constatação",
        "prompt": "Ata notarial de constatação. Solicitante: Rafael Gomes, CPF 111.444.777-99; Descrição: Registrar conteúdo publicado em perfil de rede social Instagram em 05/11/2025."
    },
    {
        "category": "Atas e Certidões",
        "name": "Certidão de casamento",
        "prompt": "Certidão de casamento. Nome dos cônjuges: Ricardo Oliveira e Bruna Castro. Casamento realizado em 20/06/2018 no Cartório de São José dos Campos/SP."
    },
    # Outros tipos úteis
    {
        "category": "Outros tipos úteis",
        "name": "Testamento público",
        "prompt": "Testamento público. Testador: Margarida Alves, CPF 999.888.777-66; Declara seus bens e disposições de última vontade conforme lista anexa."
    },
    {
        "category": "Outros tipos úteis",
        "name": "Escritura de compra e venda",
        "prompt": "Escritura de compra e venda. Vendedor: Eduardo Rocha, CPF 333.222.111-00; Compradora: Marina Costa, CPF 555.444.333-22; Imóvel em Curitiba/PR, matrícula 12345; Valor R$ 450.000,00."
    },
]

def test_prompt(prompt_data: Dict) -> Dict:
    """Test a single prompt."""
    category = prompt_data["category"]
    name = prompt_data["name"]
    prompt = prompt_data["prompt"]
    
    print(f"\n{'='*80}")
    print(f"Testing: {category} - {name}")
    print(f"{'='*80}")
    print(f"Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"Prompt: {prompt}")
    print("-" * 80)
    
    try:
        response = requests.post(
            INTENT_ENGINE_URL,
            json={
                "intent": prompt,
                "processo_id": None,
                "tenant_id": TENANT_ID,
                "user_id": USER_ID
            },
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            parsed_intent = data.get("parsed_intent", {})
            
            print(f"✅ SUCCESS")
            print(f"Document Type: {parsed_intent.get('document_type', 'N/A')}")
            print(f"Confidence: {parsed_intent.get('confidence', 0):.2%}")
            
            # Show entities
            entities = parsed_intent.get('entities', {})
            if entities:
                print(f"\nEntities found:")
                for key, value in list(entities.items())[:5]:  # Show first 5
                    if isinstance(value, dict):
                        print(f"  - {key}: {value.get('nome', value.get('name', value))}")
                    else:
                        print(f"  - {key}: {value}")
            
            # Show PII fields
            pii_fields = parsed_intent.get('pii_fields', [])
            if pii_fields:
                print(f"PII Fields: {', '.join(pii_fields)}")
            
            return {
                "success": True,
                "category": category,
                "name": name,
                "document_type": parsed_intent.get('document_type'),
                "confidence": parsed_intent.get('confidence', 0),
                "entities_count": len(entities) if entities else 0,
                "pii_fields": pii_fields
            }
        else:
            error_msg = response.text[:200]
            print(f"❌ FAILED (Status: {response.status_code})")
            print(f"Error: {error_msg}")
            return {
                "success": False,
                "category": category,
                "name": name,
                "error": error_msg,
                "status_code": response.status_code
            }
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {
            "success": False,
            "category": category,
            "name": name,
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("NOTARIUS DOCUMENT GENERATION PROMPT TESTING")
    print("=" * 80)
    print(f"Testing against: {INTENT_ENGINE_URL}")
    print(f"Total prompts: {len(PROMPTS)}")
    print("=" * 80)
    
    # Check if intent engine is accessible
    try:
        health_check = requests.get("http://localhost:8003/health", timeout=5)
        if health_check.status_code != 200:
            print("⚠️  Warning: Intent engine health check failed")
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to intent engine: {e}")
        print("Make sure the intent engine is running on port 8003")
        sys.exit(1)
    
    results = []
    passed = 0
    failed = 0
    
    for prompt_data in PROMPTS:
        result = test_prompt(prompt_data)
        results.append(result)
        
        if result["success"]:
            passed += 1
        else:
            failed += 1
    
    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(PROMPTS)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/len(PROMPTS))*100:.1f}%")
    print("=" * 80)
    
    # Show failed tests
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for result in results:
            if not result["success"]:
                print(f"  - {result['category']} - {result['name']}")
                if "error" in result:
                    error = result['error'][:100]
                    print(f"    Error: {error}")
    
    # Show document types distribution
    print("\n📊 DOCUMENT TYPES DETECTED:")
    doc_types = {}
    for result in results:
        if result["success"] and "document_type" in result:
            doc_type = result["document_type"] or "unknown"
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
    
    for doc_type, count in sorted(doc_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {doc_type}: {count}")
    
    # Save results
    with open("prompt_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Detailed results saved to: prompt_test_results.json")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

