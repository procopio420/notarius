describe('Complete End-to-End Workflow', () => {
  it('should complete full workflow: register → login → generate → edit → approve → finalize → download', () => {
    // Step 1: Register new user
    const username = `testuser_${Date.now()}`
    const password = 'SecurePass123!'
    
    cy.visit('/register')
    cy.get('input[name="username"]').type(username)
    cy.get('input[name="email"]').type(`${username}@example.com`)
    cy.get('input[name="password"]').type(password)
    cy.get('input[name="password_confirm"]').type(password)
    cy.get('input[name="first_name"]').type('Test')
    cy.get('input[name="last_name"]').type('User')
    cy.get('button[type="submit"]').click()
    
    // Wait for registration success
    cy.contains(/registr(o|ado)|successfully/i, { timeout: 10000 }).should('be.visible')
    
    // Step 2: Login with new user
    cy.visit('/login')
    cy.get('input[name="username"]').type(username)
    cy.get('input[name="password"]').type(password)
    cy.get('button[type="submit"]').click()
    
    // Wait for dashboard
    cy.url().should('not.include', '/login')
    cy.wait(1000)
    
    // Step 3: Select tenant
    cy.get('[data-testid="tenant-selector"]', { timeout: 10000 }).should('be.visible')
    cy.selectTenant('Test Cartório')
    
    // Step 4: Generate minuta from natural language
    cy.visit('/criar')
    const command = 'Criar procuração para Ana Costa representar Bruno Lima na venda de veículo'
    cy.get('textarea[name="command"]').type(command)
    cy.get('button').contains('Gerar Documento').click()
    
    // Wait for AI generation
    cy.waitForAI()
    
    // Verify generation successful
    cy.get('[data-testid="editor-content"]').should('be.visible')
    cy.get('[data-testid="editor-content"]').should('contain.text', 'procuração')
    
    // Get minuta ID for later steps
    cy.url().then((url) => {
      const match = url.match(/minutas\/([a-f0-9-]+)/)
      const minutaId = match ? match[1] : ''
      
      cy.wrap(minutaId).as('minutaId')
    })
    
    // Step 5: Edit the generated content
    cy.get('[data-testid="editor-content"]').type(' - CLÁUSULA ADICIONAL: Este documento foi editado pelo usuário.')
    
    // Step 6: Save changes
    cy.get('[data-testid="save-button"]').click()
    cy.contains(/salv(o|a)|saved/i, { timeout: 10000 }).should('be.visible')
    
    // Step 7: Verify placeholders are highlighted
    cy.get('[data-placeholder-type]').should('exist')
    cy.get('[data-placeholder-type]').should('have.length.gte', 1)
    
    // Step 8: Verify citations are displayed
    cy.get('[data-testid="citations-panel"]').should('be.visible')
    cy.get('[data-testid="citation-item"]').should('have.length.gte', 1)
    
    // Step 9: Approve the minuta
    cy.get('[data-testid="approve-button"]').should('be.visible')
    cy.get('[data-testid="approve-button"]').click()
    cy.get('button').contains('Confirmar').click()
    
    // Wait for approval
    cy.contains(/aprovad(o|a)|approved/i, { timeout: 10000 }).should('be.visible')
    
    // Step 10: Verify status changed to aprovado
    cy.get('[data-testid="minuta-status"]').should('contain.text', 'aprovado')
    
    // Step 11: Finalize to generate PDF
    cy.get('[data-testid="finalize-button"]').should('be.visible')
    cy.get('[data-testid="finalize-button"]').click()
    cy.get('button').contains(/Confirmar|Finalizar/i).click()
    
    // Wait for PDF generation
    cy.contains(/gerando|generating/i, { timeout: 5000 }).should('be.visible')
    cy.contains(/finalizad(o|a)|finalized/i, { timeout: 30000 }).should('be.visible')
    
    // Step 12: Download PDF
    cy.get('[data-testid="download-button"]').should('be.visible')
    cy.get('[data-testid="download-button"]').click()
    
    // Wait a moment for download to initiate
    cy.wait(1000)
    
    // Step 13: Verify final status
    cy.get('[data-testid="minuta-status"]').should('contain.text', 'finalizado')
    
    // Step 14: Verify minuta appears in list
    cy.visit('/minutas')
    cy.get('[data-testid="minuta-table"]').within(() => {
      cy.contains(username).should('be.visible') // Created by this user
      cy.contains('finalizado').should('be.visible')
    })
  })

  it('should handle workflow with rejection and recreation', () => {
    cy.login('admin', 'admin')
    cy.selectTenant('Test Cartório')
    
    // Generate minuta
    cy.createMinuta('Criar procuração teste').then((minutaId) => {
      cy.visit(`/minutas/${minutaId}`)
      
      // Reject the minuta
      cy.get('[data-testid="reject-button"]').click()
      cy.get('textarea[name="rejection_reason"]').type('Necessita revisão de cláusulas')
      cy.get('button').contains('Rejeitar').click()
      
      cy.contains(/rejeitad(o|a)|rejected/i, { timeout: 10000 }).should('be.visible')
      
      // Verify cannot approve rejected minuta
      cy.get('[data-testid="approve-button"]').should('not.exist')
      cy.get('[data-testid="finalize-button"]').should('not.exist')
      
      // Create new version
      cy.visit('/criar')
      cy.get('textarea[name="command"]').type('Criar procuração revisada')
      cy.get('button').contains('Gerar Documento').click()
      
      cy.waitForAI()
      
      // New minuta should be in draft status
      cy.get('[data-testid="minuta-status"]').should('contain.text', 'rascunho')
    })
  })

  it('should track complete audit trail', () => {
    cy.login('admin', 'admin')
    cy.selectTenant('Test Cartório')
    
    cy.createMinuta('Criar procuração para auditoria').then((minutaId) => {
      // Edit
      cy.visit(`/minutas/${minutaId}`)
      cy.get('[data-testid="editor-content"]').type(' - Edição 1')
      cy.get('[data-testid="save-button"]').click()
      cy.wait(1000)
      
      // Approve
      cy.get('[data-testid="approve-button"]').click()
      cy.get('button').contains('Confirmar').click()
      cy.wait(2000)
      
      // Check audit trail
      cy.visit(`/minutas/${minutaId}`)
      
      // Should show created by
      cy.get('[data-testid="minuta-created-by"]').should('contain.text', 'admin')
      
      // Should show approved by
      cy.get('[data-testid="approved-by"]').should('contain.text', 'admin')
      
      // Should show approval timestamp
      cy.get('[data-testid="approved-at"]').should('be.visible')
    })
  })
})

