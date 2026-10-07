describe('HITL Editor Functionality', () => {
  beforeEach(() => {
    cy.login('admin', 'admin')
    cy.selectTenant('Test Cartório')
  })

  describe('Editor Initialization', () => {
    it('should load editor with existing minuta', () => {
      // Create a minuta first
      cy.createMinuta('Criar procuração simples').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Editor should be visible
        cy.get('[data-testid="editor-content"]').should('be.visible')
        
        // Toolbar should be visible
        cy.get('[data-testid="editor-toolbar"]').should('be.visible')
      })
    })

    it('should display minuta metadata', () => {
      cy.createMinuta('Criar certidão').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Should show version, status, created by
        cy.get('[data-testid="minuta-version"]').should('contain.text', 'Versão')
        cy.get('[data-testid="minuta-status"]').should('be.visible')
        cy.get('[data-testid="minuta-created-by"]').should('be.visible')
      })
    })
  })

  describe('Text Editing', () => {
    it('should allow text editing in draft mode', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Editor should be editable
        cy.get('[data-testid="editor-content"]')
          .should('have.attr', 'contenteditable', 'true')
        
        // Type some text
        cy.get('[data-testid="editor-content"]')
          .type(' - Texto adicionado pelo usuário')
        
        // Text should appear
        cy.get('[data-testid="editor-content"]')
          .should('contain.text', 'Texto adicionado pelo usuário')
      })
    })

    it('should prevent editing when minuta is approved', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        // Approve the minuta
        cy.approveMinuta(minutaId)
        
        // Visit again
        cy.visit(`/minutas/${minutaId}`)
        
        // Editor should be read-only
        cy.get('[data-testid="editor-content"]')
          .should('have.attr', 'contenteditable', 'false')
      })
    })
  })

  describe('Formatting Toolbar', () => {
    beforeEach(() => {
      cy.createMinuta('Criar procuração teste').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
      })
    })

    it('should apply bold formatting', () => {
      cy.get('[data-testid="editor-content"]').type('Texto importante')
      cy.get('[data-testid="editor-content"]').type('{selectall}')
      
      cy.get('[data-testid="toolbar-bold"]').click()
      
      cy.get('[data-testid="editor-content"]').within(() => {
        cy.get('strong').should('contain.text', 'Texto importante')
      })
    })

    it('should apply italic formatting', () => {
      cy.get('[data-testid="editor-content"]').type('Texto enfatizado')
      cy.get('[data-testid="editor-content"]').type('{selectall}')
      
      cy.get('[data-testid="toolbar-italic"]').click()
      
      cy.get('[data-testid="editor-content"]').within(() => {
        cy.get('em').should('contain.text', 'Texto enfatizado')
      })
    })

    it('should apply underline formatting', () => {
      cy.get('[data-testid="editor-content"]').type('Texto sublinhado')
      cy.get('[data-testid="editor-content"]').type('{selectall}')
      
      cy.get('[data-testid="toolbar-underline"]').click()
      
      cy.get('[data-testid="editor-content"]').within(() => {
        cy.get('u').should('contain.text', 'Texto sublinhado')
      })
    })

    it('should create headings', () => {
      cy.get('[data-testid="editor-content"]').type('Título Principal')
      cy.get('[data-testid="editor-content"]').type('{selectall}')
      
      cy.get('[data-testid="toolbar-heading1"]').click()
      
      cy.get('[data-testid="editor-content"]').within(() => {
        cy.get('h1').should('contain.text', 'Título Principal')
      })
    })

    it('should create bullet lists', () => {
      cy.get('[data-testid="toolbar-bullet-list"]').click()
      
      cy.get('[data-testid="editor-content"]').type('Item 1{enter}Item 2{enter}Item 3')
      
      cy.get('[data-testid="editor-content"]').within(() => {
        cy.get('ul li').should('have.length', 3)
      })
    })

    it('should create numbered lists', () => {
      cy.get('[data-testid="toolbar-numbered-list"]').click()
      
      cy.get('[data-testid="editor-content"]').type('Primeiro{enter}Segundo{enter}Terceiro')
      
      cy.get('[data-testid="editor-content"]').within(() => {
        cy.get('ol li').should('have.length', 3)
      })
    })
  })

  describe('Undo/Redo Functionality', () => {
    beforeEach(() => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
      })
    })

    it('should undo recent changes', () => {
      const originalText = 'Texto original'
      const addedText = ' - Adicionado'
      
      cy.get('[data-testid="editor-content"]').type(originalText)
      cy.get('[data-testid="editor-content"]').type(addedText)
      
      // Undo
      cy.get('[data-testid="toolbar-undo"]').click()
      
      // Added text should be removed
      cy.get('[data-testid="editor-content"]')
        .should('not.contain.text', addedText)
    })

    it('should redo undone changes', () => {
      const text = 'Texto para testar redo'
      
      cy.get('[data-testid="editor-content"]').type(text)
      
      // Undo
      cy.get('[data-testid="toolbar-undo"]').click()
      cy.get('[data-testid="editor-content"]').should('not.contain.text', text)
      
      // Redo
      cy.get('[data-testid="toolbar-redo"]').click()
      cy.get('[data-testid="editor-content"]').should('contain.text', text)
    })
  })

  describe('Save Functionality', () => {
    it('should save changes to minuta', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Make changes
        cy.get('[data-testid="editor-content"]').type(' - Alteração salva')
        
        // Save
        cy.get('[data-testid="save-button"]').click()
        
        // Success message should appear
        cy.contains(/salv(o|a) com sucesso|saved successfully/i, { timeout: 10000 })
          .should('be.visible')
        
        // Reload page
        cy.reload()
        
        // Changes should persist
        cy.get('[data-testid="editor-content"]')
          .should('contain.text', 'Alteração salva')
      })
    })

    it('should track edit confidence score', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        // Make substantial changes
        cy.get('[data-testid="editor-content"]').clear()
        cy.get('[data-testid="editor-content"]').type('Conteúdo completamente novo')
        
        // Confidence score should update
        cy.get('[data-testid="edit-confidence"]').should('exist')
        cy.get('[data-testid="edit-confidence"]').invoke('text').then((text) => {
          // Confidence should be lower after major edits
          expect(text).to.match(/[0-9]+%/)
        })
      })
    })
  })

  describe('Character Count', () => {
    it('should display character count', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-testid="character-count"]').should('be.visible')
        cy.get('[data-testid="character-count"]').should('match', /[0-9]+ caracteres/)
      })
    })

    it('should update character count as user types', () => {
      cy.createMinuta('Criar procuração').then((minutaId) => {
        cy.visit(`/minutas/${minutaId}`)
        
        cy.get('[data-testid="character-count"]').invoke('text').then((initialCount) => {
          cy.get('[data-testid="editor-content"]').type('Texto adicional para teste')
          
          cy.get('[data-testid="character-count"]').invoke('text').should((newCount) => {
            expect(newCount).to.not.equal(initialCount)
          })
        })
      })
    })
  })
})

