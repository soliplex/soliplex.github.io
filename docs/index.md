# Soliplex Documentation

Welcome to the Soliplex ecosystem documentation. Soliplex provides AI-powered retrieval-augmented generation capabilities for intelligent document search and question answering.

## Core Components

### [Soliplex Platform](soliplex/overview.md)

The main Soliplex RAG system with FastAPI backend and Flutter frontend.

**Quick Links:**
- [Overview](soliplex/overview.md)
- [Server Setup](soliplex/server.md)
- [Client Setup](soliplex/client.md)
- [RAG Database](soliplex/rag.md)
- [Configuration Guide](soliplex/config/installation.md)
- [Usage](soliplex/usage.md)

### [Ingester](ingester/GETTING_STARTED.md)

Robust document ingestion system for loading content into RAG databases.

**Quick Links:**
- [Getting Started](ingester/GETTING_STARTED.md)
- [Architecture](ingester/ARCHITECTURE.md)
- [API Reference](ingester/API.md)
- [CLI Reference](ingester/CLI.md)
- [Configuration](ingester/CONFIGURATION.md)
- [Database Schema](ingester/DATABASE.md)
- [Workflows](ingester/WORKFLOWS.md)

## User Interfaces

### Flutter Client

Cross-platform mobile and desktop client application for Soliplex.

**Quick Links:**
- [Developer Setup Guide](flutter/guides/developer-setup.md)
- [Flutter Development Rules](flutter/rules/flutter_rules.md)
- [Client Summary](flutter/summary/client.md)

### [Chatbot Widget](chatbot/readme.md)

Embeddable Next.js chat widget for integrating Soliplex into web applications.

**Quick Links:**
- [Documentation](chatbot/readme.md)
- [Usage Guide](chatbot/usage.md)

## Supporting Tools

### [Ingester Agents](ingester-agents/index.md)

Agents for ingesting documents from various sources (filesystem, GitHub, Gitea) into the Soliplex Ingester.

**Quick Links:**
- [Documentation](ingester-agents/index.md)

### [PDF Splitter](pdf-splitter/index.md)

Utility for splitting and processing PDF documents for ingestion.

**Quick Links:**
- [Documentation](pdf-splitter/index.md)

## Getting Started

### For New Users

1. [Core Platform Overview](soliplex/overview.md) - Understanding the Soliplex system
2. [Server Setup](soliplex/server.md) - Set up the backend server
3. [Client Setup](soliplex/client.md) - Configure the client application
4. [Getting Started with Ingester](ingester/GETTING_STARTED.md) - Document ingestion basics

### For Developers

1. [Core Platform Architecture](soliplex/overview.md) - System design and components
2. [Ingester Architecture](ingester/ARCHITECTURE.md) - Ingestion pipeline design
3. [API References](ingester/API.md) - REST API documentation

### For Operations

1. [Configuration Guide](soliplex/config/installation.md) - Installation configuration
2. [Environment Setup](soliplex/config/environment.md) - Environment variables
3. [Secrets Management](soliplex/config/secrets.md) - Handling sensitive configuration
4. [Ingester CLI Reference](ingester/CLI.md) - Command-line tool usage

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
- **Flutter Client**: [soliplex/flutter](https://github.com/soliplex/flutter)
- **Chatbot Widget**: [soliplex/chatbot](https://github.com/soliplex/chatbot)
- **Ingester Agents**: [soliplex/ingester-agents](https://github.com/soliplex/ingester-agents)
- **PDF Splitter**: [soliplex/pdf-splitter](https://github.com/soliplex/pdf-splitter)

Documentation is updated automatically when changes are made to the source repositories via git submodules.





