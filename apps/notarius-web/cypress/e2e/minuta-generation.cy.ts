describe('AI Minuta Generation', () => {
  beforeEach(() => {
    // Login before each test
    cy.login('admin', 'admin')
    cy.selectTenant('Test Cartório')
  })

  describe('Natural Language Command Processing', () => {
    it('should generate procuração from natural language', () => {
      cy.visit('/criar')
      
      // Enter command
      const command = 'Criar procuração para João Silva representar Maria Santos na compra de imóvel'
      cy.get('textarea[name="command"]').type(command)
      
      // Submit
      cy.get('button').contains('Gerar Documento').click()
      
      // Wait for AI generation
      cy.waitForAI()
      
      // Verify editor is loaded with content
      cy.get('[data-testid="editor-content"]').should('be.visible')
      cy.get('[data-testid="editor-content"]').should('contain.text', 'procuração')
      
      // Verify document type detected
      cy.contains('procuração', { matchCase: false }).should('be.visible')
    })

    it('should generate certidão from natural language', () => {
      cy.visit('/criar')
      
      const command = 'Criar certidão de nascimento para Maria da Silva'
      cy.get('textarea[name="command"]').type(command)
      cy.get('button').contains('Gerar Documento').click()
      
      cy.waitForAI()
      
      cy.get('[data-testid="editor-content"]').should('contain.text', 'certidão')
    })

    it('should generate testamento from natural language', () => {
      cy.visit('/criar')
      
      const command = 'Criar testamento para Carlos Mendes, deixando todos os bens para sua filha'
      cy.get('textarea[name="command"]').type(command)
      cy.get('button').contains('Gerar Documento').click()
      
      cy.waitForAI()
      
      cy.get('[data-testid="editor-content"]').should('contain.text', 'testamento')
    })
  })

  describe('PII Token Detection', () => {
    it('should detect and highlight PII tokens in generated content', () => {
      cy.createMinuta('Criar procuração para João Silva')
      
      // Look for PII tokens in format PII_TYPE_xxxxx
      cy.get('[data-testid="editor-content"]').within(() => {
        cy.get('[data-placeholder-type]').should('exist')
      })
    })

    it('should show token type on hover', () => {
      cy.createMinuta('Criar procuração para João Silva CPF 123.456.789-00')
      
      // Hover over a PII token
      cy.get('[data-placeholder-type="nome"]').first().trigger('mouseover')
      
      // Tooltip should appear
      cy.get('[data-testid="placeholder-tooltip"]').should('be.visible')
      cy.get('[data-testid="placeholder-tooltip"]').should('contain.text', 'NOME')
    })
  })

  describe('Legal Citations', () => {
    it('should include legal citations in generated minuta', () => {
      cy.createMinuta('Criar procuração simples')
      
      // Verify citations section exists
      cy.get('[data-testid="citations-panel"]').should('exist')
      
      // Should have at least one citation
      cy.get('[data-testid="citation-item"]').should('have.length.gte', 1)
    })

    it('should display citation sources correctly', () => {
      cy.createMinuta('Criar testamento')
      
      cy.get('[data-testid="citations-panel"]').within(() => {
        // Should reference Brazilian legal sources
        cy.contains(/Lei|Código Civil|CGJ/i).should('be.visible')
      })
    })

    it('should show confidence scores for citations', () => {
      cy.createMinuta('Criar escritura de compra e venda')
      
      cy.get('[data-testid="citation-item"]').first().within(() => {
        cy.get('[data-testid="confidence-score"]').should('exist')
        cy.get('[data-testid="confidence-score"]').invoke('text').then((text) => {
          const score = parseFloat(text)
          expect(score).to.be.gte(0)
          expect(score).to.be.lte(1)
        })
      })
    })
  })

  describe('Generation Progress', () => {
    it('should show loading state during generation', () => {
      cy.visit('/criar')
      
      cy.get('textarea[name="command"]').type('Criar procuração')
      cy.get('button').contains('Gerar Documento').click()
      
      // Loading indicator should appear
      cy.get('[data-testid="ai-loading"]').should('be.visible')
      
      // Loading should eventually disappear
      cy.get('[data-testid="ai-loading"]', { timeout: 30000 }).should('not.exist')
    })

    it('should display confidence score after generation', () => {
      cy.createMinuta('Criar procuração simples')
      
      // Confidence score should be displayed
      cy.get('[data-testid="confidence-score"]').should('exist')
      cy.get('[data-testid="confidence-score"]').invoke('text').then((text) => {
        const score = parseFloat(text.replace('%', ''))
        expect(score).to.be.gte(0)
        expect(score).to.be.lte(100)
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle empty command gracefully', () => {
      cy.visit('/criar')
      
      cy.get('button').contains('Gerar Documento').click()
      
      // Should show validation error
      cy.contains(/comando não pode estar vazio|command cannot be empty/i)
        .should('be.visible')
    })

    it('should handle AI service unavailable', () => {
      cy.intercept('POST', '**/generate-from-intent/', {
        statusCode: 503,
        body: { detail: 'Service temporarily unavailable' }
      }).as('generateIntent')
      
      cy.visit('/criar')
      cy.get('textarea[name="command"]').type('Criar procuração')
      cy.get('button').contains('Gerar Documento').click()
      
      // Should show error message
      cy.contains(/serviço indisponível|service unavailable/i, { timeout: 10000 })
        .should('be.visible')
    })

    it('should allow retry after generation failure', () => {
      cy.visit('/criar')
      
      // Mock failure then success
      let callCount = 0
      cy.intercept('POST', '**/generate-from-intent/', (req) => {
        callCount++
        if (callCount === 1) {
          req.reply({ statusCode: 500, body: { detail: 'Internal error' } })
        } else {
          req.continue()
        }
      }).as('generateIntent')
      
      cy.get('textarea[name="command"]').type('Criar procuração')
      cy.get('button').contains('Gerar Documento').click()
      
      // Wait for error
      cy.wait('@generateIntent')
      cy.contains(/erro|error/i).should('be.visible')
      
      // Click retry
      cy.get('button').contains(/tentar novamente|retry/i).click()
      
      // Should succeed on retry
      cy.wait('@generateIntent')
      cy.get('[data-testid="editor-content"]', { timeout: 30000 }).should('be.visible')
    })
  })
})

