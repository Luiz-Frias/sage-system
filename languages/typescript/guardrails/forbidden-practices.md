# TypeScript Forbidden Practices

## Overview
This document outlines practices that should be avoided in TypeScript development. These anti-patterns can lead to bugs, maintenance issues, and poor code quality.

## Type Safety Violations

### 1. Never Use `any` Type
The `any` type defeats the purpose of using TypeScript.

```typescript
// ❌ FORBIDDEN: Using any
function processData(data: any) {
  return data.someProperty; // No type checking
}

// ✅ CORRECT: Use specific types or generics
function processData<T extends { someProperty: string }>(data: T) {
  return data.someProperty;
}

// ✅ CORRECT: Use unknown for truly unknown types
function processUnknownData(data: unknown) {
  if (typeof data === 'object' && data !== null && 'someProperty' in data) {
    return (data as { someProperty: string }).someProperty;
  }
  throw new Error('Invalid data structure');
}
```

### 2. Avoid Type Assertions Without Validation
Type assertions can hide runtime errors.

```typescript
// ❌ FORBIDDEN: Unsafe type assertion
const user = JSON.parse(userJson) as User; // Dangerous assumption

// ✅ CORRECT: Validate before asserting
import { z } from 'zod';

const UserSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string().email()
});

const userData = JSON.parse(userJson);
const user = UserSchema.parse(userData); // Throws if invalid
```

### 3. Never Suppress TypeScript Errors
Don't use `@ts-ignore` or `@ts-nocheck`.

```typescript
// ❌ FORBIDDEN: Suppressing errors
// @ts-ignore
const result = someFunction(wrongArgument);

// ✅ CORRECT: Fix the actual issue
const result = someFunction(correctArgument);

// If absolutely necessary, use @ts-expect-error with explanation
// @ts-expect-error - Third-party library has incorrect types, PR submitted
const result = thirdPartyFunction(argument);
```

## Variable and Function Practices

### 4. No `var` Declarations
Always use `const` or `let`.

```typescript
// ❌ FORBIDDEN: Using var
var count = 0;
for (var i = 0; i < 10; i++) {
  var temp = i * 2;
}

// ✅ CORRECT: Use const/let
const count = 0;
for (let i = 0; i < 10; i++) {
  const temp = i * 2;
}
```

### 5. Avoid Function Declarations in Blocks
Function declarations are hoisted, which can cause confusion.

```typescript
// ❌ FORBIDDEN: Function declaration in block
if (condition) {
  function doSomething() { // Hoisted to function scope
    return 'result';
  }
}

// ✅ CORRECT: Use function expressions
if (condition) {
  const doSomething = () => {
    return 'result';
  };
}
```

### 6. Never Modify Function Parameters
Parameters should be treated as immutable.

```typescript
// ❌ FORBIDDEN: Modifying parameters
function processArray(items: string[]) {
  items.push('new item'); // Mutates external array
  return items;
}

// ✅ CORRECT: Create new values
function processArray(items: string[]) {
  return [...items, 'new item'];
}

// ✅ CORRECT: For objects
function updateUser(user: User, name: string) {
  return { ...user, name }; // Don't mutate: user.name = name
}
```

## Async/Promise Anti-Patterns

### 7. No Async Without Await
Avoid async functions that don't use await.

```typescript
// ❌ FORBIDDEN: Async without await
async function getValue() {
  return someValue; // Unnecessarily wraps in Promise
}

// ✅ CORRECT: Remove async if not needed
function getValue() {
  return someValue;
}

// ✅ CORRECT: Or actually use await
async function getValue() {
  const result = await fetchValue();
  return result;
}
```

### 8. Never Use Promise Constructor Anti-Pattern
Don't wrap promises in new Promise unnecessarily.

```typescript
// ❌ FORBIDDEN: Promise constructor anti-pattern
function fetchData() {
  return new Promise((resolve, reject) => {
    fetch('/api/data')
      .then(response => resolve(response))
      .catch(error => reject(error));
  });
}

// ✅ CORRECT: Return the promise directly
function fetchData() {
  return fetch('/api/data');
}
```

### 9. Avoid Unhandled Promise Rejections
Always handle promise errors.

```typescript
// ❌ FORBIDDEN: Unhandled rejection
async function riskyOperation() {
  const data = await fetchData(); // Can throw
  return process(data);
}

// ✅ CORRECT: Handle errors
async function riskyOperation() {
  try {
    const data = await fetchData();
    return process(data);
  } catch (error) {
    logger.error('Operation failed:', error);
    throw new OperationError('Failed to process data', { cause: error });
  }
}
```

## Code Organization Anti-Patterns

### 10. No Circular Dependencies
Circular dependencies cause initialization issues.

```typescript
// ❌ FORBIDDEN: Circular dependency
// file: user.ts
import { Order } from './order';
export class User {
  orders: Order[];
}

// file: order.ts
import { User } from './user';
export class Order {
  user: User;
}

// ✅ CORRECT: Use interfaces or reorganize
// file: types.ts
export interface IUser {
  orders: IOrder[];
}
export interface IOrder {
  user: IUser;
}

// file: user.ts
import type { IUser, IOrder } from './types';
export class User implements IUser {
  orders: IOrder[];
}
```

### 11. Avoid Default Exports
Named exports are more explicit and refactoring-friendly.

```typescript
// ❌ FORBIDDEN: Default export
export default class UserService {
  // ...
}

// In another file - unclear what's imported
import Service from './UserService'; // Could be anything

// ✅ CORRECT: Named exports
export class UserService {
  // ...
}

// Clear imports
import { UserService } from './UserService';
```

### 12. No Mixed Module Formats
Don't mix CommonJS and ES modules.

```typescript
// ❌ FORBIDDEN: Mixed formats
export const value = 42;
module.exports.other = 'bad'; // Don't mix

// ❌ FORBIDDEN: Dynamic require in ES modules
import { readFileSync } from 'fs';
const config = require('./config'); // Use import

// ✅ CORRECT: Use consistent ES modules
export const value = 42;
export const other = 'good';

import { readFileSync } from 'fs';
import config from './config';
```

## State Management Anti-Patterns

### 13. Never Mutate State Directly
State should be immutable.

```typescript
// ❌ FORBIDDEN: Direct mutation
const state = { count: 0, items: [] };
state.count++; // Mutation
state.items.push(newItem); // Mutation

// ✅ CORRECT: Create new state
const newState = {
  count: state.count + 1,
  items: [...state.items, newItem]
};
```

### 14. Avoid Storing Derived State
Don't store values that can be computed.

```typescript
// ❌ FORBIDDEN: Storing derived values
interface BadState {
  items: Item[];
  totalPrice: number; // Can be calculated
  itemCount: number; // Can be calculated
}

// ✅ CORRECT: Compute when needed
interface GoodState {
  items: Item[];
}

const totalPrice = state.items.reduce((sum, item) => sum + item.price, 0);
const itemCount = state.items.length;
```

## Performance Anti-Patterns

### 15. No Synchronous Operations in Async Contexts
Don't block the event loop.

```typescript
// ❌ FORBIDDEN: Sync operations in async function
async function processLargeData(data: any[]) {
  const results = [];
  for (const item of data) {
    const processed = expensiveSyncOperation(item); // Blocks
    results.push(processed);
  }
  return results;
}

// ✅ CORRECT: Use async operations or workers
async function processLargeData(data: any[]) {
  const results = await Promise.all(
    data.map(item => processAsync(item))
  );
  return results;
}
```

### 16. Avoid Memory Leaks
Clean up resources and references.

```typescript
// ❌ FORBIDDEN: Not cleaning up
class Component {
  private interval: number;
  
  start() {
    this.interval = setInterval(() => {
      this.update();
    }, 1000);
  }
  // Missing cleanup!
}

// ✅ CORRECT: Proper cleanup
class Component {
  private interval?: number;
  
  start() {
    this.interval = setInterval(() => {
      this.update();
    }, 1000);
  }
  
  stop() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = undefined;
    }
  }
}
```

## Security Anti-Patterns

### 17. Never Use `eval` or `Function` Constructor
These can execute arbitrary code.

```typescript
// ❌ FORBIDDEN: Using eval
const result = eval(userInput); // Security risk!

// ❌ FORBIDDEN: Function constructor
const fn = new Function('x', userCode);

// ✅ CORRECT: Use safe alternatives
// Parse JSON instead of eval
const data = JSON.parse(jsonString);

// Use predefined functions
const operations = {
  add: (a: number, b: number) => a + b,
  multiply: (a: number, b: number) => a * b
};
const result = operations[operation]?.(x, y);
```

### 18. No Direct DOM Manipulation with User Input
Prevent XSS attacks.

```typescript
// ❌ FORBIDDEN: Direct HTML injection
element.innerHTML = userContent; // XSS vulnerability

// ❌ FORBIDDEN: Using dangerouslySetInnerHTML without sanitization
<div dangerouslySetInnerHTML={{ __html: userContent }} />

// ✅ CORRECT: Use text content or sanitize
element.textContent = userContent;

// ✅ CORRECT: Sanitize HTML if needed
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userContent);
```

## Testing Anti-Patterns

### 19. No Test Implementation in Production Code
Keep test logic separate.

```typescript
// ❌ FORBIDDEN: Test code in production
class UserService {
  async getUser(id: string) {
    if (process.env.NODE_ENV === 'test') {
      return mockUser; // Test logic in production code
    }
    return this.database.findUser(id);
  }
}

// ✅ CORRECT: Use dependency injection
class UserService {
  constructor(private database: Database) {}
  
  async getUser(id: string) {
    return this.database.findUser(id);
  }
}

// In tests, inject mock
const service = new UserService(mockDatabase);
```

### 20. Avoid Hard-Coded Values
Use configuration and constants.

```typescript
// ❌ FORBIDDEN: Hard-coded values
async function fetchData() {
  return fetch('http://localhost:3000/api/data'); // Hard-coded URL
}

if (retries > 3) { // Magic number
  throw new Error('Max retries exceeded');
}

// ✅ CORRECT: Use configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:3000';
const MAX_RETRIES = 3;

async function fetchData() {
  return fetch(`${API_BASE_URL}/api/data`);
}

if (retries > MAX_RETRIES) {
  throw new Error('Max retries exceeded');
}
```

## Enforcement

These forbidden practices should be enforced through:

1. **ESLint Rules**: Configure rules to catch these patterns
2. **TypeScript Config**: Use strict compiler options
3. **Code Reviews**: Reviewers should check for these patterns
4. **Pre-commit Hooks**: Automated checks before commits
5. **CI/CD Pipeline**: Fail builds that contain forbidden practices

Example ESLint configuration:
```json
{
  "rules": {
    "no-any": "error",
    "no-var": "error",
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-non-null-assertion": "error",
    "no-eval": "error",
    "no-implied-eval": "error",
    "@typescript-eslint/require-await": "error",
    "@typescript-eslint/no-misused-promises": "error"
  }
}
```