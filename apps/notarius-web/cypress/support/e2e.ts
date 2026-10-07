// ***********************************************************
// This file is processed and loaded automatically before test files.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import './commands'

// Alternatively you can use CommonJS syntax:
// require('./commands')

// Prevent Cypress from failing on uncaught exceptions
Cypress.on('uncaught:exception', (err, runnable) => {
  // Returning false here prevents Cypress from failing the test
  // You can customize this to ignore specific errors
  if (err.message.includes('ResizeObserver') || err.message.includes('hydration')) {
    return false
  }
  return true
})

// Global before hook
before(() => {
  cy.log('Starting Cypress test suite')
})

// Global after hook
after(() => {
  cy.log('Cypress test suite completed')
})

