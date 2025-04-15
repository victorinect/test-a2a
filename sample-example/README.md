# A2A Echo Examples

resource: https://huggingface.co/blog/lynn-mikami/agent2agent

This project demonstrates implementations of Agent-to-Agent (A2A) API servers and clients. It provides both standard and streaming examples of A2A communication following the Agent Protocol specification.

## Overview

The sample-example project includes:

1. A basic Echo Agent server that responds with non-streaming communication
2. A streaming Echo Agent server that responds with incremental updates
3. Client implementations for both types of agents
4. Common library components for types and communication

## Components

### Echo Server & Client (Non-Streaming)

- **echo_server.py**: Implements a simple A2A server that echoes back user messages.
- **echo_client.py**: Client implementation to communicate with the Echo server.

### Streaming Echo Server & Client

- **streaming_echo_server.py**: Implements an A2A server with streaming support.
- **streaming_echo_client.py**: Client implementation with support for streaming responses.

### Common Library

The `common/` directory contains shared code:
- Type definitions in `types.py`
- Client and server implementation classes

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Required packages (install using pip):
  - asyncio
  - uvicorn
  - fastapi (implied by code structure)

### Running the Echo Server

```bash
python echo_server.py
```

This starts the Echo server on http://localhost:8001/a2a.

### Running the Echo Client

```bash
python echo_client.py
```

This connects to the Echo server and sends a test message.

### Running the Streaming Echo Server

```bash
python streaming_echo_server.py
```

This starts the Streaming Echo server on http://localhost:8002/a2a.

### Running the Streaming Echo Client

```bash
python streaming_echo_client.py
```

This connects to the Streaming Echo server and processes streamed responses.

## API Examples

### Non-Streaming Interaction

The Echo Agent:
1. Receives a message via JSON-RPC `tasks/send` method
2. Processes the message synchronously
3. Returns a complete response with the user's message echoed back

### Streaming Interaction

The Streaming Echo Agent:
1. Receives a message via JSON-RPC `tasks/sendSubscribe` method
2. Streams back status updates via Server-Sent Events (SSE)
3. Shows intermediate "thinking" state
4. Delivers the final response with the user's message echoed back

## Project Structure

```
sample-example/
├── echo_server.py          # Non-streaming server
├── echo_client.py          # Non-streaming client
├── streaming_echo_server.py # Streaming server
├── streaming_echo_client.py # Streaming client
├── common/                 # Shared code
│   ├── client/             # Client implementations
│   ├── server/             # Server implementations
│   └── types.py            # Data type definitions
└── README.md               # This documentation
```

## Implementation Details

Both implementations use:
- JSON-RPC for request/response communication
- Server-Sent Events (SSE) for streaming
- Async/await patterns
- Task state management
- Agent capability declarations
