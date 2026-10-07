/// <reference types="cypress" />

// ***********************************************
// Custom Cypress Commands for Notarius Frontend
// ***********************************************

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Custom command to login
       * @example cy.login('testuser', 'password123')
       */
      login(username: string, password: string): Chainable<void>
      
      /**
       * Custom command to select a tenant
       * @example cy.selectTenant('Cartório 1')
       */
      selectTenant(tenantName: string): Chainable<void>
      
      /**
       * Custom command to create a minuta via AI
       * @example cy.createMinuta('Criar procuração para João Silva')
       */
      createMinuta(command: string): Chainable<string>
      
      /**
       * Custom command to approve a minuta
       * @example cy.approveMinuta('minuta-id-123')
       */
      approveMinuta(minutaId: string): Chainable<void>
      
      /**
       * Custom command to finalize and download PDF
       * @example cy.downloadPDF('minuta-id-123')
       */
      downloadPDF(minutaId: string): Chainable<void>
      
      /**
       * Custom command to resolve a PII placeholder
       * @example cy.resolvePlaceholder('PII_NOME_abc123')
       */
      resolvePlaceholder(token: string): Chainable<string>
      
      /**
       * Wait for AI generation to complete
       * @example cy.waitForAI()
       */
      waitForAI(): Chainable<void>
    }
  }
}

// Login command
Cypress.Commands.add('login', (username: string, password: string) => {
  cy.session([username, password], () => {
    cy.visit('/login')
    cy.get('input[name="username"]').type(username)
    cy.get('input[name="password"]').type(password)
    cy.get('button[type="submit"]').click()
    
    // Wait for redirect to dashboard
    cy.url().should('include', '/')
    cy.url().should('not.include', '/login')
    
    // Verify token is stored
    cy.window().then((win) => {
      const token = win.localStorage.getItem('auth_token')
      expect(token).to.exist
    })
  })
})

// Select tenant command
Cypress.Commands.add('selectTenant', (tenantName: string) => {
  cy.get('[data-testid="tenant-selector"]').click()
  cy.contains(tenantName).click()
  
  // Verify tenant ID is stored
  cy.window().then((win) => {
    const tenantId = win.localStorage.getItem('tenant_id')
    expect(tenantId).to.exist
  })
})

// Create minuta command
Cypress.Commands.add('createMinuta', (command: string) => {
  cy.visit('/criar')
  cy.get('textarea[name="command"]').type(command)
  cy.get('button[type="submit"]').click()
  
  // Wait for AI generation
  cy.waitForAI()
  
  // Get the created minuta ID from URL or response
  cy.url().then((url) => {
    const match = url.match(/minutas\/([a-f0-9-]+)/)
    if (match) {
      return cy.wrap(match[1])
    }
    return cy.wrap('')
  })
})

// Approve minuta command
Cypress.Commands.add('approveMinuta', (minutaId: string) => {
  cy.visit(`/minutas/${minutaId}`)
  cy.get('[data-testid="approve-button"]').click()
  
  // Confirm approval dialog if present
  cy.get('button').contains('Confirmar').click({ force: true })
  
  // Wait for success message
  cy.contains('aprovada com sucesso', { timeout: 10000 }).should('be.visible')
})

// Download PDF command
Cypress.Commands.add('downloadPDF', (minutaId: string) => {
  cy.visit(`/minutas/${minutaId}`)
  cy.get('[data-testid="finalize-button"]').click()
  
  // Wait for PDF generation
  cy.wait(3000)
  
  // Click download button
  cy.get('[data-testid="download-button"]').click()
  
  // Verify download started (file will be in downloads folder)
  cy.wait(1000)
})

// Resolve placeholder command
Cypress.Commands.add('resolvePlaceholder', (token: string) => {
  // Find the placeholder element
  cy.contains(token).click()
  
  // Click resolve button in tooltip
  cy.get('[data-testid="resolve-placeholder-button"]').click()
  
  // Get the resolved value
  cy.get('[data-testid="resolved-value"]').invoke('text')
})

// Wait for AI generation
Cypress.Commands.add('waitForAI', () => {
  // Look for loading indicator
  cy.get('[data-testid="ai-loading"]', { timeout: 30000 }).should('exist')
  
  // Wait for it to disappear
  cy.get('[data-testid="ai-loading"]', { timeout: 30000 }).should('not.exist')
  
  // Wait for editor to be ready
  cy.get('[data-testid="editor-content"]', { timeout: 10000 }).should('be.visible')
})

// Export for TypeScript
export {}

