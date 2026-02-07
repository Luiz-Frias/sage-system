---
name: Dependency Injection
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# TypeScript Dependency Injection Patterns

## Overview
Dependency Injection (DI) is a design pattern that helps achieve Inversion of Control (IoC) between classes and their dependencies. This document outlines TypeScript-specific DI patterns for building maintainable, testable applications.

## Core Principles

### 1. Constructor Injection
The most common and recommended pattern for TypeScript applications.

```typescript
// Define interfaces for dependencies
interface Logger {
  log(message: string): void;
  error(message: string, error?: Error): void;
}

interface Database {
  connect(): Promise<void>;
  query<T>(sql: string, params?: any[]): Promise<T[]>;
}

// Implement the service with constructor injection
class UserService {
  constructor(
    private readonly logger: Logger,
    private readonly database: Database
  ) {}

  async getUser(id: string): Promise<User | null> {
    try {
      this.logger.log(`Fetching user with id: ${id}`);
      const users = await this.database.query<User>(
        'SELECT * FROM users WHERE id = ?',
        [id]
      );
      return users[0] || null;
    } catch (error) {
      this.logger.error('Failed to fetch user', error as Error);
      throw error;
    }
  }
}
```

### 2. Interface-Based Design
Always depend on interfaces, not concrete implementations.

```typescript
// Bad: Depending on concrete implementation
class OrderService {
  constructor(private emailService: SMTPEmailService) {} // ❌
}

// Good: Depending on interface
interface EmailService {
  sendEmail(to: string, subject: string, body: string): Promise<void>;
}

class OrderService {
  constructor(private emailService: EmailService) {} // ✅
}
```

### 3. Factory Pattern for Complex Dependencies
Use factories when dependencies require complex initialization.

```typescript
interface ServiceFactory<T> {
  create(): T | Promise<T>;
}

class DatabaseFactory implements ServiceFactory<Database> {
  constructor(
    private readonly config: DatabaseConfig,
    private readonly logger: Logger
  ) {}

  async create(): Promise<Database> {
    const db = new PostgresDatabase(this.config);
    await db.connect();
    this.logger.log('Database connection established');
    return db;
  }
}
```

### 4. Composition Root Pattern
Centralize dependency resolution at the application's entry point.

```typescript
// app.ts - Composition root
class Application {
  private container: DIContainer;

  async bootstrap(): Promise<void> {
    this.container = new DIContainer();
    
    // Register dependencies
    this.container.register<Logger>('Logger', ConsoleLogger);
    this.container.register<Database>('Database', PostgresDatabase);
    this.container.register<UserService>('UserService', UserService, [
      'Logger',
      'Database'
    ]);
    
    // Resolve and start application
    const server = this.container.resolve<Server>('Server');
    await server.start();
  }
}
```

### 5. Lightweight DI Container Implementation
A simple, type-safe DI container for TypeScript.

```typescript
type Constructor<T = {}> = new (...args: any[]) => T;
type Token<T> = string | symbol | Constructor<T>;

class DIContainer {
  private services = new Map<Token<any>, any>();
  private singletons = new Map<Token<any>, any>();

  register<T>(
    token: Token<T>,
    implementation: Constructor<T>,
    dependencies: Token<any>[] = [],
    options: { singleton?: boolean } = {}
  ): void {
    this.services.set(token, {
      implementation,
      dependencies,
      singleton: options.singleton ?? true
    });
  }

  resolve<T>(token: Token<T>): T {
    const service = this.services.get(token);
    
    if (!service) {
      throw new Error(`Service not found: ${String(token)}`);
    }

    if (service.singleton && this.singletons.has(token)) {
      return this.singletons.get(token);
    }

    const dependencies = service.dependencies.map((dep: Token<any>) => 
      this.resolve(dep)
    );
    
    const instance = new service.implementation(...dependencies);
    
    if (service.singleton) {
      this.singletons.set(token, instance);
    }

    return instance;
  }
}
```

### 6. Decorator-Based DI (with TypeScript Decorators)
Using decorators for cleaner DI syntax (requires experimental decorators).

```typescript
// Decorator definitions
function Injectable(token?: string) {
  return function (target: any) {
    Reflect.defineMetadata('token', token || target.name, target);
  };
}

function Inject(token: string) {
  return function (target: any, propertyKey: string | symbol, parameterIndex: number) {
    const existingTokens = Reflect.getMetadata('inject:tokens', target) || [];
    existingTokens[parameterIndex] = token;
    Reflect.defineMetadata('inject:tokens', existingTokens, target);
  };
}

// Usage
@Injectable('UserService')
class UserService {
  constructor(
    @Inject('Logger') private logger: Logger,
    @Inject('Database') private database: Database
  ) {}
}
```

## Testing with Dependency Injection

### Mock Injection for Unit Tests
```typescript
describe('UserService', () => {
  let userService: UserService;
  let mockLogger: jest.Mocked<Logger>;
  let mockDatabase: jest.Mocked<Database>;

  beforeEach(() => {
    mockLogger = {
      log: jest.fn(),
      error: jest.fn()
    };
    
    mockDatabase = {
      connect: jest.fn(),
      query: jest.fn()
    };

    userService = new UserService(mockLogger, mockDatabase);
  });

  it('should fetch user successfully', async () => {
    const expectedUser = { id: '1', name: 'John' };
    mockDatabase.query.mockResolvedValue([expectedUser]);

    const user = await userService.getUser('1');

    expect(user).toEqual(expectedUser);
    expect(mockLogger.log).toHaveBeenCalledWith('Fetching user with id: 1');
  });
});
```

## Framework-Specific Patterns

### NestJS Built-in DI
```typescript
import { Injectable, Inject } from '@nestjs/common';

@Injectable()
export class CatsService {
  constructor(
    @Inject('DATABASE_CONNECTION') private connection: Connection,
    private readonly logger: LoggerService
  ) {}
}
```

### InversifyJS Integration
```typescript
import { injectable, inject, Container } from 'inversify';

const TYPES = {
  Logger: Symbol.for('Logger'),
  Database: Symbol.for('Database')
};

@injectable()
class UserService {
  constructor(
    @inject(TYPES.Logger) private logger: Logger,
    @inject(TYPES.Database) private database: Database
  ) {}
}
```

## Best Practices

1. **Keep Dependencies Explicit**: Always inject through constructor, making dependencies clear.
2. **Avoid Service Locator Pattern**: Don't hide dependencies inside classes.
3. **Use Interfaces**: Define contracts for all dependencies.
4. **Single Responsibility**: Each service should have one clear purpose.
5. **Avoid Circular Dependencies**: Design your architecture to prevent circular references.
6. **Scope Management**: Be explicit about service lifetimes (singleton, transient, scoped).

## Anti-Patterns to Avoid

```typescript
// ❌ Service Locator Anti-Pattern
class BadService {
  private logger = ServiceLocator.get<Logger>('Logger'); // Hidden dependency
}

// ❌ Property Injection
class BadService {
  @Inject() logger!: Logger; // Makes testing harder
}

// ❌ Ambient Dependencies
class BadService {
  log(message: string) {
    console.log(message); // Hard-coded dependency
  }
}
```

## Migration Strategy

When migrating legacy code to use DI:

1. **Identify Dependencies**: List all external dependencies in each class.
2. **Extract Interfaces**: Create interfaces for each dependency.
3. **Refactor Constructors**: Move dependencies to constructor parameters.
4. **Update Tests**: Replace real dependencies with mocks.
5. **Introduce Container**: Gradually introduce a DI container starting from entry points.