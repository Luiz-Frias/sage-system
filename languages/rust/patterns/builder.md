---
name: Builder
purpose: Agent-native directive knowledge source.
layer: knowledge_pack
---

# Objective
Use this document as mandatory structured input. Preserve constraints, IDs, enums, thresholds, examples, and schemas.

# Rust Builder Pattern

## Overview
The Builder pattern in Rust provides a way to construct complex objects step by step, offering a flexible API with optional parameters and compile-time validation.

## Core Implementation

### 1. Basic Builder Pattern
```rust
#[derive(Debug, Clone)]
pub struct Server {
    host: String,
    port: u16,
    max_connections: usize,
    timeout: Duration,
}

pub struct ServerBuilder {
    host: String,
    port: u16,
    max_connections: Option<usize>,
    timeout: Option<Duration>,
}

impl ServerBuilder {
    pub fn new(host: String, port: u16) -> Self {
        ServerBuilder {
            host,
            port,
            max_connections: None,
            timeout: None,
        }
    }

    pub fn max_connections(mut self, max: usize) -> Self {
        self.max_connections = Some(max);
        self
    }

    pub fn timeout(mut self, timeout: Duration) -> Self {
        self.timeout = Some(timeout);
        self
    }

    pub fn build(self) -> Server {
        Server {
            host: self.host,
            port: self.port,
            max_connections: self.max_connections.unwrap_or(100),
            timeout: self.timeout.unwrap_or(Duration::from_secs(30)),
        }
    }
}

// Usage
let server = ServerBuilder::new("localhost".to_string(), 8080)
    .max_connections(200)
    .timeout(Duration::from_secs(60))
    .build();
```

### 2. Builder with Validation
```rust
#[derive(Debug)]
pub enum BuilderError {
    InvalidPort,
    InvalidHost,
    InvalidConfiguration(String),
}

impl ServerBuilder {
    pub fn build(self) -> Result<Server, BuilderError> {
        // Validate configuration
        if self.port == 0 {
            return Err(BuilderError::InvalidPort);
        }

        if self.host.is_empty() {
            return Err(BuilderError::InvalidHost);
        }

        if let Some(max) = self.max_connections {
            if max == 0 {
                return Err(BuilderError::InvalidConfiguration(
                    "Max connections must be greater than 0".to_string()
                ));
            }
        }

        Ok(Server {
            host: self.host,
            port: self.port,
            max_connections: self.max_connections.unwrap_or(100),
            timeout: self.timeout.unwrap_or(Duration::from_secs(30)),
        })
    }
}
```

### 3. Generic Builder Pattern
```rust
pub struct QueryBuilder<T> {
    table: String,
    conditions: Vec<String>,
    limit: Option<usize>,
    _phantom: std::marker::PhantomData<T>,
}

impl<T> QueryBuilder<T> {
    pub fn from_table(table: impl Into<String>) -> Self {
        QueryBuilder {
            table: table.into(),
            conditions: Vec::new(),
            limit: None,
            _phantom: std::marker::PhantomData,
        }
    }

    pub fn where_clause(mut self, condition: impl Into<String>) -> Self {
        self.conditions.push(condition.into());
        self
    }

    pub fn limit(mut self, limit: usize) -> Self {
        self.limit = Some(limit);
        self
    }

    pub fn build(self) -> Query<T> {
        Query {
            sql: self.generate_sql(),
            _phantom: self._phantom,
        }
    }

    fn generate_sql(&self) -> String {
        let mut sql = format!("SELECT * FROM {}", self.table);
        
        if !self.conditions.is_empty() {
            sql.push_str(" WHERE ");
            sql.push_str(&self.conditions.join(" AND "));
        }
        
        if let Some(limit) = self.limit {
            sql.push_str(&format!(" LIMIT {}", limit));
        }
        
        sql
    }
}
```

### 4. Type-State Builder Pattern
```rust
// Type states
pub struct NoAuth;
pub struct Authenticated;
pub struct Ready;

pub struct ClientBuilder<State = NoAuth> {
    endpoint: String,
    auth_token: Option<String>,
    _state: std::marker::PhantomData<State>,
}

impl ClientBuilder<NoAuth> {
    pub fn new(endpoint: impl Into<String>) -> Self {
        ClientBuilder {
            endpoint: endpoint.into(),
            auth_token: None,
            _state: std::marker::PhantomData,
        }
    }

    pub fn with_auth(mut self, token: impl Into<String>) -> ClientBuilder<Authenticated> {
        ClientBuilder {
            endpoint: self.endpoint,
            auth_token: Some(token.into()),
            _state: std::marker::PhantomData,
        }
    }
}

impl ClientBuilder<Authenticated> {
    pub fn configure(self) -> ClientBuilder<Ready> {
        // Additional configuration
        ClientBuilder {
            endpoint: self.endpoint,
            auth_token: self.auth_token,
            _state: std::marker::PhantomData,
        }
    }
}

impl ClientBuilder<Ready> {
    pub fn build(self) -> Client {
        Client {
            endpoint: self.endpoint,
            auth_token: self.auth_token.expect("Auth token must be set"),
        }
    }
}

// Usage - compile-time enforcement of auth requirement
let client = ClientBuilder::new("https://api.example.com")
    .with_auth("secret-token")  // Required step
    .configure()
    .build();
```

### 5. Consuming vs Non-Consuming Builder
```rust
// Consuming builder (takes self)
pub struct ConsumingBuilder {
    data: Vec<String>,
}

impl ConsumingBuilder {
    pub fn add(mut self, item: String) -> Self {
        self.data.push(item);
        self  // Moves ownership
    }
}

// Non-consuming builder (takes &mut self)
pub struct MutableBuilder {
    data: Vec<String>,
}

impl MutableBuilder {
    pub fn add(&mut self, item: String) -> &mut Self {
        self.data.push(item);
        self  // Returns mutable reference
    }
}
```

### 6. Builder with Lifetime Parameters
```rust
pub struct DocumentBuilder<'a> {
    title: &'a str,
    content: Vec<&'a str>,
    metadata: Option<&'a str>,
}

impl<'a> DocumentBuilder<'a> {
    pub fn new(title: &'a str) -> Self {
        DocumentBuilder {
            title,
            content: Vec::new(),
            metadata: None,
        }
    }

    pub fn add_paragraph(mut self, text: &'a str) -> Self {
        self.content.push(text);
        self
    }

    pub fn metadata(mut self, metadata: &'a str) -> Self {
        self.metadata = Some(metadata);
        self
    }

    pub fn build(self) -> Document<'a> {
        Document {
            title: self.title,
            content: self.content,
            metadata: self.metadata,
        }
    }
}
```

### 7. Derive Builder with `derive_builder` Crate
```rust
use derive_builder::Builder;

#[derive(Builder, Debug)]
#[builder(setter(into))]
pub struct EmailMessage {
    #[builder(setter(each = "recipient"))]
    recipients: Vec<String>,
    
    subject: String,
    
    #[builder(setter(strip_option), default)]
    body: Option<String>,
    
    #[builder(default = "false")]
    urgent: bool,
}

// Generated usage
let email = EmailMessageBuilder::default()
    .recipient("alice@example.com")
    .recipient("bob@example.com")
    .subject("Meeting Reminder")
    .body("Don't forget about our meeting at 3 PM")
    .urgent(true)
    .build()
    .unwrap();
```

## Best Practices

### 1. Use `Into` for Flexible APIs
```rust
impl ServerBuilder {
    pub fn host(mut self, host: impl Into<String>) -> Self {
        self.host = Some(host.into());
        self
    }
}

// Allows both &str and String
builder.host("localhost");
builder.host(String::from("localhost"));
```

### 2. Provide Sensible Defaults
```rust
impl Default for ServerBuilder {
    fn default() -> Self {
        ServerBuilder {
            host: "localhost".to_string(),
            port: 8080,
            max_connections: None,
            timeout: None,
        }
    }
}
```

### 3. Consider `must_use` Attribute
```rust
#[must_use = "builders do nothing unless you call .build()"]
pub struct ConfigBuilder {
    // ...
}
```

### 4. Builder Method Naming Conventions
```rust
impl Builder {
    // Setter methods
    pub fn set_name(mut self, name: String) -> Self { ... }
    pub fn with_option(mut self, opt: Option) -> Self { ... }
    
    // Boolean flags
    pub fn enable_feature(mut self) -> Self { ... }
    pub fn disable_feature(mut self) -> Self { ... }
    
    // Collections
    pub fn add_item(mut self, item: Item) -> Self { ... }
    pub fn extend_items(mut self, items: Vec<Item>) -> Self { ... }
}
```

## Common Patterns

### 1. Nested Builders
```rust
let config = ConfigBuilder::new()
    .database(
        DatabaseBuilder::new()
            .host("localhost")
            .port(5432)
            .build()
    )
    .server(
        ServerBuilder::new()
            .port(8080)
            .build()
    )
    .build();
```

### 2. Builder Factory Methods
```rust
impl Server {
    pub fn builder() -> ServerBuilder {
        ServerBuilder::default()
    }
}

// Usage
let server = Server::builder()
    .port(3000)
    .build();
```

### 3. Conditional Building
```rust
let mut builder = ServerBuilder::new();

if development_mode {
    builder = builder.timeout(Duration::from_secs(5));
}

if let Some(port) = env_port {
    builder = builder.port(port);
}

let server = builder.build();
```