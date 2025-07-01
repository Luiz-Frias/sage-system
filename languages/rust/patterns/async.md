# Rust Async Patterns with Tokio

## Overview
Asynchronous programming in Rust with Tokio enables efficient concurrent operations through futures and async/await syntax, providing high-performance I/O operations without the overhead of OS threads.

## Core Async Patterns

### 1. Basic Async/Await
```rust
use tokio::time::{sleep, Duration};

async fn fetch_data() -> Result<String, Error> {
    // Simulate async operation
    sleep(Duration::from_millis(100)).await;
    Ok("Data fetched".to_string())
}

#[tokio::main]
async fn main() {
    match fetch_data().await {
        Ok(data) => println!("Received: {}", data),
        Err(e) => eprintln!("Error: {}", e),
    }
}
```

### 2. Concurrent Execution with join!
```rust
use tokio::join;

async fn fetch_user(id: u64) -> User {
    // Async user fetch
    sleep(Duration::from_millis(100)).await;
    User { id, name: format!("User{}", id) }
}

async fn fetch_posts(user_id: u64) -> Vec<Post> {
    // Async posts fetch
    sleep(Duration::from_millis(150)).await;
    vec![Post { id: 1, user_id, content: "Hello".to_string() }]
}

async fn load_user_data(id: u64) -> (User, Vec<Post>) {
    // Execute both operations concurrently
    let (user, posts) = join!(
        fetch_user(id),
        fetch_posts(id)
    );
    
    (user, posts)
}
```

### 3. Select Pattern
```rust
use tokio::select;
use tokio::time::timeout;

async fn race_operations() -> Result<String, Error> {
    select! {
        result = fetch_from_primary() => {
            println!("Primary responded first");
            result
        }
        result = fetch_from_secondary() => {
            println!("Secondary responded first");
            result
        }
        _ = sleep(Duration::from_secs(5)) => {
            println!("Operation timed out");
            Err(Error::Timeout)
        }
    }
}

// Biased select for priority
async fn priority_select() {
    loop {
        select! {
            // biased ensures high priority is checked first
            biased;
            
            Some(task) = high_priority_queue.recv() => {
                process_high_priority(task).await;
            }
            Some(task) = normal_priority_queue.recv() => {
                process_normal_priority(task).await;
            }
            else => {
                // All channels closed
                break;
            }
        }
    }
}
```

### 4. Spawning Tasks
```rust
use tokio::task;
use tokio::sync::mpsc;

async fn spawn_pattern() {
    let (tx, mut rx) = mpsc::channel(32);

    // Spawn a task
    let handle = tokio::spawn(async move {
        for i in 0..10 {
            tx.send(i).await.unwrap();
            sleep(Duration::from_millis(100)).await;
        }
    });

    // Process messages
    while let Some(value) = rx.recv().await {
        println!("Received: {}", value);
    }

    // Wait for the spawned task to complete
    handle.await.unwrap();
}

// Spawn with error handling
async fn spawn_with_result() -> Result<(), Box<dyn std::error::Error>> {
    let handle = tokio::spawn(async {
        // Task that might fail
        risky_operation().await
    });

    // Handle both spawn error and task error
    match handle.await {
        Ok(Ok(result)) => println!("Success: {:?}", result),
        Ok(Err(e)) => eprintln!("Task error: {}", e),
        Err(e) => eprintln!("Spawn error: {}", e),
    }

    Ok(())
}
```

### 5. Channel Patterns
```rust
use tokio::sync::{mpsc, oneshot, broadcast};

// Multi-producer, single-consumer
async fn mpsc_pattern() {
    let (tx, mut rx) = mpsc::channel::<Message>(100);

    // Multiple producers
    for i in 0..5 {
        let tx = tx.clone();
        tokio::spawn(async move {
            tx.send(Message::new(i)).await.unwrap();
        });
    }

    // Single consumer
    while let Some(msg) = rx.recv().await {
        process_message(msg).await;
    }
}

// One-shot channel for request/response
async fn oneshot_pattern() -> Result<Response, Error> {
    let (tx, rx) = oneshot::channel();

    tokio::spawn(async move {
        let result = expensive_computation().await;
        let _ = tx.send(result);
    });

    rx.await.map_err(|_| Error::ChannelClosed)
}

// Broadcast for pub/sub
async fn broadcast_pattern() {
    let (tx, _) = broadcast::channel::<Event>(16);

    // Spawn subscribers
    for i in 0..3 {
        let mut rx = tx.subscribe();
        tokio::spawn(async move {
            while let Ok(event) = rx.recv().await {
                println!("Subscriber {} received: {:?}", i, event);
            }
        });
    }

    // Publish events
    tx.send(Event::Started).unwrap();
    tx.send(Event::Progress(50)).unwrap();
    tx.send(Event::Completed).unwrap();
}
```

### 6. Mutex and RwLock Patterns
```rust
use tokio::sync::{Mutex, RwLock};
use std::sync::Arc;

// Shared state with Mutex
async fn mutex_pattern() {
    let counter = Arc::new(Mutex::new(0));

    let mut handles = vec![];

    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let handle = tokio::spawn(async move {
            let mut num = counter.lock().await;
            *num += 1;
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.await.unwrap();
    }

    println!("Counter: {}", *counter.lock().await);
}

// Read-heavy workload with RwLock
async fn rwlock_pattern() {
    let data = Arc::new(RwLock::new(HashMap::new()));

    // Writer task
    let data_w = Arc::clone(&data);
    tokio::spawn(async move {
        loop {
            let mut map = data_w.write().await;
            map.insert(rand::random(), rand::random());
            drop(map); // Explicitly drop to release lock
            sleep(Duration::from_millis(100)).await;
        }
    });

    // Multiple reader tasks
    for i in 0..5 {
        let data_r = Arc::clone(&data);
        tokio::spawn(async move {
            loop {
                let map = data_r.read().await;
                println!("Reader {} sees {} items", i, map.len());
                drop(map);
                sleep(Duration::from_millis(50)).await;
            }
        });
    }
}
```

### 7. Stream Processing
```rust
use tokio_stream::{Stream, StreamExt};
use futures::stream;

// Basic stream processing
async fn stream_pattern() {
    let stream = stream::iter(vec![1, 2, 3, 4, 5]);

    let processed: Vec<_> = stream
        .map(|x| x * 2)
        .filter(|x| x % 3 != 0)
        .collect()
        .await;

    println!("Processed: {:?}", processed);
}

// Async stream transformation
async fn async_stream_transform() {
    let urls = vec!["url1", "url2", "url3"];
    let stream = stream::iter(urls);

    let results: Vec<_> = stream
        .map(|url| async move {
            fetch_url(url).await
        })
        .buffer_unordered(3) // Process up to 3 concurrently
        .collect()
        .await;
}

// Custom stream implementation
use std::pin::Pin;
use std::task::{Context, Poll};

struct IntervalStream {
    interval: tokio::time::Interval,
    count: u64,
}

impl Stream for IntervalStream {
    type Item = u64;

    fn poll_next(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        match self.interval.poll_tick(cx) {
            Poll::Ready(_) => {
                let count = self.count;
                self.count += 1;
                Poll::Ready(Some(count))
            }
            Poll::Pending => Poll::Pending,
        }
    }
}
```

### 8. Timeout and Retry Patterns
```rust
use tokio::time::timeout;
use std::time::Duration;

// Basic timeout
async fn with_timeout() -> Result<String, Error> {
    match timeout(Duration::from_secs(5), fetch_data()).await {
        Ok(Ok(data)) => Ok(data),
        Ok(Err(e)) => Err(e),
        Err(_) => Err(Error::Timeout),
    }
}

// Retry with exponential backoff
async fn retry_with_backoff<F, Fut, T, E>(
    mut operation: F,
    max_retries: u32,
) -> Result<T, E>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = Result<T, E>>,
    E: std::fmt::Display,
{
    let mut retries = 0;
    let mut delay = Duration::from_millis(100);

    loop {
        match operation().await {
            Ok(result) => return Ok(result),
            Err(e) if retries < max_retries => {
                eprintln!("Attempt {} failed: {}, retrying in {:?}", retries + 1, e, delay);
                sleep(delay).await;
                delay *= 2; // Exponential backoff
                retries += 1;
            }
            Err(e) => return Err(e),
        }
    }
}
```

### 9. Graceful Shutdown Pattern
```rust
use tokio::signal;
use tokio::sync::watch;

async fn graceful_shutdown() {
    let (shutdown_tx, shutdown_rx) = watch::channel(false);

    // Spawn workers
    let mut handles = vec![];
    for i in 0..3 {
        let mut shutdown_rx = shutdown_rx.clone();
        let handle = tokio::spawn(async move {
            loop {
                select! {
                    _ = do_work(i) => {
                        // Work completed
                    }
                    _ = shutdown_rx.changed() => {
                        if *shutdown_rx.borrow() {
                            println!("Worker {} shutting down", i);
                            break;
                        }
                    }
                }
            }
        });
        handles.push(handle);
    }

    // Wait for shutdown signal
    signal::ctrl_c().await.unwrap();
    println!("Shutdown signal received");

    // Notify all workers to shutdown
    shutdown_tx.send(true).unwrap();

    // Wait for all workers to finish
    for handle in handles {
        handle.await.unwrap();
    }

    println!("Graceful shutdown complete");
}
```

### 10. Connection Pool Pattern
```rust
use tokio::sync::Semaphore;
use std::sync::Arc;

struct ConnectionPool {
    connections: Arc<Mutex<Vec<Connection>>>,
    semaphore: Arc<Semaphore>,
    max_connections: usize,
}

impl ConnectionPool {
    fn new(max_connections: usize) -> Self {
        Self {
            connections: Arc::new(Mutex::new(Vec::new())),
            semaphore: Arc::new(Semaphore::new(max_connections)),
            max_connections,
        }
    }

    async fn get(&self) -> Result<PooledConnection, Error> {
        // Acquire permit
        let permit = self.semaphore.acquire().await?;

        // Try to reuse existing connection
        let mut connections = self.connections.lock().await;
        if let Some(conn) = connections.pop() {
            return Ok(PooledConnection {
                conn: Some(conn),
                pool: self.connections.clone(),
                _permit: permit,
            });
        }
        drop(connections);

        // Create new connection
        let conn = Connection::new().await?;
        Ok(PooledConnection {
            conn: Some(conn),
            pool: self.connections.clone(),
            _permit: permit,
        })
    }
}

struct PooledConnection {
    conn: Option<Connection>,
    pool: Arc<Mutex<Vec<Connection>>>,
    _permit: SemaphorePermit<'static>,
}

impl Drop for PooledConnection {
    fn drop(&mut self) {
        if let Some(conn) = self.conn.take() {
            let pool = self.pool.clone();
            tokio::spawn(async move {
                let mut connections = pool.lock().await;
                connections.push(conn);
            });
        }
    }
}
```

## Best Practices

### 1. Avoid Blocking Operations
```rust
// Bad - blocks the executor
async fn bad_example() {
    std::thread::sleep(Duration::from_secs(1)); // Blocks!
}

// Good - use async alternatives
async fn good_example() {
    tokio::time::sleep(Duration::from_secs(1)).await;
}

// For CPU-intensive work, use spawn_blocking
async fn cpu_intensive_work() -> Result<u64, Error> {
    tokio::task::spawn_blocking(|| {
        // Heavy computation
        calculate_prime(1_000_000)
    })
    .await?
}
```

### 2. Proper Error Handling
```rust
// Define custom error types
#[derive(Debug, thiserror::Error)]
enum ServiceError {
    #[error("Network error: {0}")]
    Network(#[from] reqwest::Error),
    
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
    
    #[error("Timeout")]
    Timeout,
}

// Use Result in async functions
async fn fetch_user(id: u64) -> Result<User, ServiceError> {
    let user = timeout(
        Duration::from_secs(5),
        database.get_user(id)
    )
    .await
    .map_err(|_| ServiceError::Timeout)??;
    
    Ok(user)
}
```

### 3. Structured Concurrency
```rust
use tokio::task::JoinSet;

async fn structured_concurrency() -> Result<Vec<Result<Data, Error>>, Error> {
    let mut set = JoinSet::new();

    // Spawn tasks into the set
    for id in 0..10 {
        set.spawn(async move {
            fetch_data(id).await
        });
    }

    // Collect all results
    let mut results = Vec::new();
    while let Some(result) = set.join_next().await {
        results.push(result?);
    }

    Ok(results)
}
```

### 4. Resource Cleanup
```rust
// Use RAII for cleanup
struct TempResource {
    id: u64,
}

impl Drop for TempResource {
    fn drop(&mut self) {
        // Cleanup happens automatically
        println!("Cleaning up resource {}", self.id);
    }
}

// Async cleanup with defer pattern
async fn with_cleanup<F, Fut, T>(f: F) -> T
where
    F: FnOnce() -> Fut,
    Fut: Future<Output = T>,
{
    let result = f().await;
    cleanup().await;
    result
}
```