describe('Authentication Flow', () => {
  beforeEach(() => {
    // Clear storage before each test
    cy.clearLocalStorage()
    cy.clearCookies()
  })

  describe('User Registration', () => {
    it('should register a new user successfully', () => {
      cy.visit('/register')
      
      // Fill registration form
      cy.get('input[name="username"]').type('newuser')
      cy.get('input[name="email"]').type('newuser@example.com')
      cy.get('input[name="password"]').type('SecurePass123!')
      cy.get('input[name="password_confirm"]').type('SecurePass123!')
      cy.get('input[name="first_name"]').type('Test')
      cy.get('input[name="last_name"]').type('User')
      
      // Submit form
      cy.get('button[type="submit"]').click()
      
      // Should redirect to login or dashboard
      cy.url().should('not.include', '/register')
      
      // Success message should appear
      cy.contains(/registr(o|ado) com sucesso|successfully registered/i, { timeout: 10000 })
        .should('be.visible')
    })

    it('should show validation errors for invalid input', () => {
      cy.visit('/register')
      
      // Submit without filling form
      cy.get('button[type="submit"]').click()
      
      // Should show validation errors
      cy.contains(/campo obrigatório|required/i).should('be.visible')
    })

    it('should show error for duplicate username', () => {
      cy.visit('/register')
      
      // Try to register with existing username
      cy.get('input[name="username"]').type('admin')
      cy.get('input[name="email"]').type('duplicate@example.com')
      cy.get('input[name="password"]').type('Password123!')
      cy.get('input[name="password_confirm"]').type('Password123!')
      cy.get('button[type="submit"]').click()
      
      // Should show error
      cy.contains(/já existe|already exists/i, { timeout: 10000 }).should('be.visible')
    })
  })

  describe('User Login', () => {
    it('should login with valid credentials', () => {
      cy.visit('/login')
      
      // Fill login form
      cy.get('input[name="username"]').type('admin')
      cy.get('input[name="password"]').type('admin')
      
      // Submit
      cy.get('button[type="submit"]').click()
      
      // Should redirect to dashboard
      cy.url().should('not.include', '/login')
      
      // Token should be stored
      cy.window().then((win) => {
        const token = win.localStorage.getItem('auth_token')
        expect(token).to.exist
      })
    })

    it('should show error for invalid credentials', () => {
      cy.visit('/login')
      
      cy.get('input[name="username"]').type('wronguser')
      cy.get('input[name="password"]').type('wrongpass')
      cy.get('button[type="submit"]').click()
      
      // Should show error message
      cy.contains(/inválid(o|as)|invalid|incorrect/i, { timeout: 10000 })
        .should('be.visible')
    })

    it('should validate required fields', () => {
      cy.visit('/login')
      
      // Submit without credentials
      cy.get('button[type="submit"]').click()
      
      // Should show validation errors
      cy.get('input[name="username"]').should('have.attr', 'required')
      cy.get('input[name="password"]').should('have.attr', 'required')
    })
  })

  describe('User Logout', () => {
    it('should logout successfully', () => {
      // First login
      cy.login('admin', 'admin')
      cy.visit('/')
      
      // Click logout button
      cy.get('[data-testid="logout-button"]').click()
      
      // Should redirect to login
      cy.url().should('include', '/login')
      
      // Token should be removed
      cy.window().then((win) => {
        const token = win.localStorage.getItem('auth_token')
        expect(token).to.not.exist
      })
    })
  })

  describe('Protected Routes', () => {
    it('should redirect unauthenticated users to login', () => {
      // Try to access protected route without login
      cy.visit('/criar')
      
      // Should redirect to login
      cy.url().should('include', '/login')
    })

    it('should allow authenticated users to access protected routes', () => {
      cy.login('admin', 'admin')
      
      // Should be able to access protected route
      cy.visit('/criar')
      cy.url().should('include', '/criar')
    })
  })

  describe('Session Persistence', () => {
    it('should maintain session across page reloads', () => {
      cy.login('admin', 'admin')
      cy.visit('/')
      
      // Reload page
      cy.reload()
      
      // Should still be logged in
      cy.url().should('not.include', '/login')
      cy.window().then((win) => {
        const token = win.localStorage.getItem('auth_token')
        expect(token).to.exist
      })
    })
  })
})

