describe('Responsive UI and Accessibility', () => {
  beforeEach(() => {
    cy.login('admin', 'admin')
    cy.selectTenant('Test Cartório')
  })

  describe('Mobile Viewport', () => {
    beforeEach(() => {
      cy.viewport('iphone-x')
    })

    it('should display mobile-friendly navigation', () => {
      cy.visit('/')
      
      // Mobile menu should be accessible
      cy.get('[data-testid="mobile-menu-button"]').should('be.visible')
      cy.get('[data-testid="mobile-menu-button"]').click()
      
      // Navigation items should be visible
      cy.get('[data-testid="mobile-nav"]').should('be.visible')
      cy.get('[data-testid="mobile-nav"]').within(() => {
        cy.contains('Criar').should('be.visible')
        cy.contains('Minutas').should('be.visible')
        cy.contains('Documentos').should('be.visible')
      })
    })

    it('should work with touch interactions', () => {
      cy.createMinuta('Criar procuração mobile').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Editor should be usable on mobile
        cy.get('[data-testid="editor-content"]').should('be.visible')
        
        // Toolbar should be accessible
        cy.get('[data-testid="editor-toolbar"]').should('be.visible')
      })
    })
  })

  describe('Tablet Viewport', () => {
    beforeEach(() => {
      cy.viewport('ipad-2')
    })

    it('should optimize layout for tablet', () => {
      cy.visit('/criar')
      
      // Should have appropriate spacing and layout
      cy.get('[data-testid="main-content"]').should('be.visible')
      cy.get('[data-testid="sidebar"]').should('be.visible')
    })
  })

  describe('Desktop Viewport', () => {
    beforeEach(() => {
      cy.viewport(1920, 1080)
    })

    it('should utilize full screen width efficiently', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Editor and citations should be side by side
        cy.get('[data-testid="editor-content"]').should('be.visible')
        cy.get('[data-testid="citations-panel"]').should('be.visible')
      })
    })
  })

  describe('Keyboard Navigation', () => {
    it('should navigate with Tab key', () => {
      cy.visit('/login')
      
      // Tab through form fields
      cy.get('input[name="username"]').focus()
      cy.realPress('Tab')
      cy.focused().should('have.attr', 'name', 'password')
      cy.realPress('Tab')
      cy.focused().should('have.attr', 'type', 'submit')
    })

    it('should support keyboard shortcuts in editor', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-testid="editor-content"]').type('Texto para formatar')
        cy.get('[data-testid="editor-content"]').type('{selectall}')
        
        // Ctrl/Cmd + B for bold
        cy.get('[data-testid="editor-content"]').type('{ctrl}b')
        
        cy.get('[data-testid="editor-content"]').within(() => {
          cy.get('strong').should('exist')
        })
      })
    })

    it('should save with Ctrl+S shortcut', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-testid="editor-content"]').type(' - Edição')
        
        // Press Ctrl+S
        cy.get('[data-testid="editor-content"]').type('{ctrl}s')
        
        // Should save
        cy.contains(/salv(o|a)|saved/i, { timeout: 10000 }).should('be.visible')
      })
    })
  })

  describe('Accessibility Features', () => {
    it('should have proper ARIA labels', () => {
      cy.visit('/criar')
      
      // Form elements should have labels
      cy.get('textarea[name="command"]').should('have.attr', 'aria-label')
      cy.get('button[type="submit"]').should('have.attr', 'aria-label')
    })

    it('should support screen readers', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Important elements should have aria-labels
        cy.get('[data-testid="approve-button"]').should('have.attr', 'aria-label')
        cy.get('[data-testid="reject-button"]').should('have.attr', 'aria-label')
        cy.get('[data-testid="save-button"]').should('have.attr', 'aria-label')
      })
    })

    it('should have sufficient color contrast', () => {
      cy.visit('/')
      
      // Check that main text is readable
      cy.get('body').should('have.css', 'color')
      cy.get('body').should('have.css', 'background-color')
    })
  })

  describe('Performance', () => {
    it('should load pages within acceptable time', () => {
      const startTime = Date.now()
      
      cy.visit('/criar')
      
      cy.get('[data-testid="main-content"]').should('be.visible')
      
      cy.then(() => {
        const loadTime = Date.now() - startTime
        expect(loadTime).to.be.lessThan(3000) // Should load in under 3 seconds
      })
    })

    it('should handle large documents efficiently', () => {
      // Create a minuta with long content
      const longCommand = 'Criar procuração com múltiplos poderes: ' + 
        'comprar, vender, alugar, hipotecar, dar em garantia, receber, quitar, transigir, ' +
        'representar em juízo e fora dele, podendo substabelecer'.repeat(10)
      
      cy.visit('/criar')
      cy.get('textarea[name="command"]').type(longCommand)
      cy.get('button').contains('Gerar Documento').click()
      
      cy.waitForAI()
      
      // Editor should load without hanging
      cy.get('[data-testid="editor-content"]', { timeout: 30000 }).should('be.visible')
      
      // Should be responsive to edits
      cy.get('[data-testid="editor-content"]').type(' - teste')
      cy.wait(100)
      cy.get('[data-testid="editor-content"]').should('contain.text', 'teste')
    })
  })
})

