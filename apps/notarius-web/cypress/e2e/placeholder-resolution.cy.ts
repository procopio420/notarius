describe('PII Placeholder Resolution', () => {
  beforeEach(() => {
    cy.login('admin', 'admin')
    cy.selectTenant('Test Cartório')
  })

  describe('Placeholder Detection', () => {
    it('should detect and highlight PII_NOME tokens', () => {
      cy.createMinuta('Criar procuração para João Silva').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Should have NOME placeholders highlighted
        cy.get('[data-placeholder-type="NOME"]').should('exist')
        cy.get('[data-placeholder-type="NOME"]').should('have.class', 'placeholder-highlight')
      })
    })

    it('should detect and highlight PII_CPF tokens', () => {
      cy.createMinuta('Criar procuração para pessoa com CPF 123.456.789-00').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Should have CPF placeholders highlighted
        cy.get('[data-placeholder-type="CPF"]').should('exist')
      })
    })

    it('should use different colors for different token types', () => {
      cy.createMinuta('Criar procuração para João Silva, CPF 123.456.789-00, endereço Rua A').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Get background colors
        cy.get('[data-placeholder-type="NOME"]').invoke('css', 'background-color').as('nomeColor')
        cy.get('[data-placeholder-type="CPF"]').invoke('css', 'background-color').as('cpfColor')
        
        // Colors should be different
        cy.get('@nomeColor').then((nomeColor) => {
          cy.get('@cpfColor').should('not.equal', nomeColor)
        })
      })
    })
  })

  describe('Placeholder Tooltips', () => {
    it('should show tooltip on hover', () => {
      cy.createMinuta('Criar procuração para João Silva').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Hover over placeholder
        cy.get('[data-placeholder-type="NOME"]').first().trigger('mouseover')
        
        // Tooltip should appear
        cy.get('[data-testid="placeholder-tooltip"]', { timeout: 2000 }).should('be.visible')
      })
    })

    it('should display token type in tooltip', () => {
      cy.createMinuta('Criar procuração para João Silva').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-placeholder-type="NOME"]').first().trigger('mouseover')
        
        cy.get('[data-testid="placeholder-tooltip"]').should('contain.text', 'NOME')
      })
    })

    it('should show token ID in tooltip', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-placeholder-type]').first().trigger('mouseover')
        
        // Tooltip should show the token in format PII_TYPE_xxxxx
        cy.get('[data-testid="placeholder-tooltip"]').should('match', /PII_[A-Z]+_[a-f0-9]+/)
      })
    })
  })

  describe('Placeholder Resolution (Authorized Users)', () => {
    it('should show resolve button for authorized users', () => {
      cy.createMinuta('Criar procuração para João Silva').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-placeholder-type="NOME"]').first().click()
        
        // Resolve button should be visible
        cy.get('[data-testid="resolve-placeholder-button"]').should('be.visible')
      })
    })

    it('should display decrypted value when resolved', () => {
      cy.createMinuta('Criar procuração para João Silva').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-placeholder-type="NOME"]').first().click()
        cy.get('[data-testid="resolve-placeholder-button"]').click()
        
        // Wait for API call
        cy.wait(1000)
        
        // Should show decrypted value
        cy.get('[data-testid="resolved-value"]', { timeout: 5000 })
          .should('be.visible')
          .and('not.be.empty')
      })
    })

    it('should handle resolution errors gracefully', () => {
      cy.intercept('POST', '**/retrieve-pii', {
        statusCode: 403,
        body: { detail: 'Not authorized' }
      }).as('retrievePII')
      
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-placeholder-type]').first().click()
        cy.get('[data-testid="resolve-placeholder-button"]').click()
        
        cy.wait('@retrievePII')
        
        // Should show error message
        cy.contains(/não autorizado|not authorized/i, { timeout: 5000 })
          .should('be.visible')
      })
    })
  })

  describe('Placeholder Count', () => {
    it('should show total placeholder count', () => {
      cy.createMinuta('Criar procuração para João Silva, CPF 123.456.789-00').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Placeholder count should be displayed
        cy.get('[data-testid="placeholder-count"]').should('exist')
        cy.get('[data-testid="placeholder-count"]').invoke('text').then((text) => {
          const count = parseInt(text.match(/\d+/)?.[0] || '0')
          expect(count).to.be.gte(1)
        })
      })
    })

    it('should show resolved placeholder count', () => {
      cy.createMinuta('Criar procuração para João Silva').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Resolve one placeholder
        cy.get('[data-placeholder-type]').first().click()
        cy.get('[data-testid="resolve-placeholder-button"]').click()
        
        cy.wait(1000)
        
        // Resolved count should update
        cy.get('[data-testid="placeholders-resolved"]').should('exist')
      })
    })
  })

  describe('Batch Placeholder Resolution', () => {
    it('should provide option to resolve all placeholders', () => {
      cy.createMinuta('Criar procuração para João Silva, CPF 123.456.789-00').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Should have "Resolver Todos" button
        cy.get('button').contains(/Resolver todos|Resolve all/i).should('be.visible')
      })
    })

    it('should resolve all placeholders when clicked', () => {
      cy.createMinuta('Criar procuração para João Silva, CPF 123.456.789-00').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Get initial placeholder count
        cy.get('[data-placeholder-type]').its('length').as('totalPlaceholders')
        
        // Click resolve all
        cy.get('button').contains(/Resolver todos|Resolve all/i).click()
        
        // Confirm action
        cy.get('button').contains('Confirmar').click()
        
        cy.wait(3000)
        
        // All should be marked as resolved
        cy.get('@totalPlaceholders').then((count) => {
          cy.get('[data-testid="placeholders-resolved"]')
            .should('contain.text', `${count}`)
        })
      })
    })
  })

  describe('Placeholder Privacy Controls', () => {
    it('should hide placeholder values by default', () => {
      cy.createMinuta('Criar procuração para João Silva').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Placeholders should show token, not actual value
        cy.get('[data-placeholder-type="NOME"]').first().should('match', /PII_NOME_[a-f0-9]+/)
      })
    })

    it('should require authorization to view actual values', () => {
      // This test verifies that resolve button calls the PII Vault with auth
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Intercept PII Vault API call
        cy.intercept('POST', '**/retrieve-pii').as('retrievePII')
        
        cy.get('[data-placeholder-type]').first().click()
        cy.get('[data-testid="resolve-placeholder-button"]').click()
        
        // Should make authenticated API call
        cy.wait('@retrievePII').its('request.headers').should('have.property', 'authorization')
      })
    })

    it('should audit placeholder access', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-placeholder-type]').first().click()
        cy.get('[data-testid="resolve-placeholder-button"]').click()
        
        // API call should include user_id for audit
        cy.intercept('POST', '**/retrieve-pii').as('retrievePII')
        
        cy.wait('@retrievePII').its('request.body').should('have.property', 'tenant_id')
      })
    })
  })
})

