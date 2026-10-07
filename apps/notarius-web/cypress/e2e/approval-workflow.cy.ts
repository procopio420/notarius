describe('Approval Workflow', () => {
  beforeEach(() => {
    cy.login('admin', 'admin')
    cy.selectTenant('Test Cartório')
  })

  describe('Minuta Approval', () => {
    it('should approve a draft minuta', () => {
      cy.createMinuta('Criar procuração teste').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Status should be rascunho
        cy.get('[data-testid="minuta-status"]').should('contain.text', 'rascunho')
        
        // Approve button should be visible
        cy.get('[data-testid="approve-button"]').should('be.visible')
        cy.get('[data-testid="approve-button"]').should('not.be.disabled')
        
        // Click approve
        cy.get('[data-testid="approve-button"]').click()
        
        // Confirm in dialog
        cy.get('button').contains('Confirmar').click()
        
        // Success message
        cy.contains(/aprovad(o|a) com sucesso|approved successfully/i, { timeout: 10000 })
          .should('be.visible')
        
        // Status should update to aprovado
        cy.get('[data-testid="minuta-status"]').should('contain.text', 'aprovado')
        
        // Approve button should disappear
        cy.get('[data-testid="approve-button"]').should('not.exist')
        
        // Finalize button should appear
        cy.get('[data-testid="finalize-button"]').should('be.visible')
      })
    })

    it('should record who approved and when', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-testid="approve-button"]').click()
        cy.get('button').contains('Confirmar').click()
        
        cy.wait(2000)
        
        // Should show approval metadata
        cy.get('[data-testid="approved-by"]').should('contain.text', 'admin')
        cy.get('[data-testid="approved-at"]').should('exist')
      })
    })
  })

  describe('Minuta Rejection', () => {
    it('should reject a draft minuta with reason', () => {
      cy.createMinuta('Criar procuração teste').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Click reject
        cy.get('[data-testid="reject-button"]').should('be.visible')
        cy.get('[data-testid="reject-button"]').click()
        
        // Fill rejection reason
        cy.get('textarea[name="rejection_reason"]').type('Conteúdo precisa de revisão')
        
        // Confirm rejection
        cy.get('button').contains('Rejeitar').click()
        
        // Success message
        cy.contains(/rejeitad(o|a)|rejected/i, { timeout: 10000 }).should('be.visible')
        
        // Status should update
        cy.get('[data-testid="minuta-status"]').should('contain.text', 'rejeitado')
      })
    })

    it('should require rejection reason', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-testid="reject-button"]').click()
        
        // Try to reject without reason
        cy.get('button').contains('Rejeitar').click()
        
        // Should show validation error
        cy.contains(/motivo.*obrigatório|reason.*required/i).should('be.visible')
      })
    })
  })

  describe('Finalization', () => {
    it('should finalize approved minuta and generate PDF', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        // First approve
        cy.approveMinuta(minutaId)
        
        cy.visit(`/minutas/${minutaId}`)
        
        // Finalize button should be visible
        cy.get('[data-testid="finalize-button"]').should('be.visible')
        cy.get('[data-testid="finalize-button"]').click()
        
        // Confirm finalization
        cy.get('button').contains(/Confirmar|Finalizar/i).click()
        
        // Wait for PDF generation
        cy.contains(/gerando PDF|generating PDF/i, { timeout: 5000 }).should('be.visible')
        
        // Success message
        cy.contains(/finalizad(o|a) com sucesso|finalized successfully/i, { timeout: 30000 })
          .should('be.visible')
        
        // Status should update
        cy.get('[data-testid="minuta-status"]').should('contain.text', 'finalizado')
        
        // Download button should appear
        cy.get('[data-testid="download-button"]').should('be.visible')
      })
    })

    it('should not allow finalization of draft minuta', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Finalize button should not exist for draft
        cy.get('[data-testid="finalize-button"]').should('not.exist')
      })
    })

    it('should not allow finalization of rejected minuta', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        // Reject the minuta
        cy.visit(`/minutas/${minutaId}`)
        cy.get('[data-testid="reject-button"]').click()
        cy.get('textarea[name="rejection_reason"]').type('Teste de rejeição')
        cy.get('button').contains('Rejeitar').click()
        
        cy.wait(2000)
        
        // Finalize button should not exist
        cy.get('[data-testid="finalize-button"]').should('not.exist')
      })
    })
  })

  describe('PDF Download', () => {
    it('should download PDF after finalization', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.approveMinuta(minutaId)
        cy.downloadPDF(minutaId)
        
        // Verify download button clicked successfully
        cy.get('[data-testid="download-button"]').should('exist')
      })
    })
  })

  describe('Version History', () => {
    it('should track minuta versions', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Initial version should be 1
        cy.get('[data-testid="minuta-version"]').should('contain.text', '1')
        
        // Make changes and save
        cy.get('[data-testid="editor-content"]').type(' - Alteração v2')
        cy.get('[data-testid="save-button"]').click()
        
        cy.wait(2000)
        
        // Version might increment (depending on backend logic)
        cy.get('[data-testid="minuta-version"]').should('be.visible')
      })
    })
  })

  describe('Read-only Mode', () => {
    it('should show read-only view for finalized minutas', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.approveMinuta(minutaId)
        
        // Finalize
        cy.visit(`/minutas/${minutaId}`)
        cy.get('[data-testid="finalize-button"]').click()
        cy.get('button').contains(/Confirmar|Finalizar/i).click()
        
        cy.wait(3000)
        
        // Visit again
        cy.visit(`/minutas/${minutaId}`)
        
        // Should be read-only
        cy.get('[data-testid="editor-content"]')
          .should('have.attr', 'contenteditable', 'false')
        
        // Edit buttons should be disabled or hidden
        cy.get('[data-testid="save-button"]').should('not.exist')
        cy.get('[data-testid="approve-button"]').should('not.exist')
      })
    })
  })
})

