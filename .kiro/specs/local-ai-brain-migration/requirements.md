# Requirements Document

## Introduction

This document specifies the requirements for migrating from Google Gemini API to a local AI "brain" service. The system will replace cloud-based AI processing with a locally-running FastAPI service that orchestrates multiple specialized AI models (Qwen 2.5 1.5B for text, DeepSeek OCR for vision, Whisper Turbo for audio transcription, and mxbai-embed-large for embeddings). The main Python backend will communicate with this brain service via HTTP requests.

## Glossary

- **AI Brain Service**: A standalone FastAPI application running on port 8001 that provides AI capabilities through local models
- **Main Backend**: The existing FastAPI application (python-backend) that handles business logic and database operations
- **Ollama**: Local model serving infrastructure that hosts and runs the AI models
- **Qwen 2.5 1.5B**: The primary text generation model, kept persistently in memory
- **DeepSeek OCR**: Vision model for optical character recognition and image analysis
- **Whisper Turbo**: Audio transcription model for converting speech to text
- **mxbai-embed-large**: Embedding model for generating vector representations of text
- **VRAM**: Video RAM used by GPU to store models during inference
- **Persistent Core Mode**: Architecture pattern where the primary model stays loaded in memory indefinitely

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want to set up a local AI brain service, so that the application can process AI requests without external API dependencies.

#### Acceptance Criteria

1. WHEN the AI brain service starts THEN the system SHALL load Qwen 2.5 1.5B into memory with keep_alive set to -1
2. WHEN the AI brain service starts THEN the system SHALL load Whisper Turbo model into RAM
3. WHEN the AI brain service starts THEN the system SHALL expose a FastAPI server on port 8001
4. WHEN the AI brain service starts THEN the system SHALL configure CORS to allow requests from any origin
5. WHEN Ollama is not running THEN the system SHALL fail gracefully with a clear error message

### Requirement 2

**User Story:** As a developer, I want the brain service to handle text generation requests, so that users can interact with the AI chatbot.

#### Acceptance Criteria

1. WHEN a POST request is sent to /router with text prompt THEN the system SHALL generate a response using Qwen 2.5 1.5B
2. WHEN generating text responses THEN the system SHALL keep Qwen 2.5 1.5B loaded in memory after completion
3. WHEN a text generation request completes THEN the system SHALL return the response text and model name
4. WHEN a text generation request fails THEN the system SHALL return an HTTP 500 error with error details
5. WHEN multiple text requests arrive THEN the system SHALL process them sequentially using the persistent model

### Requirement 3

**User Story:** As a user, I want to extract text from images, so that I can digitize printed or handwritten materials.

#### Acceptance Criteria

1. WHEN a POST request is sent to /router with an image file THEN the system SHALL load DeepSeek OCR model
2. WHEN processing an image THEN the system SHALL extract text content from the image
3. WHEN image processing completes THEN the system SHALL unload DeepSeek OCR model to free VRAM
4. WHEN image processing completes THEN the system SHALL return extracted text and model name
5. WHEN image processing fails THEN the system SHALL return an error message with model name

### Requirement 4

**User Story:** As a user, I want to transcribe audio recordings, so that I can convert spoken content into text.

#### Acceptance Criteria

1. WHEN a POST request is sent to /router with an audio file THEN the system SHALL save the audio to a temporary file
2. WHEN processing audio THEN the system SHALL use Whisper Turbo to transcribe the content
3. WHEN audio transcription completes THEN the system SHALL use the transcribed text as the prompt for text generation
4. WHEN audio transcription fails THEN the system SHALL log the error and continue with the original prompt
5. WHEN Whisper model is not loaded THEN the system SHALL skip audio processing gracefully

### Requirement 5

**User Story:** As a developer, I want to generate embeddings for text, so that I can implement semantic search and similarity matching.

#### Acceptance Criteria

1. WHEN a POST request is sent to /utility/embed with text THEN the system SHALL load mxbai-embed-large model
2. WHEN generating embeddings THEN the system SHALL set keep_alive to 0 for immediate unloading
3. WHEN embedding generation completes THEN the system SHALL unload the embedding model
4. WHEN embedding generation completes THEN the system SHALL return the embedding vector
5. WHEN embedding generation fails THEN the system SHALL return an HTTP 500 error with error details

### Requirement 6

**User Story:** As a system administrator, I want efficient VRAM management, so that the system can run multiple models without running out of memory.

#### Acceptance Criteria

1. WHEN a specialist model (vision or embedding) completes processing THEN the system SHALL unload that model from VRAM
2. WHEN unloading a model THEN the system SHALL send a keep_alive: 0 request to Ollama
3. WHEN unloading a model THEN the system SHALL clear CUDA cache
4. WHEN unloading a model THEN the system SHALL trigger garbage collection
5. WHILE Qwen 2.5 1.5B is the core model THEN the system SHALL never unload it during cleanup operations

### Requirement 7

**User Story:** As a developer, I want to migrate the main backend from Gemini to the brain service, so that all AI functionality uses local models.

#### Acceptance Criteria

1. WHEN the main backend needs AI responses THEN the system SHALL send HTTP requests to http://localhost:8001
2. WHEN replacing Gemini service THEN the system SHALL maintain the same interface for chat endpoints
3. WHEN sending requests to the brain THEN the system SHALL handle text, image, and audio attachments
4. WHEN the brain service is unavailable THEN the system SHALL return appropriate error responses
5. WHEN migrating is complete THEN the system SHALL remove all Gemini API dependencies

### Requirement 8

**User Story:** As a developer, I want proper error handling and logging, so that I can diagnose issues with the AI brain service.

#### Acceptance Criteria

1. WHEN any operation starts THEN the system SHALL log the operation type and relevant details
2. WHEN any operation completes THEN the system SHALL log the completion time and status
3. WHEN any operation fails THEN the system SHALL log the error with full context
4. WHEN models are loaded or unloaded THEN the system SHALL log the model name and action
5. WHEN the brain service starts THEN the system SHALL log the active configuration and model names

### Requirement 9

**User Story:** As a system administrator, I want installation scripts for the AI brain, so that I can easily set up the required dependencies.

#### Acceptance Criteria

1. WHEN running the installation script THEN the system SHALL install Python dependencies (fastapi, uvicorn, ollama, whisper, torch)
2. WHEN running the installation script THEN the system SHALL pull required Ollama models (qwen2.5:1.5b, deepseek-ocr, mxbai-embed-large)
3. WHEN running the installation script THEN the system SHALL verify Ollama is installed and running
4. WHEN installation completes THEN the system SHALL provide instructions for starting the brain service
5. WHEN installation fails THEN the system SHALL provide clear error messages and troubleshooting steps

### Requirement 10

**User Story:** As a developer, I want the brain service organized in a separate directory, so that it's clearly separated from the main backend.

#### Acceptance Criteria

1. WHEN organizing the project THEN the system SHALL create an ai-brain directory at the project root
2. WHEN organizing the project THEN the system SHALL place the brain service code in ai-brain/brain.py
3. WHEN organizing the project THEN the system SHALL create ai-brain/requirements.txt with all dependencies
4. WHEN organizing the project THEN the system SHALL create ai-brain/README.md with setup and usage instructions
5. WHEN organizing the project THEN the system SHALL create ai-brain/install.sh for automated setup

### Requirement 11

**User Story:** As a developer, I want the brain service to start automatically with the backend, so that I don't need to manage two separate processes.

#### Acceptance Criteria

1. WHEN the main backend starts THEN the system SHALL automatically start the AI brain service as a subprocess
2. WHEN the brain service is starting THEN the system SHALL wait for it to be ready before accepting requests
3. WHEN the main backend shuts down THEN the system SHALL gracefully terminate the brain service subprocess
4. WHEN the brain service fails to start THEN the system SHALL log the error and continue without AI capabilities
5. WHEN the brain service crashes THEN the system SHALL detect the failure and optionally restart it
