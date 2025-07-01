# Rust Type State Pattern

## Overview
The Type State pattern uses Rust's type system to encode state machines at compile time, ensuring invalid state transitions are caught during compilation rather than at runtime.

## Core Concepts

### 1. Basic Type State Pattern
```rust
// Define states as zero-sized types
pub struct Locked;
pub struct Unlocked;

// Generic struct parameterized by state
pub struct Door<State> {
    _state: std::marker::PhantomData<State>,
}

// State-specific implementations
impl Door<Locked> {
    pub fn new() -> Self {
        Door {
            _state: std::marker::PhantomData,
        }
    }

    pub fn unlock(self) -> Door<Unlocked> {
        println!("Unlocking door");
        Door {
            _state: std::marker::PhantomData,
        }
    }
}

impl Door<Unlocked> {
    pub fn lock(self) -> Door<Locked> {
        println!("Locking door");
        Door {
            _state: std::marker::PhantomData,
        }
    }

    pub fn open(&self) {
        println!("Opening door");
    }
}

// Usage
let door = Door::<Locked>::new();
let door = door.unlock();  // Returns Door<Unlocked>
door.open();               // Only available when unlocked
let door = door.lock();    // Returns Door<Locked>
// door.open();            // Compile error! Method doesn't exist
```

### 2. Connection State Machine
```rust
// Connection states
pub struct Disconnected;
pub struct Connected;
pub struct Authenticated;

pub struct Connection<State> {
    url: String,
    _state: std::marker::PhantomData<State>,
}

impl Connection<Disconnected> {
    pub fn new(url: String) -> Self {
        Connection {
            url,
            _state: std::marker::PhantomData,
        }
    }

    pub fn connect(self) -> Result<Connection<Connected>, ConnectionError> {
        // Perform connection logic
        println!("Connecting to {}", self.url);
        Ok(Connection {
            url: self.url,
            _state: std::marker::PhantomData,
        })
    }
}

impl Connection<Connected> {
    pub fn authenticate(self, credentials: Credentials) -> Result<Connection<Authenticated>, AuthError> {
        // Perform authentication
        println!("Authenticating...");
        Ok(Connection {
            url: self.url,
            _state: std::marker::PhantomData,
        })
    }

    pub fn disconnect(self) -> Connection<Disconnected> {
        println!("Disconnecting");
        Connection {
            url: self.url,
            _state: std::marker::PhantomData,
        }
    }
}

impl Connection<Authenticated> {
    pub fn execute_query(&self, query: &str) -> Result<QueryResult, QueryError> {
        println!("Executing: {}", query);
        // Query execution logic
        Ok(QueryResult::new())
    }

    pub fn disconnect(self) -> Connection<Disconnected> {
        println!("Disconnecting authenticated session");
        Connection {
            url: self.url,
            _state: std::marker::PhantomData,
        }
    }
}
```

### 3. File Handle with Type States
```rust
use std::fs::File;
use std::io::{Read, Write};

// File states
pub struct Closed;
pub struct Open<Mode> {
    file: File,
    _mode: std::marker::PhantomData<Mode>,
}

// File modes
pub struct ReadMode;
pub struct WriteMode;

pub struct FileHandle<State> {
    path: String,
    _state: std::marker::PhantomData<State>,
}

impl FileHandle<Closed> {
    pub fn new(path: String) -> Self {
        FileHandle {
            path,
            _state: std::marker::PhantomData,
        }
    }

    pub fn open_read(self) -> Result<FileHandle<Open<ReadMode>>, std::io::Error> {
        let file = File::open(&self.path)?;
        Ok(FileHandle {
            path: self.path,
            _state: std::marker::PhantomData,
        })
    }

    pub fn open_write(self) -> Result<FileHandle<Open<WriteMode>>, std::io::Error> {
        let file = File::create(&self.path)?;
        Ok(FileHandle {
            path: self.path,
            _state: std::marker::PhantomData,
        })
    }
}

impl FileHandle<Open<ReadMode>> {
    pub fn read(&mut self) -> Result<String, std::io::Error> {
        let mut contents = String::new();
        // Read implementation
        Ok(contents)
    }

    pub fn close(self) -> FileHandle<Closed> {
        FileHandle {
            path: self.path,
            _state: std::marker::PhantomData,
        }
    }
}

impl FileHandle<Open<WriteMode>> {
    pub fn write(&mut self, data: &[u8]) -> Result<(), std::io::Error> {
        // Write implementation
        Ok(())
    }

    pub fn close(self) -> FileHandle<Closed> {
        FileHandle {
            path: self.path,
            _state: std::marker::PhantomData,
        }
    }
}
```

### 4. Order Processing State Machine
```rust
// Order states
pub struct Draft;
pub struct Submitted;
pub struct Approved;
pub struct Shipped;
pub struct Delivered;

pub struct Order<State> {
    id: u64,
    items: Vec<Item>,
    total: f64,
    _state: std::marker::PhantomData<State>,
}

impl Order<Draft> {
    pub fn new(id: u64) -> Self {
        Order {
            id,
            items: Vec::new(),
            total: 0.0,
            _state: std::marker::PhantomData,
        }
    }

    pub fn add_item(&mut self, item: Item) {
        self.total += item.price;
        self.items.push(item);
    }

    pub fn submit(self) -> Result<Order<Submitted>, ValidationError> {
        if self.items.is_empty() {
            return Err(ValidationError::EmptyOrder);
        }
        
        Ok(Order {
            id: self.id,
            items: self.items,
            total: self.total,
            _state: std::marker::PhantomData,
        })
    }
}

impl Order<Submitted> {
    pub fn approve(self, approver: &User) -> Result<Order<Approved>, ApprovalError> {
        // Check approval authority
        if !approver.can_approve(self.total) {
            return Err(ApprovalError::InsufficientAuthority);
        }

        Ok(Order {
            id: self.id,
            items: self.items,
            total: self.total,
            _state: std::marker::PhantomData,
        })
    }

    pub fn reject(self) -> Order<Draft> {
        Order {
            id: self.id,
            items: self.items,
            total: self.total,
            _state: std::marker::PhantomData,
        }
    }
}

impl Order<Approved> {
    pub fn ship(self, tracking_number: String) -> Order<Shipped> {
        println!("Order {} shipped with tracking: {}", self.id, tracking_number);
        Order {
            id: self.id,
            items: self.items,
            total: self.total,
            _state: std::marker::PhantomData,
        }
    }
}

impl Order<Shipped> {
    pub fn deliver(self, signature: String) -> Order<Delivered> {
        println!("Order {} delivered, signed by: {}", self.id, signature);
        Order {
            id: self.id,
            items: self.items,
            total: self.total,
            _state: std::marker::PhantomData,
        }
    }
}
```

### 5. Resource Management with Type States
```rust
// Resource states
pub struct Uninitialized;
pub struct Initialized;
pub struct InUse;

pub struct Resource<State> {
    handle: Option<ResourceHandle>,
    _state: std::marker::PhantomData<State>,
}

impl Resource<Uninitialized> {
    pub fn new() -> Self {
        Resource {
            handle: None,
            _state: std::marker::PhantomData,
        }
    }

    pub fn initialize(mut self) -> Result<Resource<Initialized>, InitError> {
        self.handle = Some(ResourceHandle::acquire()?);
        Ok(Resource {
            handle: self.handle,
            _state: std::marker::PhantomData,
        })
    }
}

impl Resource<Initialized> {
    pub fn acquire(self) -> Resource<InUse> {
        Resource {
            handle: self.handle,
            _state: std::marker::PhantomData,
        }
    }
}

impl Resource<InUse> {
    pub fn use_resource(&self) {
        if let Some(ref handle) = self.handle {
            handle.do_work();
        }
    }

    pub fn release(self) -> Resource<Initialized> {
        Resource {
            handle: self.handle,
            _state: std::marker::PhantomData,
        }
    }
}

impl Drop for Resource<Initialized> {
    fn drop(&mut self) {
        if let Some(handle) = self.handle.take() {
            handle.cleanup();
        }
    }
}
```

### 6. Protocol Implementation
```rust
// Protocol states
pub struct Start;
pub struct HandshakeSent;
pub struct HandshakeReceived;
pub struct Established;

pub struct Protocol<State> {
    socket: TcpStream,
    _state: std::marker::PhantomData<State>,
}

impl Protocol<Start> {
    pub fn initiate(socket: TcpStream) -> Self {
        Protocol {
            socket,
            _state: std::marker::PhantomData,
        }
    }

    pub fn send_handshake(mut self) -> Result<Protocol<HandshakeSent>, ProtocolError> {
        self.socket.write_all(b"HELLO")?;
        Ok(Protocol {
            socket: self.socket,
            _state: std::marker::PhantomData,
        })
    }
}

impl Protocol<HandshakeSent> {
    pub fn receive_handshake(mut self) -> Result<Protocol<HandshakeReceived>, ProtocolError> {
        let mut buffer = [0; 5];
        self.socket.read_exact(&mut buffer)?;
        
        if &buffer == b"HELLO" {
            Ok(Protocol {
                socket: self.socket,
                _state: std::marker::PhantomData,
            })
        } else {
            Err(ProtocolError::InvalidHandshake)
        }
    }
}

impl Protocol<HandshakeReceived> {
    pub fn complete_handshake(mut self) -> Result<Protocol<Established>, ProtocolError> {
        self.socket.write_all(b"ACK")?;
        Ok(Protocol {
            socket: self.socket,
            _state: std::marker::PhantomData,
        })
    }
}

impl Protocol<Established> {
    pub fn send_data(&mut self, data: &[u8]) -> Result<(), ProtocolError> {
        self.socket.write_all(data)?;
        Ok(())
    }

    pub fn receive_data(&mut self) -> Result<Vec<u8>, ProtocolError> {
        let mut buffer = Vec::new();
        self.socket.read_to_end(&mut buffer)?;
        Ok(buffer)
    }
}
```

## Best Practices

### 1. Keep States Zero-Sized
```rust
// Good - zero cost abstraction
pub struct StateA;
pub struct StateB;

// Avoid - adds runtime overhead
pub struct StateWithData {
    data: String,
}
```

### 2. Use Traits for Shared Behavior
```rust
trait ConnectionState {
    fn is_connected(&self) -> bool;
}

impl ConnectionState for Connected {
    fn is_connected(&self) -> bool { true }
}

impl ConnectionState for Disconnected {
    fn is_connected(&self) -> bool { false }
}
```

### 3. Consider Sealed Traits
```rust
mod private {
    pub trait Sealed {}
}

pub trait State: private::Sealed {}

impl private::Sealed for Locked {}
impl private::Sealed for Unlocked {}

impl State for Locked {}
impl State for Unlocked {}
```

### 4. Document State Transitions
```rust
/// A door that can be locked or unlocked.
/// 
/// State transitions:
/// - Locked -> Unlocked (via `unlock()`)
/// - Unlocked -> Locked (via `lock()`)
pub struct Door<State> {
    _state: std::marker::PhantomData<State>,
}
```

## Common Pitfalls and Solutions

### 1. State Data Preservation
```rust
// Problem: Losing data during state transitions
// Solution: Pass data through transitions

pub struct Machine<State> {
    id: u64,
    data: MachineData,
    _state: std::marker::PhantomData<State>,
}

impl Machine<StateA> {
    pub fn transition(self) -> Machine<StateB> {
        Machine {
            id: self.id,        // Preserve fields
            data: self.data,
            _state: std::marker::PhantomData,
        }
    }
}
```

### 2. Runtime State Queries
```rust
// Sometimes you need runtime state information
pub enum RuntimeState {
    Locked,
    Unlocked,
}

impl<State> Door<State> {
    pub fn runtime_state(&self) -> RuntimeState
    where
        State: State,
    {
        State::runtime_state()
    }
}
```

### 3. Error Recovery
```rust
// Allow recovery from failed transitions
impl Connection<Connected> {
    pub fn try_authenticate(self, creds: Credentials) 
        -> Result<Connection<Authenticated>, (Self, AuthError)> 
    {
        match perform_auth(&creds) {
            Ok(_) => Ok(Connection {
                url: self.url,
                _state: std::marker::PhantomData,
            }),
            Err(e) => Err((self, e)), // Return self on error
        }
    }
}
```