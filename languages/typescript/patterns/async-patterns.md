---
name: Async Patterns
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# TypeScript Async Patterns

## Overview
Asynchronous programming is fundamental to modern TypeScript applications. This document outlines patterns for handling promises, async/await, concurrent operations, and managing complex async workflows.

## Core Async Patterns

### 1. Promise Composition Patterns
Combining multiple promises effectively.

```typescript
// Sequential execution
async function sequentialOperations<T>(
  operations: Array<() => Promise<T>>
): Promise<T[]> {
  const results: T[] = [];
  
  for (const operation of operations) {
    results.push(await operation());
  }
  
  return results;
}

// Parallel execution with error handling
async function parallelOperations<T>(
  operations: Array<() => Promise<T>>
): Promise<Array<{ status: 'fulfilled' | 'rejected'; value?: T; reason?: any }>> {
  const promises = operations.map(op => op());
  const results = await Promise.allSettled(promises);
  
  return results.map(result => ({
    status: result.status,
    value: result.status === 'fulfilled' ? result.value : undefined,
    reason: result.status === 'rejected' ? result.reason : undefined
  }));
}

// Batch processing with concurrency limit
async function batchProcess<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>,
  concurrencyLimit: number = 5
): Promise<R[]> {
  const results: R[] = [];
  
  for (let i = 0; i < items.length; i += concurrencyLimit) {
    const batch = items.slice(i, i + concurrencyLimit);
    const batchResults = await Promise.all(
      batch.map(item => processor(item))
    );
    results.push(...batchResults);
  }
  
  return results;
}
```

### 2. Async Queue Pattern
Managing async operations with a queue.

```typescript
interface QueueOptions {
  concurrency?: number;
  timeout?: number;
}

class AsyncQueue<T> {
  private queue: Array<() => Promise<T>> = [];
  private running = 0;
  private results: T[] = [];
  
  constructor(private options: QueueOptions = {}) {
    this.options.concurrency = options.concurrency || 1;
  }

  add(task: () => Promise<T>): this {
    this.queue.push(task);
    this.process();
    return this;
  }

  private async process(): Promise<void> {
    if (this.running >= this.options.concurrency! || this.queue.length === 0) {
      return;
    }

    this.running++;
    const task = this.queue.shift()!;

    try {
      const result = await this.executeWithTimeout(task);
      this.results.push(result);
    } catch (error) {
      // Handle error appropriately
      console.error('Task failed:', error);
    } finally {
      this.running--;
      this.process();
    }
  }

  private async executeWithTimeout(task: () => Promise<T>): Promise<T> {
    if (!this.options.timeout) {
      return await task();
    }

    return Promise.race([
      task(),
      new Promise<T>((_, reject) => 
        setTimeout(() => reject(new Error('Task timeout')), this.options.timeout)
      )
    ]);
  }

  async waitForAll(): Promise<T[]> {
    while (this.queue.length > 0 || this.running > 0) {
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    return this.results;
  }
}

// Usage
const queue = new AsyncQueue<string>({ concurrency: 3, timeout: 5000 });

['url1', 'url2', 'url3', 'url4', 'url5'].forEach(url => {
  queue.add(async () => {
    const response = await fetch(url);
    return response.text();
  });
});

const results = await queue.waitForAll();
```

### 3. Async Iterator Pattern
Working with async iterables and generators.

```typescript
// Async generator for paginated data
async function* paginatedFetch<T>(
  baseUrl: string,
  pageSize: number = 50
): AsyncGenerator<T[], void, unknown> {
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const response = await fetch(
      `${baseUrl}?page=${page}&size=${pageSize}`
    );
    const data = await response.json();
    
    yield data.items as T[];
    
    hasMore = data.hasNextPage;
    page++;
  }
}

// Consuming async iterator
async function processAllItems<T>(
  generator: AsyncGenerator<T[], void, unknown>,
  processor: (item: T) => Promise<void>
): Promise<void> {
  for await (const batch of generator) {
    await Promise.all(batch.map(item => processor(item)));
  }
}

// Transform async iterator
async function* mapAsyncIterator<T, R>(
  source: AsyncIterable<T>,
  mapper: (item: T) => Promise<R>
): AsyncGenerator<R, void, unknown> {
  for await (const item of source) {
    yield await mapper(item);
  }
}
```

### 4. Debounce and Throttle Patterns
Controlling async function execution frequency.

```typescript
// Debounce for async functions
function debounceAsync<T extends (...args: any[]) => Promise<any>>(
  func: T,
  delay: number
): (...args: Parameters<T>) => Promise<ReturnType<T>> {
  let timeoutId: NodeJS.Timeout | null = null;
  let activePromise: Promise<ReturnType<T>> | null = null;

  return async (...args: Parameters<T>): Promise<ReturnType<T>> => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    if (!activePromise) {
      activePromise = new Promise<ReturnType<T>>((resolve, reject) => {
        timeoutId = setTimeout(async () => {
          try {
            const result = await func(...args);
            resolve(result);
          } catch (error) {
            reject(error);
          } finally {
            activePromise = null;
            timeoutId = null;
          }
        }, delay);
      });
    }

    return activePromise;
  };
}

// Throttle for async functions
function throttleAsync<T extends (...args: any[]) => Promise<any>>(
  func: T,
  limit: number
): (...args: Parameters<T>) => Promise<ReturnType<T> | void> {
  let inThrottle = false;
  let lastResult: ReturnType<T>;

  return async (...args: Parameters<T>): Promise<ReturnType<T> | void> => {
    if (!inThrottle) {
      inThrottle = true;
      
      try {
        lastResult = await func(...args);
        return lastResult;
      } finally {
        setTimeout(() => {
          inThrottle = false;
        }, limit);
      }
    }
    
    return lastResult;
  };
}
```

### 5. Async Cache Pattern
Caching async operation results.

```typescript
interface CacheOptions {
  ttl?: number; // Time to live in milliseconds
  maxSize?: number;
}

class AsyncCache<K, V> {
  private cache = new Map<K, { value: V; timestamp: number }>();
  private pendingPromises = new Map<K, Promise<V>>();

  constructor(private options: CacheOptions = {}) {}

  async get(
    key: K,
    fetcher: () => Promise<V>
  ): Promise<V> {
    // Check if we have a valid cached value
    const cached = this.cache.get(key);
    if (cached && this.isValid(cached.timestamp)) {
      return cached.value;
    }

    // Check if there's already a pending promise for this key
    const pending = this.pendingPromises.get(key);
    if (pending) {
      return pending;
    }

    // Create new promise and cache it
    const promise = fetcher().then(value => {
      this.set(key, value);
      this.pendingPromises.delete(key);
      return value;
    }).catch(error => {
      this.pendingPromises.delete(key);
      throw error;
    });

    this.pendingPromises.set(key, promise);
    return promise;
  }

  private set(key: K, value: V): void {
    // Implement LRU eviction if needed
    if (this.options.maxSize && this.cache.size >= this.options.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }

    this.cache.set(key, {
      value,
      timestamp: Date.now()
    });
  }

  private isValid(timestamp: number): boolean {
    if (!this.options.ttl) return true;
    return Date.now() - timestamp < this.options.ttl;
  }

  clear(): void {
    this.cache.clear();
    this.pendingPromises.clear();
  }
}

// Usage
const userCache = new AsyncCache<string, User>({ 
  ttl: 5 * 60 * 1000, // 5 minutes
  maxSize: 100 
});

const user = await userCache.get(userId, async () => {
  const response = await fetch(`/api/users/${userId}`);
  return response.json();
});
```

### 6. Async Event Emitter Pattern
Event-driven async programming.

```typescript
type AsyncEventHandler<T> = (data: T) => Promise<void> | void;

class AsyncEventEmitter<Events extends Record<string, any>> {
  private handlers = new Map<keyof Events, Set<AsyncEventHandler<any>>>();

  on<K extends keyof Events>(
    event: K,
    handler: AsyncEventHandler<Events[K]>
  ): void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);
  }

  off<K extends keyof Events>(
    event: K,
    handler: AsyncEventHandler<Events[K]>
  ): void {
    this.handlers.get(event)?.delete(handler);
  }

  async emit<K extends keyof Events>(
    event: K,
    data: Events[K]
  ): Promise<void> {
    const handlers = this.handlers.get(event);
    if (!handlers) return;

    const promises = Array.from(handlers).map(handler =>
      Promise.resolve(handler(data)).catch(error => {
        console.error(`Error in event handler for ${String(event)}:`, error);
      })
    );

    await Promise.all(promises);
  }

  // Emit events in sequence rather than parallel
  async emitSerial<K extends keyof Events>(
    event: K,
    data: Events[K]
  ): Promise<void> {
    const handlers = this.handlers.get(event);
    if (!handlers) return;

    for (const handler of handlers) {
      try {
        await handler(data);
      } catch (error) {
        console.error(`Error in event handler for ${String(event)}:`, error);
      }
    }
  }
}

// Usage
interface AppEvents {
  userLogin: { userId: string; timestamp: Date };
  dataUpdate: { entityId: string; changes: any };
}

const emitter = new AsyncEventEmitter<AppEvents>();

emitter.on('userLogin', async ({ userId, timestamp }) => {
  await logUserActivity(userId, timestamp);
});

await emitter.emit('userLogin', { 
  userId: '123', 
  timestamp: new Date() 
});
```

### 7. Async State Machine Pattern
Managing complex async workflows.

```typescript
interface StateTransition<S, E> {
  from: S;
  event: E;
  to: S;
  guard?: () => boolean | Promise<boolean>;
  action?: () => void | Promise<void>;
}

class AsyncStateMachine<S extends string, E extends string> {
  private transitions: StateTransition<S, E>[] = [];
  
  constructor(
    private currentState: S,
    private onStateChange?: (from: S, to: S, event: E) => void | Promise<void>
  ) {}

  addTransition(transition: StateTransition<S, E>): void {
    this.transitions.push(transition);
  }

  async send(event: E): Promise<boolean> {
    const transition = this.transitions.find(
      t => t.from === this.currentState && t.event === event
    );

    if (!transition) {
      return false;
    }

    if (transition.guard) {
      const canTransition = await transition.guard();
      if (!canTransition) {
        return false;
      }
    }

    const previousState = this.currentState;
    this.currentState = transition.to;

    if (transition.action) {
      await transition.action();
    }

    if (this.onStateChange) {
      await this.onStateChange(previousState, this.currentState, event);
    }

    return true;
  }

  getState(): S {
    return this.currentState;
  }
}

// Usage example
enum OrderState {
  PENDING = 'PENDING',
  PROCESSING = 'PROCESSING',
  SHIPPED = 'SHIPPED',
  DELIVERED = 'DELIVERED',
  CANCELLED = 'CANCELLED'
}

enum OrderEvent {
  PROCESS = 'PROCESS',
  SHIP = 'SHIP',
  DELIVER = 'DELIVER',
  CANCEL = 'CANCEL'
}

const orderStateMachine = new AsyncStateMachine<OrderState, OrderEvent>(
  OrderState.PENDING,
  async (from, to, event) => {
    await saveOrderStateChange(from, to, event);
  }
);

orderStateMachine.addTransition({
  from: OrderState.PENDING,
  event: OrderEvent.PROCESS,
  to: OrderState.PROCESSING,
  action: async () => {
    await chargeCustomer();
    await notifyWarehouse();
  }
});
```

## Best Practices

1. **Always Handle Errors**: Never let promises fail silently.
2. **Avoid Promise Constructor Anti-Pattern**: Don't wrap promises unnecessarily.
3. **Use Promise.allSettled for Resilience**: When you need all results regardless of failures.
4. **Implement Timeouts**: Always set reasonable timeouts for async operations.
5. **Clean Up Resources**: Use finally blocks or cleanup functions.
6. **Avoid Blocking the Event Loop**: Break up CPU-intensive tasks.

## Common Anti-Patterns

```typescript
// ❌ Promise constructor anti-pattern
const bad = new Promise(async (resolve, reject) => {
  const data = await fetchData(); // Don't use async in Promise constructor
  resolve(data);
});

// ✅ Correct approach
const good = fetchData();

// ❌ Forgetting to handle errors
async function badErrorHandling() {
  const data = await fetchData(); // Unhandled rejection if this fails
}

// ✅ Proper error handling
async function goodErrorHandling() {
  try {
    const data = await fetchData();
  } catch (error) {
    // Handle error appropriately
  }
}

// ❌ Sequential when parallel would work
async function inefficient(ids: string[]) {
  const results = [];
  for (const id of ids) {
    results.push(await fetchById(id)); // Unnecessarily sequential
  }
  return results;
}

// ✅ Parallel execution
async function efficient(ids: string[]) {
  return Promise.all(ids.map(id => fetchById(id)));
}
```