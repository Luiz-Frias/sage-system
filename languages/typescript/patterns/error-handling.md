# TypeScript Error Handling Patterns

## Overview
Robust error handling is crucial for building reliable TypeScript applications. This document outlines patterns for handling errors effectively, including error boundaries, custom error types, and recovery strategies.

## Core Error Handling Principles

### 1. Custom Error Classes
Create domain-specific error types for better error discrimination.

```typescript
// Base error class with proper prototype chain
abstract class BaseError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode?: number
  ) {
    super(message);
    this.name = this.constructor.name;
    
    // Maintains proper prototype chain for instanceof checks
    Object.setPrototypeOf(this, new.target.prototype);
    
    // Captures stack trace
    Error.captureStackTrace(this, this.constructor);
  }

  toJSON() {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      statusCode: this.statusCode,
      stack: this.stack
    };
  }
}

// Domain-specific errors
class ValidationError extends BaseError {
  constructor(
    message: string,
    public readonly field?: string,
    public readonly value?: unknown
  ) {
    super(message, 'VALIDATION_ERROR', 400);
  }
}

class NotFoundError extends BaseError {
  constructor(
    resource: string,
    identifier: string | number
  ) {
    super(
      `${resource} with identifier ${identifier} not found`,
      'NOT_FOUND',
      404
    );
  }
}

class AuthenticationError extends BaseError {
  constructor(message: string = 'Authentication required') {
    super(message, 'AUTHENTICATION_ERROR', 401);
  }
}
```

### 2. Result Pattern (Railway-Oriented Programming)
Handle errors as values instead of throwing exceptions.

```typescript
// Result type definition
type Result<T, E = Error> = 
  | { success: true; value: T }
  | { success: false; error: E };

// Helper functions
const Ok = <T>(value: T): Result<T> => ({ 
  success: true, 
  value 
});

const Err = <E>(error: E): Result<never, E> => ({ 
  success: false, 
  error 
});

// Usage example
class UserService {
  async findUser(id: string): Promise<Result<User, NotFoundError | ValidationError>> {
    if (!isValidUUID(id)) {
      return Err(new ValidationError('Invalid user ID format', 'id', id));
    }

    const user = await this.repository.findById(id);
    
    if (!user) {
      return Err(new NotFoundError('User', id));
    }

    return Ok(user);
  }
}

// Consuming the result
const userResult = await userService.findUser(userId);

if (userResult.success) {
  console.log('User found:', userResult.value);
} else {
  console.error('Error:', userResult.error.message);
}
```

### 3. Error Boundary Pattern for React
Catch and handle errors in React component trees.

```typescript
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

interface ErrorBoundaryProps {
  fallback?: React.ComponentType<{ error: Error; reset: () => void }>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  children: React.ReactNode;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  reset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback;
      return <FallbackComponent error={this.state.error} reset={this.reset} />;
    }

    return this.props.children;
  }
}

// Default fallback component
const DefaultErrorFallback: React.FC<{ error: Error; reset: () => void }> = ({ 
  error, 
  reset 
}) => (
  <div className="error-fallback">
    <h2>Something went wrong</h2>
    <details style={{ whiteSpace: 'pre-wrap' }}>
      {error.toString()}
    </details>
    <button onClick={reset}>Try again</button>
  </div>
);
```

### 4. Async Error Handling Patterns
Proper error handling for asynchronous operations.

```typescript
// Async wrapper with error handling
async function asyncHandler<T>(
  fn: () => Promise<T>
): Promise<Result<T>> {
  try {
    const result = await fn();
    return Ok(result);
  } catch (error) {
    return Err(error as Error);
  }
}

// Express middleware error wrapper
const asyncMiddleware = (
  fn: (req: Request, res: Response, next: NextFunction) => Promise<void>
) => {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};

// Usage
app.get('/users/:id', asyncMiddleware(async (req, res) => {
  const user = await userService.findUser(req.params.id);
  res.json(user);
}));
```

### 5. Centralized Error Handling
Global error handler for applications.

```typescript
interface ErrorHandler {
  handle(error: Error, context?: ErrorContext): void;
}

interface ErrorContext {
  userId?: string;
  requestId?: string;
  action?: string;
  metadata?: Record<string, unknown>;
}

class ApplicationErrorHandler implements ErrorHandler {
  constructor(
    private readonly logger: Logger,
    private readonly monitoring: MonitoringService
  ) {}

  handle(error: Error, context?: ErrorContext): void {
    // Log the error
    this.logger.error({
      message: error.message,
      stack: error.stack,
      ...context
    });

    // Send to monitoring service
    this.monitoring.captureException(error, {
      user: context?.userId,
      tags: {
        action: context?.action || 'unknown'
      },
      extra: context?.metadata
    });

    // Handle specific error types
    if (error instanceof ValidationError) {
      this.handleValidationError(error);
    } else if (error instanceof AuthenticationError) {
      this.handleAuthError(error);
    } else {
      this.handleUnknownError(error);
    }
  }

  private handleValidationError(error: ValidationError): void {
    // Specific handling for validation errors
  }

  private handleAuthError(error: AuthenticationError): void {
    // Specific handling for auth errors
  }

  private handleUnknownError(error: Error): void {
    // Generic error handling
  }
}
```

### 6. Retry Pattern with Exponential Backoff
Automatic retry mechanism for transient failures.

```typescript
interface RetryOptions {
  maxAttempts?: number;
  initialDelay?: number;
  maxDelay?: number;
  backoffMultiplier?: number;
  shouldRetry?: (error: Error, attempt: number) => boolean;
}

async function withRetry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const {
    maxAttempts = 3,
    initialDelay = 1000,
    maxDelay = 30000,
    backoffMultiplier = 2,
    shouldRetry = () => true
  } = options;

  let lastError: Error;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      if (attempt === maxAttempts || !shouldRetry(lastError, attempt)) {
        throw lastError;
      }

      const delay = Math.min(
        initialDelay * Math.pow(backoffMultiplier, attempt - 1),
        maxDelay
      );
      
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  throw lastError!;
}

// Usage
const data = await withRetry(
  () => fetchDataFromAPI(),
  {
    maxAttempts: 5,
    shouldRetry: (error) => error.message.includes('TIMEOUT')
  }
);
```

### 7. Circuit Breaker Pattern
Prevent cascading failures in distributed systems.

```typescript
enum CircuitState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN'
}

class CircuitBreaker<T> {
  private state = CircuitState.CLOSED;
  private failureCount = 0;
  private lastFailureTime?: number;
  private successCount = 0;

  constructor(
    private readonly options: {
      failureThreshold: number;
      resetTimeout: number;
      successThreshold: number;
    }
  ) {}

  async execute(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (this.shouldAttemptReset()) {
        this.state = CircuitState.HALF_OPEN;
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private shouldAttemptReset(): boolean {
    return (
      this.lastFailureTime !== undefined &&
      Date.now() - this.lastFailureTime >= this.options.resetTimeout
    );
  }

  private onSuccess(): void {
    this.failureCount = 0;
    
    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
      
      if (this.successCount >= this.options.successThreshold) {
        this.state = CircuitState.CLOSED;
        this.successCount = 0;
      }
    }
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    
    if (this.failureCount >= this.options.failureThreshold) {
      this.state = CircuitState.OPEN;
    }
    
    if (this.state === CircuitState.HALF_OPEN) {
      this.state = CircuitState.OPEN;
      this.successCount = 0;
    }
  }
}
```

## Testing Error Scenarios

```typescript
describe('UserService Error Handling', () => {
  it('should handle validation errors', async () => {
    const service = new UserService();
    const result = await service.findUser('invalid-id');
    
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toBeInstanceOf(ValidationError);
      expect(result.error.code).toBe('VALIDATION_ERROR');
    }
  });

  it('should retry on transient failures', async () => {
    const mockFetch = jest.fn()
      .mockRejectedValueOnce(new Error('Network timeout'))
      .mockRejectedValueOnce(new Error('Network timeout'))
      .mockResolvedValueOnce({ data: 'success' });

    const result = await withRetry(mockFetch, {
      maxAttempts: 3,
      initialDelay: 0
    });

    expect(mockFetch).toHaveBeenCalledTimes(3);
    expect(result).toEqual({ data: 'success' });
  });
});
```

## Best Practices

1. **Use Specific Error Types**: Create custom error classes for different failure scenarios.
2. **Fail Fast**: Validate inputs early and throw errors immediately.
3. **Provide Context**: Include relevant information in error messages.
4. **Log Appropriately**: Log errors with sufficient detail for debugging.
5. **Handle Errors at the Right Level**: Don't catch errors too early or too late.
6. **Use Type Guards**: Create type guards for error discrimination.

```typescript
// Type guard example
function isValidationError(error: unknown): error is ValidationError {
  return error instanceof ValidationError;
}

// Usage
try {
  await someOperation();
} catch (error) {
  if (isValidationError(error)) {
    // Handle validation error specifically
  } else {
    // Handle other errors
  }
}
```

## Anti-Patterns to Avoid

```typescript
// ❌ Catching and ignoring errors
try {
  await riskyOperation();
} catch (error) {
  // Silent failure - don't do this!
}

// ❌ Throwing strings
throw 'Something went wrong'; // Always throw Error objects

// ❌ Generic catch-all error handling
catch (error) {
  console.log('An error occurred'); // Too generic, loses context
}

// ❌ Not preserving stack traces
catch (error) {
  throw new Error('Failed'); // Original stack trace lost
}
```