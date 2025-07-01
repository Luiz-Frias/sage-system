# Rust Error Handling Patterns

## Overview
Rust's `Result<T, E>` type is the cornerstone of error handling, providing compile-time guarantees that errors are handled properly.

## Core Patterns

### 1. Basic Result Pattern
```rust
use std::fs::File;
use std::io::{self, Read};

fn read_file_contents(path: &str) -> Result<String, io::Error> {
    let mut file = File::open(path)?;
    let mut contents = String::new();
    file.read_to_string(&mut contents)?;
    Ok(contents)
}
```

### 2. Custom Error Types
```rust
use std::fmt;
use std::error::Error;

#[derive(Debug)]
enum AppError {
    Io(std::io::Error),
    Parse(std::num::ParseIntError),
    Validation(String),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            AppError::Io(err) => write!(f, "IO error: {}", err),
            AppError::Parse(err) => write!(f, "Parse error: {}", err),
            AppError::Validation(msg) => write!(f, "Validation error: {}", msg),
        }
    }
}

impl Error for AppError {}

// Implement From for automatic conversion
impl From<std::io::Error> for AppError {
    fn from(err: std::io::Error) -> Self {
        AppError::Io(err)
    }
}

impl From<std::num::ParseIntError> for AppError {
    fn from(err: std::num::ParseIntError) -> Self {
        AppError::Parse(err)
    }
}
```

### 3. Error Chaining with `thiserror`
```rust
use thiserror::Error;

#[derive(Error, Debug)]
enum DatabaseError {
    #[error("connection failed")]
    ConnectionFailed(#[from] std::io::Error),
    
    #[error("query failed: {0}")]
    QueryFailed(String),
    
    #[error("record not found for id: {id}")]
    NotFound { id: u64 },
}
```

### 4. Result Combinators
```rust
fn process_data(input: &str) -> Result<i32, AppError> {
    input
        .parse::<i32>()
        .map_err(AppError::from)
        .and_then(|n| {
            if n > 0 {
                Ok(n * 2)
            } else {
                Err(AppError::Validation("Number must be positive".to_string()))
            }
        })
        .map(|n| n + 10)
}
```

### 5. Early Return Pattern
```rust
fn complex_operation() -> Result<String, AppError> {
    // Early return on error
    let config = load_config()?;
    let connection = establish_connection(&config)?;
    let data = fetch_data(&connection)?;
    
    // Process data
    Ok(process(data))
}
```

### 6. Option to Result Conversion
```rust
fn find_user(id: u64) -> Result<User, AppError> {
    users
        .get(&id)
        .cloned()
        .ok_or_else(|| AppError::Validation(format!("User {} not found", id)))
}
```

### 7. Collecting Results
```rust
fn validate_all(items: Vec<String>) -> Result<Vec<i32>, AppError> {
    items
        .into_iter()
        .map(|s| s.parse::<i32>().map_err(AppError::from))
        .collect()
}
```

### 8. Error Context with `anyhow`
```rust
use anyhow::{Context, Result};

fn load_configuration() -> Result<Config> {
    let contents = std::fs::read_to_string("config.toml")
        .context("Failed to read configuration file")?;
    
    toml::from_str(&contents)
        .context("Failed to parse configuration")
}
```

## Best Practices

### 1. Use `?` for Error Propagation
```rust
// Good
fn read_number() -> Result<i32, Box<dyn Error>> {
    let contents = std::fs::read_to_string("number.txt")?;
    let number = contents.trim().parse()?;
    Ok(number)
}

// Avoid
fn read_number_verbose() -> Result<i32, Box<dyn Error>> {
    match std::fs::read_to_string("number.txt") {
        Ok(contents) => {
            match contents.trim().parse() {
                Ok(number) => Ok(number),
                Err(e) => Err(Box::new(e)),
            }
        }
        Err(e) => Err(Box::new(e)),
    }
}
```

### 2. Provide Context
```rust
fn process_file(path: &str) -> Result<Data, AppError> {
    let contents = std::fs::read_to_string(path)
        .map_err(|e| AppError::Validation(
            format!("Failed to read file '{}': {}", path, e)
        ))?;
    
    parse_data(&contents)
}
```

### 3. Type-Specific Error Handling
```rust
fn handle_specific_errors() -> Result<(), AppError> {
    match risky_operation() {
        Ok(value) => process(value),
        Err(AppError::Io(e)) if e.kind() == io::ErrorKind::NotFound => {
            // Handle missing file specifically
            create_default_file()
        }
        Err(e) => Err(e),
    }
}
```

### 4. Panic vs. Error Return
```rust
// Return error for recoverable situations
pub fn divide(a: f64, b: f64) -> Result<f64, String> {
    if b == 0.0 {
        Err("Division by zero".to_string())
    } else {
        Ok(a / b)
    }
}

// Panic for programmer errors
pub fn get_item(index: usize) -> &Item {
    assert!(index < self.items.len(), "Index out of bounds");
    &self.items[index]
}
```

## Common Pitfalls

1. **Over-using `unwrap()`**: Replace with proper error handling
2. **Generic error types**: Use specific error types for better debugging
3. **Losing error context**: Add context when converting errors
4. **Ignoring errors**: Always handle or explicitly propagate errors

## Testing Error Cases
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_conditions() {
        assert!(divide(10.0, 0.0).is_err());
        
        match divide(10.0, 0.0) {
            Err(msg) => assert_eq!(msg, "Division by zero"),
            Ok(_) => panic!("Expected error"),
        }
    }
}
```