# TypeScript Project Templates

## Overview
This directory contains starter templates and configuration files for various TypeScript project types. Each template follows best practices and includes necessary tooling setup.

## Available Templates

### Frontend Templates

#### 1. React Starter (`react-starter/`)
Modern React application with TypeScript, featuring:
- React 18+ with TypeScript
- Vite for fast development and building
- React Router for navigation
- State management setup (Context API + Zustand)
- Testing with Vitest and React Testing Library
- ESLint + Prettier configuration
- CSS Modules + Tailwind CSS
- Environment variable handling

#### 2. Vue Starter (`vue-starter/`)
Vue 3 application with TypeScript:
- Vue 3 Composition API
- Vite build tool
- Vue Router 4
- Pinia for state management
- Vitest for testing
- TypeScript strict mode
- Auto-imports setup

#### 3. Solid Starter (`solid-starter/`)
SolidJS application template:
- SolidJS with TypeScript
- Vite configuration
- Solid Router
- Solid Testing Library
- Signal-based reactivity
- Optimized for performance

### Backend Templates

#### 4. Express Starter (`express-starter/`)
REST API with Express and TypeScript:
- Express 4 with TypeScript
- Structured route organization
- Middleware setup (cors, helmet, compression)
- Error handling middleware
- Request validation with Zod
- JWT authentication boilerplate
- Database integration (Prisma)
- Testing with Jest and Supertest

#### 5. Fastify Starter (`fastify-starter/`)
High-performance API with Fastify:
- Fastify 4 with TypeScript
- Schema-based validation
- Plugin architecture
- Swagger/OpenAPI integration
- Structured logging with Pino
- Rate limiting and security plugins
- WebSocket support

#### 6. NestJS Starter (`nestjs-starter/`)
Enterprise-grade Node.js framework:
- NestJS 10 with TypeScript
- Modular architecture
- Dependency injection
- OpenAPI/Swagger documentation
- TypeORM/Prisma integration
- Guards, pipes, and interceptors
- Microservices ready
- Testing setup with Jest

### Configuration Templates

#### 7. Config Files (`configs/`)
Reusable configuration files:

**`tsconfig.base.json`** - Base TypeScript configuration
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "lib": ["ES2022"],
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "moduleResolution": "node",
    "allowJs": false,
    "noEmit": true,
    "incremental": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true
  }
}
```

**`jest.config.js`** - Jest configuration
```javascript
/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.ts', '**/?(*.)+(spec|test).ts'],
  transform: {
    '^.+\\.ts$': 'ts-jest',
  },
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/*.test.ts',
    '!src/**/__tests__/**',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

**`vitest.config.ts`** - Vitest configuration
```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'dist/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData/**',
      ],
    },
  },
});
```

**`playwright.config.ts`** - E2E testing configuration
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    actionTimeout: 0,
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

**`cypress.config.ts`** - Cypress E2E configuration
```typescript
import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    supportFile: 'cypress/support/e2e.ts',
    videosFolder: 'cypress/videos',
    screenshotsFolder: 'cypress/screenshots',
    viewportWidth: 1280,
    viewportHeight: 720,
  },
  component: {
    devServer: {
      framework: 'react',
      bundler: 'vite',
    },
    specPattern: 'src/**/*.cy.{js,jsx,ts,tsx}',
  },
});
```

### Utility Templates

#### 8. Library Starter (`library-starter/`)
For creating reusable TypeScript libraries:
- Rollup for bundling
- Multiple output formats (ESM, CJS, UMD)
- TypeScript declarations generation
- Tree-shaking optimized
- Automated API documentation
- Publishing workflow setup

#### 9. CLI Tool Starter (`cli-starter/`)
Command-line tool template:
- Commander.js for CLI parsing
- Chalk for colorful output
- Progress bars and spinners
- Interactive prompts
- TypeScript compilation to executable
- Auto-completion setup

## Usage

### Quick Start
```bash
# Clone a template
cp -r languages/typescript/templates/react-starter my-new-project
cd my-new-project

# Install dependencies
npm install

# Start development
npm run dev
```

### Customization Checklist
When using a template:

1. **Update Package Information**
   - [ ] Update `package.json` name and description
   - [ ] Update author and license information
   - [ ] Review and adjust dependencies

2. **Configure Environment**
   - [ ] Copy `.env.example` to `.env`
   - [ ] Set up required environment variables
   - [ ] Configure API endpoints

3. **Adjust TypeScript Settings**
   - [ ] Review `tsconfig.json` for project needs
   - [ ] Set appropriate target and lib versions
   - [ ] Configure path aliases if needed

4. **Setup Testing**
   - [ ] Configure test runners
   - [ ] Set up CI/CD test commands
   - [ ] Adjust coverage thresholds

5. **Configure Linting**
   - [ ] Review ESLint rules
   - [ ] Adjust Prettier settings
   - [ ] Set up pre-commit hooks

## Template Structure

Each template follows a consistent structure:

```
template-name/
├── src/                    # Source code
│   ├── components/         # UI components (frontend)
│   ├── routes/            # API routes (backend)
│   ├── services/          # Business logic
│   ├── utils/             # Utility functions
│   ├── types/             # TypeScript type definitions
│   └── index.ts           # Entry point
├── tests/                 # Test files
├── public/                # Static assets (frontend)
├── .env.example           # Environment variables template
├── .eslintrc.js          # ESLint configuration
├── .prettierrc           # Prettier configuration
├── tsconfig.json         # TypeScript configuration
├── package.json          # Dependencies and scripts
├── README.md             # Template documentation
└── .gitignore            # Git ignore patterns
```

## Best Practices

### 1. Type Safety
- Always use strict TypeScript configuration
- Define explicit return types for public APIs
- Avoid `any` type - use `unknown` when type is truly unknown
- Create proper type definitions for all data structures

### 2. Project Organization
- Keep related files close together
- Use barrel exports for clean imports
- Separate concerns (UI, business logic, data access)
- Implement dependency injection for testability

### 3. Testing Strategy
- Write tests alongside implementation
- Aim for 80%+ coverage
- Test edge cases and error scenarios
- Use proper mocking strategies

### 4. Performance
- Implement code splitting for large applications
- Use lazy loading where appropriate
- Optimize bundle sizes
- Profile and monitor performance

### 5. Security
- Validate all inputs
- Sanitize user-generated content
- Use environment variables for secrets
- Implement proper authentication/authorization

## Contributing New Templates

To add a new template:

1. Create a new directory under `templates/`
2. Include all necessary configuration files
3. Add comprehensive README with setup instructions
4. Include example code demonstrating best practices
5. Test the template in a fresh environment
6. Update this README with template description

## Template Maintenance

Templates should be updated regularly to:
- Use latest stable dependency versions
- Incorporate new best practices
- Fix security vulnerabilities
- Improve developer experience

Last updated: 2024