---
name: Memory Safety
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# Rust Memory Safety and Ownership Rules

## Overview
Rust's ownership system is the foundation of its memory safety guarantees, preventing data races, null pointer dereferences, and use-after-free errors at compile time without garbage collection.

## Core Ownership Rules

### 1. The Three Rules of Ownership
```rust
// Rule 1: Each value has a single owner
let s1 = String::from("hello");
let s2 = s1; // s1 is moved to s2
// println!("{}", s1); // Error: s1 no longer valid

// Rule 2: There can only be one owner at a time
fn take_ownership(s: String) {
    println!("{}", s);
} // s goes out of scope and is dropped

let s = String::from("hello");
take_ownership(s);
// println!("{}", s); // Error: s has been moved

// Rule 3: When the owner goes out of scope, the value is dropped
{
    let s = String::from("hello");
    // s is valid here
} // s goes out of scope and is dropped
```

### 2. Move Semantics
```rust
// Types that implement Copy
let x = 5;
let y = x; // Copy, not move
println!("x = {}, y = {}", x, y); // Both valid

// Types that don't implement Copy
let s1 = String::from("hello");
let s2 = s1; // Move
// println!("{}", s1); // Error: value moved

// Explicit clone
let s1 = String::from("hello");
let s2 = s1.clone();
println!("s1 = {}, s2 = {}", s1, s2); // Both valid

// Move in function calls
fn consume(s: String) {
    println!("{}", s);
}

let s = String::from("hello");
consume(s);
// s is no longer valid here

// Return ownership
fn give_ownership() -> String {
    String::from("hello")
}

fn take_and_give_back(s: String) -> String {
    s // Ownership transferred back
}
```

## Borrowing Rules

### 1. Immutable References
```rust
// Multiple immutable references allowed
let s = String::from("hello");
let r1 = &s;
let r2 = &s;
println!("{}, {}", r1, r2); // OK

// References must be valid
fn calculate_length(s: &String) -> usize {
    s.len()
} // s goes out of scope but doesn't drop the value

let s1 = String::from("hello");
let len = calculate_length(&s1);
println!("Length of '{}' is {}", s1, len); // s1 still valid
```

### 2. Mutable References
```rust
// Only one mutable reference at a time
let mut s = String::from("hello");
let r1 = &mut s;
// let r2 = &mut s; // Error: cannot borrow as mutable more than once

// Mutable reference scope
let mut s = String::from("hello");
{
    let r1 = &mut s;
    r1.push_str(", world");
} // r1 goes out of scope
let r2 = &mut s; // OK, r1 is no longer in scope

// Cannot mix mutable and immutable references
let mut s = String::from("hello");
let r1 = &s; // Immutable borrow
let r2 = &s; // OK
// let r3 = &mut s; // Error: cannot borrow as mutable
println!("{}, {}", r1, r2);
// r1 and r2 are no longer used after this point
let r3 = &mut s; // OK now
```

### 3. Reference Rules Summary
```rust
// Valid patterns
fn valid_borrows() {
    let mut s = String::from("hello");
    
    // Pattern 1: Multiple immutable borrows
    let r1 = &s;
    let r2 = &s;
    println!("{} {}", r1, r2);
    
    // Pattern 2: Single mutable borrow
    let r3 = &mut s;
    r3.push_str(", world");
    
    // Pattern 3: Non-overlapping scopes
    {
        let r4 = &s;
        println!("{}", r4);
    } // r4 scope ends
    let r5 = &mut s; // OK
}

// Invalid patterns (won't compile)
fn invalid_borrows() {
    let mut s = String::from("hello");
    
    // Cannot have mutable and immutable references simultaneously
    // let r1 = &s;
    // let r2 = &mut s; // Error
    
    // Cannot have multiple mutable references
    // let r1 = &mut s;
    // let r2 = &mut s; // Error
}
```

## Lifetime Rules

### 1. Basic Lifetime Annotations
```rust
// Explicit lifetime annotations
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() {
        x
    } else {
        y
    }
}

// Lifetime elision rules
fn first_word(s: &str) -> &str {
    // Compiler infers: fn first_word<'a>(s: &'a str) -> &'a str
    let bytes = s.as_bytes();
    for (i, &item) in bytes.iter().enumerate() {
        if item == b' ' {
            return &s[0..i];
        }
    }
    &s[..]
}
```

### 2. Struct Lifetimes
```rust
// Structs with references need lifetime annotations
struct ImportantExcerpt<'a> {
    part: &'a str,
}

impl<'a> ImportantExcerpt<'a> {
    fn level(&self) -> i32 {
        3
    }
    
    fn announce_and_return_part(&self, announcement: &str) -> &str {
        println!("Attention please: {}", announcement);
        self.part
    }
}

// Usage
let novel = String::from("Call me Ishmael. Some years ago...");
let first_sentence = novel.split('.').next().expect("Could not find a '.'");
let i = ImportantExcerpt {
    part: first_sentence,
};
```

### 3. Lifetime Bounds
```rust
// Generic type parameters with lifetime bounds
use std::fmt::Display;

fn longest_with_announcement<'a, T>(
    x: &'a str,
    y: &'a str,
    ann: T,
) -> &'a str
where
    T: Display,
{
    println!("Announcement: {}", ann);
    if x.len() > y.len() {
        x
    } else {
        y
    }
}

// Static lifetime
let s: &'static str = "I have a static lifetime.";
```

## Common Memory Safety Patterns

### 1. Interior Mutability
```rust
use std::cell::{Cell, RefCell};
use std::rc::Rc;

// Cell for Copy types
struct Counter {
    value: Cell<i32>,
}

impl Counter {
    fn new() -> Self {
        Counter { value: Cell::new(0) }
    }
    
    fn increment(&self) {
        self.value.set(self.value.get() + 1);
    }
}

// RefCell for runtime borrowing
struct Node {
    value: i32,
    children: RefCell<Vec<Rc<Node>>>,
}

impl Node {
    fn add_child(&self, child: Rc<Node>) {
        self.children.borrow_mut().push(child);
    }
}
```

### 2. Smart Pointers
```rust
use std::rc::{Rc, Weak};
use std::sync::Arc;

// Rc for single-threaded reference counting
let a = Rc::new(String::from("hello"));
let b = Rc::clone(&a);
let c = Rc::clone(&a);
println!("Reference count: {}", Rc::strong_count(&a));

// Weak references to prevent cycles
struct Node {
    value: i32,
    parent: RefCell<Weak<Node>>,
    children: RefCell<Vec<Rc<Node>>>,
}

// Arc for thread-safe reference counting
let data = Arc::new(vec![1, 2, 3]);
let data_clone = Arc::clone(&data);
std::thread::spawn(move || {
    println!("{:?}", data_clone);
});
```

### 3. Preventing Common Errors

#### Use After Free Prevention
```rust
// Rust prevents use after free at compile time
fn no_use_after_free() {
    let r;
    {
        let x = 5;
        // r = &x; // Error: `x` does not live long enough
    }
    // println!("{}", r); // Would be use after free
}
```

#### Null Pointer Prevention
```rust
// Rust uses Option instead of null pointers
fn safe_division(numerator: f64, denominator: f64) -> Option<f64> {
    if denominator == 0.0 {
        None
    } else {
        Some(numerator / denominator)
    }
}

// Pattern matching ensures handling
match safe_division(10.0, 0.0) {
    Some(result) => println!("Result: {}", result),
    None => println!("Cannot divide by zero"),
}
```

#### Data Race Prevention
```rust
use std::sync::{Arc, Mutex};
use std::thread;

// Safe concurrent access
let counter = Arc::new(Mutex::new(0));
let mut handles = vec![];

for _ in 0..10 {
    let counter = Arc::clone(&counter);
    let handle = thread::spawn(move || {
        let mut num = counter.lock().unwrap();
        *num += 1;
    });
    handles.push(handle);
}

for handle in handles {
    handle.join().unwrap();
}
```

## Best Practices

### 1. Prefer Borrowing Over Moving
```rust
// Good: Borrow when you don't need ownership
fn process(data: &str) {
    println!("Processing: {}", data);
}

// Avoid: Taking ownership unnecessarily
fn process_owned(data: String) {
    println!("Processing: {}", data);
}
```

### 2. Use Clone Judiciously
```rust
// Consider if you really need to clone
#[derive(Clone)]
struct ExpensiveData {
    data: Vec<u8>,
}

// Good: Pass reference when possible
fn analyze(data: &ExpensiveData) -> usize {
    data.data.len()
}

// Avoid: Cloning when not necessary
fn analyze_cloned(data: ExpensiveData) -> usize {
    data.data.len()
}
```

### 3. Leverage Lifetime Elision
```rust
// Let the compiler infer lifetimes when possible
fn get_first(s: &str) -> &str {
    // Compiler infers: fn get_first<'a>(s: &'a str) -> &'a str
    &s[..1]
}

// Only annotate when necessary
fn get_longer<'a>(s1: &'a str, s2: &'a str) -> &'a str {
    if s1.len() > s2.len() { s1 } else { s2 }
}
```

### 4. Use Appropriate Smart Pointers
```rust
// Box for heap allocation
let b = Box::new(5);

// Rc for shared ownership (single-threaded)
let rc = Rc::new(vec![1, 2, 3]);

// Arc for shared ownership (multi-threaded)
let arc = Arc::new(vec![1, 2, 3]);

// RefCell for interior mutability
let cell = RefCell::new(5);
```

## Common Pitfalls and Solutions

### 1. Fighting the Borrow Checker
```rust
// Problem: Trying to mutate while borrowed
fn bad_pattern() {
    let mut vec = vec![1, 2, 3];
    // for item in &vec {
    //     vec.push(*item); // Error: cannot borrow as mutable
    // }
}

// Solution: Separate iteration from mutation
fn good_pattern() {
    let mut vec = vec![1, 2, 3];
    let items_to_add: Vec<_> = vec.iter().copied().collect();
    for item in items_to_add {
        vec.push(item);
    }
}
```

### 2. Lifetime Confusion
```rust
// Problem: Unclear lifetime relationships
// fn confusing<'a, 'b>(x: &'a str, y: &'b str) -> &'a str { x }

// Solution: Use single lifetime when appropriate
fn clear<'a>(x: &'a str, _y: &str) -> &'a str { x }
```

### 3. Unnecessary Complexity
```rust
// Problem: Over-engineering with smart pointers
// let x = Rc::new(RefCell::new(Box::new(5)));

// Solution: Use the simplest type that works
let x = 5;
```