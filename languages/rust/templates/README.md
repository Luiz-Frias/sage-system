# Rust Templates

This directory contains reusable templates for common Rust project structures and patterns.

## Available Templates

### 1. CLI Application Template
A complete template for building command-line applications with:
- Clap for argument parsing
- Error handling with anyhow
- Logging with env_logger
- Configuration management
- Testing structure

### 2. Web API Template
REST API template featuring:
- Actix-web or Axum framework
- Database integration (SQLx)
- Authentication middleware
- OpenAPI documentation
- Docker support

### 3. Library Template
Rust library template with:
- Comprehensive documentation
- Example usage
- Benchmark setup
- CI/CD configuration
- Publishing guidelines

### 4. Async Service Template
Tokio-based async service with:
- Graceful shutdown
- Health checks
- Metrics collection
- Distributed tracing
- Message queue integration

### 5. WebAssembly Template
WASM project template including:
- wasm-bindgen setup
- JavaScript interop
- Build optimization
- Testing in Node.js
- Deployment examples

## Usage

Each template includes:
- Complete project structure
- Cargo.toml with common dependencies
- README with setup instructions
- Example code demonstrating best practices
- GitHub Actions workflow
- Pre-configured development tools

## Template Structure

```
template-name/
├── Cargo.toml           # Configured dependencies
├── README.md            # Setup and usage instructions
├── src/
│   ├── main.rs         # Application entry point
│   ├── lib.rs          # Library root (if applicable)
│   └── modules/        # Organized code modules
├── tests/
│   └── integration/    # Integration tests
├── benches/            # Benchmarks
├── examples/           # Usage examples
└── .github/
    └── workflows/      # CI/CD configuration
```

## Quick Start

1. Copy the desired template directory
2. Rename the project in Cargo.toml
3. Update the README with project-specific information
4. Run `cargo build` to verify setup
5. Begin development!

## Contributing Templates

When adding new templates:
1. Follow Rust best practices and idioms
2. Include comprehensive documentation
3. Add example usage and tests
4. Ensure all dependencies are up-to-date
5. Test the template in a fresh environment