---
name: Best Practices
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# Rust Best Practices and Idioms

## Overview
This guide covers idiomatic Rust patterns, conventions, and best practices that lead to maintainable, efficient, and safe code.

## Code Organization

### 1. Module Structure
```rust
// Prefer clear module hierarchy
// src/lib.rs
pub mod network {
    pub mod client;
    pub mod server;
    
    // Re-export commonly used items
    pub use client::Client;
    pub use server::Server;
}

// src/network/client.rs
use super::common::{Config, Error};

pub struct Client {
    config: Config,
}

impl Client {
    pub fn new(config: Config) -> Self {
        Client { config }
    }
}
```

### 2. Use Statements Organization
```rust
// Group and order imports consistently
// 1. Standard library
use std::collections::{HashMap, HashSet};
use std::io::{self, Read, Write};

// 2. External crates
use serde::{Deserialize, Serialize};
use tokio::sync::Mutex;

// 3. Internal crates
use crate::config::Config;
use crate::error::{Error, Result};

// 4. Module declarations
mod handlers;
mod utils;
```

### 3. Public API Design
```rust
// Keep public API minimal and intentional
pub struct Connection {
    // Private fields
    socket: TcpStream,
    buffer: Vec<u8>,
}

impl Connection {
    // Constructor
    pub fn new(addr: &str) -> Result<Self> {
        // Implementation
    }
    
    // Public methods expose behavior, not implementation
    pub fn send(&mut self, data: &[u8]) -> Result<()> {
        // Implementation
    }
    
    // Private helper methods
    fn flush_buffer(&mut self) -> Result<()> {
        // Implementation
    }
}
```

## Error Handling Idioms

### 1. Custom Error Types
```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("IO error occurred")]
    Io(#[from] std::io::Error),
    
    #[error("Parse error: {0}")]
    Parse(String),
    
    #[error("Invalid configuration: {msg}")]
    Config { msg: String },
    
    #[error("Network error")]
    Network(#[source] Box<dyn std::error::Error + Send + Sync>),
}

// Type alias for convenience
pub type Result<T> = std::result::Result<T, AppError>;
```

### 2. Error Propagation
```rust
// Use ? operator for clean error propagation
fn process_file(path: &Path) -> Result<String> {
    let mut file = File::open(path)?;
    let mut contents = String::new();
    file.read_to_string(&mut contents)?;
    Ok(contents.to_uppercase())
}

// Add context to errors
use anyhow::{Context, Result};

fn load_config() -> Result<Config> {
    let path = "config.toml";
    let contents = std::fs::read_to_string(path)
        .with_context(|| format!("Failed to read config from {}", path))?;
    
    toml::from_str(&contents)
        .with_context(|| "Failed to parse config file")
}
```

## Type System Best Practices

### 1. Newtype Pattern
```rust
// Use newtype for type safety
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct UserId(u64);

#[derive(Debug, Clone)]
pub struct Email(String);

impl Email {
    pub fn new(email: String) -> Result<Self, ValidationError> {
        if email.contains('@') {
            Ok(Email(email))
        } else {
            Err(ValidationError::InvalidEmail)
        }
    }
}

// Prevent mixing up parameters
fn send_email(user_id: UserId, email: Email) {
    // Can't accidentally swap parameters
}
```

### 2. Builder Pattern
```rust
#[derive(Default)]
pub struct ServerBuilder {
    port: Option<u16>,
    workers: Option<usize>,
    timeout: Option<Duration>,
}

impl ServerBuilder {
    pub fn new() -> Self {
        Self::default()
    }
    
    pub fn port(mut self, port: u16) -> Self {
        self.port = Some(port);
        self
    }
    
    pub fn workers(mut self, workers: usize) -> Self {
        self.workers = Some(workers);
        self
    }
    
    pub fn build(self) -> Result<Server> {
        Ok(Server {
            port: self.port.ok_or(Error::MissingPort)?,
            workers: self.workers.unwrap_or(num_cpus::get()),
            timeout: self.timeout.unwrap_or(Duration::from_secs(30)),
        })
    }
}
```

### 3. Type State Pattern
```rust
pub struct Button<State> {
    text: String,
    _state: PhantomData<State>,
}

pub struct Enabled;
pub struct Disabled;

impl Button<Disabled> {
    pub fn enable(self) -> Button<Enabled> {
        Button {
            text: self.text,
            _state: PhantomData,
        }
    }
}

impl Button<Enabled> {
    pub fn click(&self) {
        println!("Button clicked: {}", self.text);
    }
    
    pub fn disable(self) -> Button<Disabled> {
        Button {
            text: self.text,
            _state: PhantomData,
        }
    }
}
```

## Performance Idioms

### 1. Zero-Cost Abstractions
```rust
// Use iterators instead of loops when possible
let sum: i32 = numbers
    .iter()
    .filter(|&&x| x > 0)
    .map(|&x| x * 2)
    .sum();

// Avoid unnecessary allocations
fn process_data(data: &[u8]) -> Vec<u8> {
    // Pre-allocate with capacity
    let mut result = Vec::with_capacity(data.len());
    
    for &byte in data {
        if byte > 0 {
            result.push(byte * 2);
        }
    }
    
    result
}
```

### 2. Avoid Cloning
```rust
// Use references when possible
fn find_max(numbers: &[i32]) -> Option<&i32> {
    numbers.iter().max()
}

// Use Cow for conditional cloning
use std::borrow::Cow;

fn process_string(s: &str) -> Cow<str> {
    if s.contains("old") {
        Cow::Owned(s.replace("old", "new"))
    } else {
        Cow::Borrowed(s)
    }
}
```

### 3. Efficient String Handling
```rust
// Use &str for function parameters
fn greet(name: &str) -> String {
    format!("Hello, {}!", name)
}

// Use String::with_capacity for known sizes
fn concatenate(parts: &[&str]) -> String {
    let total_len = parts.iter().map(|s| s.len()).sum();
    let mut result = String::with_capacity(total_len);
    
    for part in parts {
        result.push_str(part);
    }
    
    result
}
```

## Trait Best Practices

### 1. Derive Common Traits
```rust
// Always derive these when appropriate
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Point {
    x: i32,
    y: i32,
}

// Implement Display for user-facing output
impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}
```

### 2. Trait Bounds
```rust
// Be specific with trait bounds
fn process_items<T, I>(items: I) -> Vec<T>
where
    T: Clone + Send + 'static,
    I: IntoIterator<Item = T>,
{
    items.into_iter().collect()
}

// Use where clauses for readability
fn complex_function<T, U, V>(t: T, u: U) -> V
where
    T: Display + Clone,
    U: Debug + Send,
    V: From<T> + Default,
{
    // Implementation
}
```

### 3. Extension Traits
```rust
// Add methods to external types
pub trait VecExt<T> {
    fn sorted(self) -> Vec<T>;
}

impl<T: Ord> VecExt<T> for Vec<T> {
    fn sorted(mut self) -> Vec<T> {
        self.sort();
        self
    }
}

// Usage
let sorted = vec![3, 1, 4, 1, 5].sorted();
```

## Testing Best Practices

### 1. Test Organization
```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    // Group related tests
    mod parser_tests {
        use super::*;
        
        #[test]
        fn parses_valid_input() {
            let input = "valid";
            let result = parse(input);
            assert!(result.is_ok());
        }
        
        #[test]
        fn rejects_invalid_input() {
            let input = "";
            let result = parse(input);
            assert!(result.is_err());
        }
    }
    
    // Use descriptive test names
    #[test]
    fn user_with_valid_email_can_be_created() {
        let user = User::new("test@example.com");
        assert!(user.is_ok());
    }
}
```

### 2. Property-Based Testing
```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn reversing_twice_is_identity(s: String) {
        let reversed_twice: String = s.chars().rev().collect::<String>()
            .chars().rev().collect();
        prop_assert_eq!(s, reversed_twice);
    }
}
```

### 3. Test Helpers
```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    // Test fixtures
    fn create_test_user() -> User {
        User::new("test@example.com").unwrap()
    }
    
    // Custom assertions
    fn assert_error_kind(result: Result<()>, expected: ErrorKind) {
        match result {
            Err(e) if e.kind() == expected => (),
            _ => panic!("Expected error kind {:?}", expected),
        }
    }
}
```

## Documentation Best Practices

### 1. Doc Comments
```rust
/// Processes a batch of items concurrently.
///
/// # Arguments
///
/// * `items` - A slice of items to process
/// * `max_concurrent` - Maximum number of concurrent operations
///
/// # Returns
///
/// A vector of processed results in the same order as the input.
///
/// # Errors
///
/// Returns an error if any item fails to process.
///
/// # Examples
///
/// ```
/// use my_crate::process_batch;
///
/// let items = vec![1, 2, 3, 4, 5];
/// let results = process_batch(&items, 2).unwrap();
/// assert_eq!(results.len(), items.len());
/// ```
pub fn process_batch<T>(items: &[T], max_concurrent: usize) -> Result<Vec<T::Output>>
where
    T: Process,
{
    // Implementation
}
```

### 2. Module Documentation
```rust
//! # Network Module
//!
//! This module provides networking functionality including:
//! 
//! - TCP client and server implementations
//! - Protocol parsing and serialization
//! - Connection pooling
//!
//! ## Examples
//!
//! ```no_run
//! use my_crate::network::{Client, Config};
//!
//! let config = Config::default();
//! let client = Client::new(config);
//! ```

pub mod client;
pub mod server;
```

## Common Anti-Patterns to Avoid

### 1. Overuse of `unwrap()`
```rust
// Bad
let value = some_option.unwrap();

// Good
let value = some_option.expect("Value should exist because...");

// Better
if let Some(value) = some_option {
    // Use value
}

// Or use match for error handling
match some_result {
    Ok(value) => process(value),
    Err(e) => log::error!("Failed to get value: {}", e),
}
```

### 2. Excessive Cloning
```rust
// Bad
fn get_name(&self) -> String {
    self.name.clone()
}

// Good
fn get_name(&self) -> &str {
    &self.name
}
```

### 3. Ignoring Clippy Warnings
```rust
// Run clippy regularly
// cargo clippy -- -W clippy::all

// Fix or explicitly allow warnings
#[allow(clippy::too_many_arguments)]
fn complex_function(/* many args */) {
    // Sometimes necessary, but document why
}
```

### 4. Not Using Type Inference
```rust
// Overly explicit
let numbers: Vec<i32> = vec![1, 2, 3];
let sum: i32 = numbers.iter().sum::<i32>();

// Better - let Rust infer
let numbers = vec![1, 2, 3];
let sum: i32 = numbers.iter().sum();
```

## Rust Idioms Checklist

- ✅ Use `Option` and `Result` instead of null/exceptions
- ✅ Prefer borrowing over owning
- ✅ Use iterators over manual loops
- ✅ Derive standard traits when sensible
- ✅ Keep public APIs minimal
- ✅ Use newtypes for domain modeling
- ✅ Write comprehensive tests
- ✅ Document public APIs with examples
- ✅ Run `cargo fmt` and `cargo clippy` regularly
- ✅ Use `#[must_use]` for types that shouldn't be ignored