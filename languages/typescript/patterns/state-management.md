---
name: State Management
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# TypeScript State Management Patterns

## Overview
State management is crucial for building scalable TypeScript applications. This document covers patterns for managing application state, from simple component state to complex global state management solutions.

## Core State Management Principles

### 1. Immutable State Pattern
Ensuring state predictability through immutability.

```typescript
// State type definition
interface AppState {
  user: {
    id: string;
    name: string;
    preferences: {
      theme: 'light' | 'dark';
      language: string;
    };
  };
  products: Product[];
  cart: CartItem[];
  isLoading: boolean;
}

// Immutable update utilities
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

function updateState<T>(
  current: T,
  updates: DeepPartial<T>
): T {
  return Object.entries(updates).reduce((acc, [key, value]) => {
    if (value === undefined) return acc;
    
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      return {
        ...acc,
        [key]: updateState(acc[key as keyof T], value)
      };
    }
    
    return { ...acc, [key]: value };
  }, { ...current });
}

// Usage
const newState = updateState(currentState, {
  user: {
    preferences: {
      theme: 'dark'
    }
  },
  isLoading: false
});
```

### 2. Redux-Style State Management
Predictable state container with actions and reducers.

```typescript
// Action types
interface Action<T = any> {
  type: string;
  payload?: T;
}

// Action creators with type inference
function createAction<T extends string>(type: T): () => Action<void>;
function createAction<T extends string, P>(type: T): (payload: P) => Action<P>;
function createAction<T extends string, P>(type: T) {
  return (payload?: P) => ({ type, payload });
}

// Type-safe reducer
type Reducer<S, A extends Action> = (state: S, action: A) => S;

// Example implementation
namespace UserActions {
  export const login = createAction<'USER_LOGIN', { id: string; name: string }>('USER_LOGIN');
  export const logout = createAction<'USER_LOGOUT'>('USER_LOGOUT');
  export const updatePreferences = createAction<'UPDATE_PREFERENCES', Partial<UserPreferences>>('UPDATE_PREFERENCES');
}

type UserAction = ReturnType<typeof UserActions[keyof typeof UserActions]>;

const userReducer: Reducer<UserState, UserAction> = (state, action) => {
  switch (action.type) {
    case 'USER_LOGIN':
      return {
        ...state,
        isAuthenticated: true,
        id: action.payload.id,
        name: action.payload.name
      };
    
    case 'USER_LOGOUT':
      return {
        ...state,
        isAuthenticated: false,
        id: null,
        name: null
      };
    
    case 'UPDATE_PREFERENCES':
      return {
        ...state,
        preferences: {
          ...state.preferences,
          ...action.payload
        }
      };
    
    default:
      return state;
  }
};
```

### 3. Observable State Pattern
Reactive state management with observables.

```typescript
type Listener<T> = (state: T) => void;
type Unsubscribe = () => void;

class Observable<T> {
  private listeners = new Set<Listener<T>>();
  
  constructor(private state: T) {}

  getState(): T {
    return this.state;
  }

  setState(updater: T | ((prev: T) => T)): void {
    const newState = typeof updater === 'function' 
      ? (updater as (prev: T) => T)(this.state)
      : updater;
    
    if (newState !== this.state) {
      this.state = newState;
      this.notify();
    }
  }

  subscribe(listener: Listener<T>): Unsubscribe {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify(): void {
    this.listeners.forEach(listener => listener(this.state));
  }
}

// Derived state with computed values
class ComputedState<T, D> extends Observable<D> {
  private unsubscribe?: Unsubscribe;

  constructor(
    source: Observable<T>,
    compute: (state: T) => D
  ) {
    super(compute(source.getState()));
    
    this.unsubscribe = source.subscribe(state => {
      this.setState(compute(state));
    });
  }

  dispose(): void {
    this.unsubscribe?.();
  }
}

// Usage
const appState = new Observable<AppState>(initialState);
const cartTotal = new ComputedState(
  appState,
  state => state.cart.reduce((sum, item) => sum + item.price * item.quantity, 0)
);
```

### 4. Context-Based State Management (React)
Managing state with React Context and hooks.

```typescript
// State context with TypeScript
interface StateContextValue<T> {
  state: T;
  dispatch: React.Dispatch<Action<any>>;
}

function createStateContext<T>() {
  const StateContext = React.createContext<StateContextValue<T> | undefined>(undefined);

  function useStateContext() {
    const context = React.useContext(StateContext);
    if (!context) {
      throw new Error('useStateContext must be used within a StateProvider');
    }
    return context;
  }

  return { StateContext, useStateContext };
}

// Provider with reducer
interface StateProviderProps<T> {
  initialState: T;
  reducer: Reducer<T, Action>;
  children: React.ReactNode;
}

function StateProvider<T>({ 
  initialState, 
  reducer, 
  children 
}: StateProviderProps<T>) {
  const [state, dispatch] = React.useReducer(reducer, initialState);
  
  const value = React.useMemo(
    () => ({ state, dispatch }),
    [state]
  );

  return (
    <StateContext.Provider value={value}>
      {children}
    </StateContext.Provider>
  );
}

// Custom hooks for state slices
function useSelector<T, R>(
  selector: (state: T) => R,
  equalityFn?: (a: R, b: R) => boolean
): R {
  const { state } = useStateContext<T>();
  const selectedState = selector(state);
  
  const prevSelectedRef = React.useRef(selectedState);
  
  if (equalityFn ? !equalityFn(prevSelectedRef.current, selectedState) : prevSelectedRef.current !== selectedState) {
    prevSelectedRef.current = selectedState;
  }
  
  return prevSelectedRef.current;
}
```

### 5. State Machine Pattern for UI State
Managing complex UI states with state machines.

```typescript
interface StateNode<C, E> {
  on?: Partial<Record<E, keyof StateNode<C, E>>>;
  entry?: (context: C) => void;
  exit?: (context: C) => void;
}

type StateConfig<S extends string, C, E extends string> = Record<S, StateNode<C, E>>;

class StateMachine<S extends string, C, E extends string> {
  private currentState: S;
  
  constructor(
    private config: StateConfig<S, C, E>,
    initialState: S,
    private context: C
  ) {
    this.currentState = initialState;
    this.config[initialState].entry?.(context);
  }

  send(event: E): void {
    const currentConfig = this.config[this.currentState];
    const nextState = currentConfig.on?.[event];
    
    if (nextState && nextState !== this.currentState) {
      currentConfig.exit?.(this.context);
      this.currentState = nextState as S;
      this.config[this.currentState].entry?.(this.context);
    }
  }

  getState(): S {
    return this.currentState;
  }
}

// Form state machine example
enum FormState {
  IDLE = 'IDLE',
  VALIDATING = 'VALIDATING',
  SUBMITTING = 'SUBMITTING',
  SUCCESS = 'SUCCESS',
  ERROR = 'ERROR'
}

enum FormEvent {
  SUBMIT = 'SUBMIT',
  VALIDATE_SUCCESS = 'VALIDATE_SUCCESS',
  VALIDATE_ERROR = 'VALIDATE_ERROR',
  SUBMIT_SUCCESS = 'SUBMIT_SUCCESS',
  SUBMIT_ERROR = 'SUBMIT_ERROR',
  RESET = 'RESET'
}

interface FormContext {
  errors: string[];
  data: any;
}

const formMachine = new StateMachine<FormState, FormContext, FormEvent>(
  {
    [FormState.IDLE]: {
      on: { [FormEvent.SUBMIT]: FormState.VALIDATING }
    },
    [FormState.VALIDATING]: {
      entry: (ctx) => ctx.errors = [],
      on: {
        [FormEvent.VALIDATE_SUCCESS]: FormState.SUBMITTING,
        [FormEvent.VALIDATE_ERROR]: FormState.ERROR
      }
    },
    [FormState.SUBMITTING]: {
      on: {
        [FormEvent.SUBMIT_SUCCESS]: FormState.SUCCESS,
        [FormEvent.SUBMIT_ERROR]: FormState.ERROR
      }
    },
    [FormState.SUCCESS]: {
      on: { [FormEvent.RESET]: FormState.IDLE }
    },
    [FormState.ERROR]: {
      on: { [FormEvent.RESET]: FormState.IDLE }
    }
  },
  FormState.IDLE,
  { errors: [], data: {} }
);
```

### 6. Atomic State Management (Jotai/Recoil Style)
Fine-grained reactive state management.

```typescript
type AtomGetter = <T>(atom: Atom<T>) => T;
type AtomSetter = <T>(atom: Atom<T>, value: T | ((prev: T) => T)) => void;

interface Atom<T> {
  id: symbol;
  init: T | ((get: AtomGetter) => T);
  subscribers: Set<() => void>;
}

function atom<T>(initialValue: T | ((get: AtomGetter) => T)): Atom<T> {
  return {
    id: Symbol('atom'),
    init: initialValue,
    subscribers: new Set()
  };
}

class AtomStore {
  private values = new Map<symbol, any>();
  private dependencies = new Map<symbol, Set<symbol>>();

  get<T>(atom: Atom<T>): T {
    if (!this.values.has(atom.id)) {
      const value = typeof atom.init === 'function'
        ? (atom.init as (get: AtomGetter) => T)(this.get.bind(this))
        : atom.init;
      this.values.set(atom.id, value);
    }
    return this.values.get(atom.id);
  }

  set<T>(atom: Atom<T>, value: T | ((prev: T) => T)): void {
    const prevValue = this.get(atom);
    const nextValue = typeof value === 'function'
      ? (value as (prev: T) => T)(prevValue)
      : value;
    
    if (nextValue !== prevValue) {
      this.values.set(atom.id, nextValue);
      atom.subscribers.forEach(subscriber => subscriber());
      this.notifyDependents(atom.id);
    }
  }

  private notifyDependents(atomId: symbol): void {
    const dependents = this.dependencies.get(atomId);
    if (dependents) {
      dependents.forEach(dependentId => {
        // Re-compute derived atoms
      });
    }
  }

  subscribe<T>(atom: Atom<T>, callback: () => void): () => void {
    atom.subscribers.add(callback);
    return () => atom.subscribers.delete(callback);
  }
}

// Usage
const countAtom = atom(0);
const doubleCountAtom = atom((get) => get(countAtom) * 2);
const store = new AtomStore();

store.set(countAtom, (prev) => prev + 1);
console.log(store.get(doubleCountAtom)); // 2
```

### 7. Event Sourcing Pattern
State as a sequence of events.

```typescript
interface Event<T = any> {
  id: string;
  type: string;
  timestamp: Date;
  payload: T;
  metadata?: Record<string, any>;
}

class EventStore<S> {
  private events: Event[] = [];
  private snapshots: Array<{ state: S; eventIndex: number }> = [];
  
  constructor(
    private reducer: (state: S, event: Event) => S,
    private initialState: S
  ) {}

  append(event: Event): void {
    this.events.push(event);
  }

  getCurrentState(): S {
    const lastSnapshot = this.snapshots[this.snapshots.length - 1];
    const startIndex = lastSnapshot?.eventIndex ?? 0;
    const startState = lastSnapshot?.state ?? this.initialState;
    
    return this.events
      .slice(startIndex)
      .reduce((state, event) => this.reducer(state, event), startState);
  }

  createSnapshot(): void {
    this.snapshots.push({
      state: this.getCurrentState(),
      eventIndex: this.events.length
    });
  }

  getEvents(from?: Date, to?: Date): Event[] {
    return this.events.filter(event => {
      if (from && event.timestamp < from) return false;
      if (to && event.timestamp > to) return false;
      return true;
    });
  }

  replay(until?: Date): S {
    const events = until 
      ? this.events.filter(e => e.timestamp <= until)
      : this.events;
    
    return events.reduce(
      (state, event) => this.reducer(state, event),
      this.initialState
    );
  }
}
```

## Performance Optimization

### Memoization and Selective Updates
```typescript
// Memoized selectors
function createSelector<S, R, Args extends any[]>(
  selector: (state: S, ...args: Args) => R,
  equalityFn: (a: R, b: R) => boolean = Object.is
): (state: S, ...args: Args) => R {
  let lastState: S;
  let lastArgs: Args;
  let lastResult: R;
  let initialized = false;

  return (state: S, ...args: Args) => {
    if (!initialized || state !== lastState || !argsEqual(args, lastArgs)) {
      const newResult = selector(state, ...args);
      
      if (!initialized || !equalityFn(newResult, lastResult)) {
        lastResult = newResult;
      }
      
      lastState = state;
      lastArgs = args;
      initialized = true;
    }
    
    return lastResult;
  };
}

function argsEqual<T extends any[]>(a: T, b: T): boolean {
  return a.length === b.length && a.every((arg, i) => arg === b[i]);
}
```

## Best Practices

1. **Keep State Minimal**: Store only what you can't derive.
2. **Normalize Complex State**: Use normalized data structures for relationships.
3. **Isolate Side Effects**: Keep state updates pure and predictable.
4. **Use TypeScript Strictly**: Leverage TypeScript for state type safety.
5. **Implement Time-Travel Debugging**: Make state changes traceable.
6. **Consider Performance Early**: Plan for memoization and selective updates.

## Anti-Patterns to Avoid

```typescript
// ❌ Mutating state directly
state.user.name = 'New Name'; // Never mutate

// ✅ Create new state
state = { ...state, user: { ...state.user, name: 'New Name' } };

// ❌ Storing derived state
interface BadState {
  items: Item[];
  itemCount: number; // Can be derived from items.length
}

// ✅ Compute derived values
const itemCount = state.items.length;

// ❌ Deeply nested state
interface BadState {
  ui: {
    modals: {
      userProfile: {
        form: {
          fields: {
            name: { value: string; error?: string };
          };
        };
      };
    };
  };
}

// ✅ Flatten state structure
interface GoodState {
  modals: Record<string, boolean>;
  forms: Record<string, FormState>;
  fields: Record<string, FieldState>;
}
```