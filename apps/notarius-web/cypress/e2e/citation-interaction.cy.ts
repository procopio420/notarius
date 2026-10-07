describe('Legal Citation Interaction', () => {
  beforeEach(() => {
    cy.login('admin', 'admin')
    cy.selectTenant('Test Cartório')
  })

  describe('Citation Display', () => {
    it('should display citations panel in generated minuta', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Citations panel should be visible
        cy.get('[data-testid="citations-panel"]').should('be.visible')
      })
    })

    it('should list all citations used in document', () => {
      cy.createMinuta('Criar procuração com poderes especiais').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-testid="citations-panel"]').within(() => {
          // Should have citation items
          cy.get('[data-testid="citation-item"]').should('have.length.gte', 1)
        })
      })
    })

    it('should display citation details', () => {
      cy.createMinuta('Criar testamento').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-testid="citation-item"]').first().within(() => {
          // Should show source
          cy.get('[data-testid="citation-source"]').should('be.visible')
          
          // Should show article/section
          cy.get('[data-testid="citation-article"]').should('be.visible')
          
          // Should show confidence score
          cy.get('[data-testid="citation-confidence"]').should('exist')
        })
      })
    })
  })

  describe('Citation Tooltips', () => {
    it('should show tooltip when hovering over citation in text', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Find citation reference in text (format: [Lei 8.935/1994, Art. 1º])
        cy.get('[data-testid="editor-content"]').within(() => {
          cy.get('[data-citation-ref]').first().trigger('mouseover')
        })
        
        // Citation tooltip should appear
        cy.get('[data-testid="citation-tooltip"]', { timeout: 2000 }).should('be.visible')
      })
    })

    it('should display full citation text in tooltip', () => {
      cy.createMinuta('Criar testamento público').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-citation-ref]').first().trigger('mouseover')
        
        cy.get('[data-testid="citation-tooltip"]').within(() => {
          // Should show full citation text/excerpt
          cy.get('[data-testid="citation-excerpt"]').should('be.visible')
          cy.get('[data-testid="citation-excerpt"]').should('not.be.empty')
        })
      })
    })

    it('should show citation confidence score in tooltip', () => {
      cy.createMinuta('Criar escritura').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-citation-ref]').first().trigger('mouseover')
        
        cy.get('[data-testid="citation-tooltip"]').within(() => {
          cy.get('[data-testid="citation-confidence"]').should('exist')
          cy.get('[data-testid="citation-confidence"]').invoke('text').then((text) => {
            expect(text).to.match(/[0-9]+%/)
          })
        })
      })
    })
  })

  describe('Citation Links', () => {
    it('should provide link to original source', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-testid="citation-item"]').first().within(() => {
          cy.get('[data-testid="citation-link"]').should('have.attr', 'href')
        })
      })
    })

    it('should open citation source in new tab', () => {
      cy.createMinuta('Criar testamento').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-testid="citation-item"]').first().within(() => {
          cy.get('[data-testid="citation-link"]')
            .should('have.attr', 'target', '_blank')
        })
      })
    })
  })

  describe('Citation Visibility Toggle', () => {
    it('should toggle citations panel visibility', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Citations should be visible by default
        cy.get('[data-testid="citations-panel"]').should('be.visible')
        
        // Click toggle button
        cy.get('[data-testid="toggle-citations"]').click()
        
        // Citations should be hidden
        cy.get('[data-testid="citations-panel"]').should('not.be.visible')
        
        // Click again to show
        cy.get('[data-testid="toggle-citations"]').click()
        cy.get('[data-testid="citations-panel"]').should('be.visible')
      })
    })

    it('should hide citation highlights in text when panel is hidden', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Hide citations
        cy.get('[data-testid="toggle-citations"]').click()
        
        // Citation highlights should be hidden
        cy.get('[data-testid="editor-content"]').within(() => {
          cy.get('[data-citation-ref]').should('not.have.class', 'citation-highlight')
        })
      })
    })
  })

  describe('Citation Quality Indicators', () => {
    it('should show high confidence citations with green indicator', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-testid="citation-item"]').each(($citation) => {
          cy.wrap($citation).within(() => {
            cy.get('[data-testid="citation-confidence"]').invoke('text').then((text) => {
              const confidence = parseFloat(text.replace('%', ''))
              
              if (confidence >= 80) {
                // High confidence should have green indicator
                cy.get('[data-testid="confidence-indicator"]')
                  .should('have.class', /green|success/)
              }
            })
          })
        })
      })
    })

    it('should show low confidence citations with warning indicator', () => {
      // Mock response with low confidence citation
      cy.intercept('POST', '**/generate-from-intent/', (req) => {
        req.reply({
          statusCode: 200,
          body: {
            minuta: {
              id: 'test-id',
              corpo_md: 'Test content',
              citations: [{
                source: 'Test Source',
                article: 'Art. 1',
                confidence: 0.45 // Low confidence
              }]
            }
          }
        })
      }).as('generateIntent')
      
      cy.visit('/criar')
      cy.get('textarea[name="command"]').type('Criar procuração')
      cy.get('button').contains('Gerar Documento').click()
      
      cy.wait('@generateIntent')
      cy.wait(1000)
      
      // Low confidence should have yellow/warning indicator
      cy.get('[data-testid="confidence-indicator"]')
        .should('have.class', /yellow|warning/)
    })
  })

  describe('Citation Grounding', () => {
    it('should display overall grounding confidence', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Overall confidence should be displayed
        cy.get('[data-testid="grounding-confidence"]').should('be.visible')
        cy.get('[data-testid="grounding-confidence"]').invoke('text').then((text) => {
          const confidence = parseFloat(text.replace('%', ''))
          expect(confidence).to.be.gte(0)
          expect(confidence).to.be.lte(100)
        })
      })
    })

    it('should show warning for low grounding confidence', () => {
      // Mock response with low overall confidence
      cy.intercept('POST', '**/generate-from-intent/', {
        statusCode: 200,
        body: {
          minuta: {
            id: 'test-id',
            corpo_md: 'Test content',
            grounding_confidence: 0.55, // Low overall confidence
            citations: []
          }
        }
      }).as('generateIntent')
      
      cy.visit('/criar')
      cy.get('textarea[name="command"]').type('Criar documento complexo')
      cy.get('button').contains('Gerar Documento').click()
      
      cy.wait('@generateIntent')
      cy.wait(1000)
      
      // Should show warning
      cy.contains(/baixa confiança|low confidence/i).should('be.visible')
    })
  })
})

