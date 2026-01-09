# Soliplex Documentation

Welcome to the Soliplex ecosystem documentation. Soliplex provides AI-powered retrieval-augmented generation capabilities for intelligent document search and question answering.

## Components

### [Core Platform](soliplex/overview.md)

The main Soliplex RAG system with FastAPI backend and Flutter frontend.

**Quick Links:**
- [Prerequisites & Installation](soliplex/prerequisites.md)
- [Server Setup](soliplex/server.md)
- [Docker Deployment](soliplex/docker.md)
- [Configuration Guide](soliplex/config/installation.md)

### [Ingester](ingester/GETTING_STARTED.md)

Robust document ingestion system for loading content into RAG databases.

**Quick Links:**
- [Getting Started](ingester/GETTING_STARTED.md)
- [Architecture](ingester/ARCHITECTURE.md)
- [API Reference](ingester/API.md)
- [CLI Reference](ingester/CLI.md)

## Getting Started

### For New Users

1. [Prerequisites Guide](soliplex/prerequisites.md) - Complete installation checklist
2. [Getting Started with Core Platform](soliplex/server.md) - Set up the backend server
3. [Getting Started with Ingester](ingester/GETTING_STARTED.md) - Document ingestion basics

### For Developers

1. [Core Platform Architecture](soliplex/overview.md) - System design and components
2. [Ingester Architecture](ingester/ARCHITECTURE.md) - Ingestion pipeline design
3. [API References](ingester/API.md) - REST API documentation

### For Operations

1. [Docker Deployment](soliplex/docker.md) - Containerized deployment guide
2. [Configuration Guide](soliplex/config/installation.md) - Installation configuration
3. [Ingester CLI Reference](ingester/CLI.md) - Command-line tool usage

## What is Soliplex?

Soliplex combines the power of retrieval systems with generative AI to provide accurate, contextual responses based on your document collections. The system indexes your documents and uses them to enhance AI responses with relevant, up-to-date information.

### Key Features

- **RAG-Powered Search**: Semantic document retrieval using LanceDB vector database
- **Multi-Room Architecture**: Independent chat environments with separate configurations
- **Multiple LLM Providers**: OpenAI, Ollama, and compatible APIs
- **Document Ingestion**: Robust pipeline for loading and processing documents
- **Real-time Communication**: WebSocket-based conversation streams
- **OIDC Authentication**: Enterprise SSO with Keycloak integration

## Documentation Updates

This documentation is automatically synchronized from multiple repositories:

- **Core Platform**: [soliplex/soliplex](https://github.com/soliplex/soliplex)
- **Ingester**: [soliplex/ingester](https://github.com/soliplex/ingester)

Documentation is updated automatically when changes are made to the source repositories.

---

**Last Updated**: This site is automatically updated when documentation changes are pushed to the main branch of each repository.
