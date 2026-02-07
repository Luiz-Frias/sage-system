---
name: Interior Mutability
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use interior mutability only when shared ownership and controlled mutation are both required.

## Core Rules
1. Prefer `RefCell<T>` for single-threaded runtime-checked borrowing.
2. Prefer `Mutex<T>` or `RwLock<T>` for multi-threaded mutation.
3. Prefer `Cell<T>` for `Copy` types with lightweight updates.
4. Keep mutation scope minimal and explicit.
5. Never hold locks across blocking calls.

## Pattern Selection
- `Cell<T>`: copy-value updates without borrow references.
- `RefCell<T>`: runtime borrow checking in single-threaded contexts.
- `Mutex<T>`: mutual exclusion across threads.
- `RwLock<T>`: many readers, few writers.
- `Atomic*`: lock-free primitive numeric/boolean state.

## Safety Constraints
1. Avoid nested lock acquisition without lock ordering policy.
2. Avoid long-lived mutable borrows from `RefCell<T>`.
3. Convert lock poisoning into typed errors when required by interface contract.
4. Keep API boundaries ownership-safe and panic-free.

## Example
```rust
use std::cell::RefCell;

struct Counter {
    value: RefCell<u64>,
}

impl Counter {
    fn increment(&self) {
        *self.value.borrow_mut() += 1;
    }

    fn get(&self) -> u64 {
        *self.value.borrow()
    }
}
```
