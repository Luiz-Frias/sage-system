# TypeScript Required Practices

## Overview
This document outlines mandatory practices for TypeScript development. These patterns ensure code quality, maintainability, and type safety across all TypeScript projects.

## Type Safety Requirements

### 1. Strict TypeScript Configuration
All projects must use strict TypeScript settings.

```json
// tsconfig.json - REQUIRED settings
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true
  }
}
```

### 2. Explicit Return Types for Public APIs
All exported functions must have explicit return types.

```typescript
// ❌ INCORRECT: Missing return type
export function calculateTotal(items: Item[]) {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// ✅ REQUIRED: Explicit return type
export function calculateTotal(items: Item[]): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// ✅ REQUIRED: For async functions
export async function fetchUser(id: string): Promise<User | null> {
  const response = await api.get(`/users/${id}`);
  return response.data;
}

// ✅ REQUIRED: For functions that don't return
export function logMessage(message: string): void {
  console.log(`[${new Date().toISOString()}] ${message}`);
}
```

### 3. Interface Documentation
All public interfaces must be documented.

```typescript
// ❌ INCORRECT: No documentation
export interface UserConfig {
  maxLoginAttempts: number;
  sessionTimeout: number;
  enableTwoFactor: boolean;
}

// ✅ REQUIRED: Documented interface
/**
 * Configuration options for user authentication and session management
 */
export interface UserConfig {
  /** Maximum number of failed login attempts before account lockout */
  maxLoginAttempts: number;
  
  /** Session timeout duration in milliseconds */
  sessionTimeout: number;
  
  /** Whether two-factor authentication is enabled for this user */
  enableTwoFactor: boolean;
}
```

### 4. Discriminated Unions for State
Use discriminated unions for representing different states.

```typescript
// ❌ INCORRECT: Ambiguous state
interface ApiResponse {
  data?: User;
  error?: Error;
  loading: boolean;
}

// ✅ REQUIRED: Discriminated union
type ApiResponse<T> = 
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

// Usage enforces exhaustive handling
function handleResponse(response: ApiResponse<User>) {
  switch (response.status) {
    case 'idle':
      return 'Not started';
    case 'loading':
      return 'Loading...';
    case 'success':
      return `User: ${response.data.name}`;
    case 'error':
      return `Error: ${response.error.message}`;
    // TypeScript ensures all cases are handled
  }
}
```

## Error Handling Requirements

### 5. Custom Error Classes
Use custom error classes for domain-specific errors.

```typescript
// ✅ REQUIRED: Custom error class pattern
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode?: number,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = this.constructor.name;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class ValidationError extends AppError {
  constructor(message: string, details?: unknown) {
    super(message, 'VALIDATION_ERROR', 400, details);
  }
}

// ✅ REQUIRED: Type-safe error handling
export function assertValid<T>(
  value: unknown,
  validator: (value: unknown) => value is T,
  errorMessage: string
): asserts value is T {
  if (!validator(value)) {
    throw new ValidationError(errorMessage, { value });
  }
}
```

### 6. Error Boundaries for React Components
All React components must be wrapped in error boundaries.

```typescript
// ✅ REQUIRED: Error boundary implementation
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
    // Send to error reporting service
  }

  private reset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.reset);
      }
      
      return (
        <div>
          <h2>Something went wrong</h2>
          <button onClick={this.reset}>Try again</button>
        </div>
      );
    }

    return this.props.children;
  }
}

// ✅ REQUIRED: Wrap components
export function App() {
  return (
    <ErrorBoundary>
      <MainContent />
    </ErrorBoundary>
  );
}
```

## Input Validation Requirements

### 7. Runtime Type Validation
Validate all external inputs at runtime.

```typescript
// ✅ REQUIRED: Use a validation library (e.g., zod)
import { z } from 'zod';

// Define schemas
const UserInputSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  age: z.number().int().positive().max(150)
});

export type UserInput = z.infer<typeof UserInputSchema>;

// ✅ REQUIRED: Validate API inputs
export async function createUser(input: unknown): Promise<User> {
  // Validates and returns typed data
  const validatedInput = UserInputSchema.parse(input);
  
  return await userService.create(validatedInput);
}

// ✅ REQUIRED: Type guards for custom validation
export function isValidUUID(value: unknown): value is string {
  return typeof value === 'string' && 
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
}
```

## Async Operations Requirements

### 8. Proper Async Error Handling
All async operations must have error handling.

```typescript
// ✅ REQUIRED: Try-catch for async operations
export async function fetchUserData(userId: string): Promise<Result<User>> {
  try {
    const user = await api.get<User>(`/users/${userId}`);
    return { success: true, data: user };
  } catch (error) {
    logger.error('Failed to fetch user', { userId, error });
    return { 
      success: false, 
      error: error instanceof Error ? error : new Error('Unknown error')
    };
  }
}

// ✅ REQUIRED: Timeout for external calls
export async function fetchWithTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number
): Promise<T> {
  const timeout = new Promise<never>((_, reject) => {
    setTimeout(() => reject(new Error('Request timeout')), timeoutMs);
  });
  
  return Promise.race([promise, timeout]);
}

// Usage
const userData = await fetchWithTimeout(
  fetchUserData(userId),
  5000 // 5 second timeout
);
```

### 9. Resource Cleanup
Always clean up resources.

```typescript
// ✅ REQUIRED: Cleanup in React components
export function useWebSocket(url: string) {
  const [socket, setSocket] = useState<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    setSocket(ws);

    // REQUIRED: Cleanup function
    return () => {
      ws.close();
    };
  }, [url]);

  return socket;
}

// ✅ REQUIRED: Cleanup for event listeners
export function useEventListener<K extends keyof WindowEventMap>(
  event: K,
  handler: (ev: WindowEventMap[K]) => void
) {
  useEffect(() => {
    window.addEventListener(event, handler);
    
    // REQUIRED: Remove listener
    return () => {
      window.removeEventListener(event, handler);
    };
  }, [event, handler]);
}

// ✅ REQUIRED: AbortController for fetch requests
export function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchData() {
      try {
        const response = await fetch(url, { signal: controller.signal });
        const data = await response.json();
        setData(data);
      } catch (error) {
        if (error.name !== 'AbortError') {
          console.error('Fetch error:', error);
        }
      } finally {
        setLoading(false);
      }
    }

    fetchData();

    // REQUIRED: Abort on cleanup
    return () => {
      controller.abort();
    };
  }, [url]);

  return { data, loading };
}
```

## Testing Requirements

### 10. Test Coverage Standards
All code must meet minimum test coverage.

```typescript
// ✅ REQUIRED: Unit tests for all exported functions
describe('calculateTotal', () => {
  it('should calculate sum of item prices', () => {
    const items = [
      { price: 10 },
      { price: 20 },
      { price: 30 }
    ];
    
    expect(calculateTotal(items)).toBe(60);
  });

  it('should return 0 for empty array', () => {
    expect(calculateTotal([])).toBe(0);
  });

  it('should handle negative prices', () => {
    const items = [{ price: -10 }, { price: 20 }];
    expect(calculateTotal(items)).toBe(10);
  });
});

// ✅ REQUIRED: Error case testing
describe('fetchUser', () => {
  it('should handle network errors', async () => {
    mockApi.get.mockRejectedValue(new Error('Network error'));
    
    const result = await fetchUser('123');
    
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.message).toBe('Network error');
    }
  });
});

// ✅ REQUIRED: Type testing
import { expectType } from 'tsd';

// Ensure types are correct
expectType<string>(user.id);
expectType<number>(user.age);
expectType<Promise<User | null>>(fetchUser('123'));
```

## Code Organization Requirements

### 11. Module Structure
Follow consistent module organization.

```typescript
// ✅ REQUIRED: Module structure
// user/
// ├── index.ts         // Public exports only
// ├── user.types.ts    // Type definitions
// ├── user.service.ts  // Business logic
// ├── user.utils.ts    // Helper functions
// └── user.test.ts     // Tests

// index.ts - REQUIRED: Explicit exports
export type { User, UserInput } from './user.types';
export { UserService } from './user.service';
export { validateUser, formatUserName } from './user.utils';

// ✅ REQUIRED: Barrel exports for features
// features/index.ts
export * from './authentication';
export * from './user-management';
export * from './data-processing';
```

### 12. Dependency Injection
Use dependency injection for testability.

```typescript
// ✅ REQUIRED: Constructor injection
export class UserService {
  constructor(
    private readonly database: Database,
    private readonly logger: Logger,
    private readonly emailService: EmailService
  ) {}

  async createUser(input: UserInput): Promise<User> {
    this.logger.info('Creating user', { email: input.email });
    
    const user = await this.database.users.create(input);
    await this.emailService.sendWelcomeEmail(user);
    
    return user;
  }
}

// ✅ REQUIRED: Factory pattern for complex initialization
export function createUserService(config: ServiceConfig): UserService {
  const database = new Database(config.database);
  const logger = new Logger(config.logging);
  const emailService = new EmailService(config.email);
  
  return new UserService(database, logger, emailService);
}
```

## Performance Requirements

### 13. Memoization for Expensive Operations
Use memoization for computationally expensive functions.

```typescript
// ✅ REQUIRED: Memoize expensive computations
import { useMemo } from 'react';

export function useFilteredData(data: Item[], filters: Filters) {
  return useMemo(() => {
    return data
      .filter(item => filters.category ? item.category === filters.category : true)
      .filter(item => filters.minPrice ? item.price >= filters.minPrice : true)
      .filter(item => filters.maxPrice ? item.price <= filters.maxPrice : true)
      .sort((a, b) => b.price - a.price);
  }, [data, filters]);
}

// ✅ REQUIRED: Memoize callbacks
import { useCallback } from 'react';

export function useDataHandler() {
  const handleUpdate = useCallback((id: string, updates: Partial<Item>) => {
    // Update logic
  }, []); // Dependencies array required
  
  return { handleUpdate };
}
```

### 14. Lazy Loading
Implement lazy loading for large modules.

```typescript
// ✅ REQUIRED: Lazy load components
import { lazy, Suspense } from 'react';

const HeavyComponent = lazy(() => import('./HeavyComponent'));

export function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <HeavyComponent />
    </Suspense>
  );
}

// ✅ REQUIRED: Dynamic imports for code splitting
export async function loadAnalytics() {
  const { Analytics } = await import('./analytics');
  return new Analytics();
}
```

## Security Requirements

### 15. Input Sanitization
Sanitize all user inputs.

```typescript
// ✅ REQUIRED: Sanitize HTML content
import DOMPurify from 'dompurify';

export function sanitizeHTML(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['p', 'b', 'i', 'em', 'strong', 'a'],
    ALLOWED_ATTR: ['href', 'target']
  });
}

// ✅ REQUIRED: Escape special characters
export function escapeRegExp(string: string): string {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ✅ REQUIRED: Validate URLs
export function isValidUrl(string: string): boolean {
  try {
    const url = new URL(string);
    return url.protocol === 'https:' || url.protocol === 'http:';
  } catch {
    return false;
  }
}
```

## Documentation Requirements

### 16. JSDoc for Public APIs
Document all public functions and classes.

```typescript
// ✅ REQUIRED: JSDoc documentation
/**
 * Calculates the total price of items in the cart
 * @param items - Array of cart items
 * @param discount - Optional discount percentage (0-100)
 * @returns Total price after discount
 * @throws {ValidationError} If discount is invalid
 * @example
 * ```typescript
 * const total = calculateTotal(items, 10); // 10% discount
 * ```
 */
export function calculateTotal(
  items: CartItem[],
  discount?: number
): number {
  if (discount !== undefined && (discount < 0 || discount > 100)) {
    throw new ValidationError('Discount must be between 0 and 100');
  }
  
  const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  return discount ? subtotal * (1 - discount / 100) : subtotal;
}
```

## Enforcement Checklist

- [ ] TypeScript strict mode enabled
- [ ] ESLint configured with required rules
- [ ] Prettier configured for consistent formatting
- [ ] Pre-commit hooks running type checks
- [ ] CI/CD pipeline enforcing all checks
- [ ] Test coverage meets minimum requirements (80%+)
- [ ] All public APIs documented
- [ ] Error boundaries implemented
- [ ] Input validation on all external data
- [ ] Resource cleanup in all components