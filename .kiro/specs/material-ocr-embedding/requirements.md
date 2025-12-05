# Requirements Document

## Introduction

This feature enables automatic OCR (Optical Character Recognition) and vector embedding generation for uploaded learning materials (PDFs, images). When users upload materials to a course, the system will automatically extract text content, generate semantic embeddings, and store them for intelligent retrieval during AI conversations. This enables Retrieval Augmented Generation (RAG) where the AI can automatically reference relevant material content when answering questions.

The system uses a local AI Brain service that orchestrates specialized models running via Ollama: qwen3-vl:2b for text extraction, mxbai-embed-large for embeddings, and Qwen 2.5 for text generation. This architecture eliminates external API dependencies and provides full control over the AI processing pipeline.

## Glossary

- **System**: The learning platform backend application
- **Material**: A user-uploaded file (PDF, JPG, PNG, GIF, WEBP) associated with a course
- **OCR**: Optical Character Recognition - extracting text from images and PDFs
- **Vector Embedding**: A numerical representation of text that captures semantic meaning
- **RAG**: Retrieval Augmented Generation - using retrieved context to enhance AI responses
- **Semantic Search**: Finding materials based on meaning rather than exact keyword matches
- **Processing Pipeline**: The automated workflow that processes uploaded materials
- **AI Brain Service**: Local FastAPI service that orchestrates specialized AI models via Ollama
- **qwen3-vl:2b**: Vision-language model for extracting text from images and PDFs
- **mxbai-embed-large**: Embedding model for generating semantic vector representations
- **Ollama**: Local model runtime for running AI models
- **Background Job**: Asynchronous task that runs independently of the main request
- **Supabase Storage**: Cloud storage service for storing uploaded files
- **pgvector**: PostgreSQL extension for storing and querying vector embeddings

## Requirements

### Requirement 1

**User Story:** As a student, I want my uploaded materials to be automatically processed and made searchable, so that the AI can reference them when answering my questions.

#### Acceptance Criteria

1. WHEN a user uploads a material file THEN the System SHALL store the file in Supabase Storage and create a database record
2. WHEN a material is uploaded THEN the System SHALL initiate background processing to extract text and generate embeddings
3. WHEN processing begins THEN the System SHALL update the material status to 'processing'
4. WHEN processing completes successfully THEN the System SHALL store extracted text and embeddings in the materials table
5. WHEN processing completes THEN the System SHALL update the material status to 'completed' and record the processed timestamp

### Requirement 2

**User Story:** As a student, I want the system to extract text from my PDF documents and images, so that the content becomes searchable and usable by the AI.

#### Acceptance Criteria

1. WHEN a PDF material is processed THEN the System SHALL extract all text content using OCR capabilities
2. WHEN an image material is processed THEN the System SHALL extract visible text using OCR capabilities
3. WHEN text extraction succeeds THEN the System SHALL store the extracted text in the materials table
4. WHEN text extraction fails THEN the System SHALL update the material status to 'failed' and log the error
5. WHEN a material contains no extractable text THEN the System SHALL store an empty string and mark status as 'completed'

### Requirement 3

**User Story:** As a student, I want my materials to have semantic embeddings, so that the AI can find relevant content based on meaning rather than just keywords.

#### Acceptance Criteria

1. WHEN text is extracted from a material THEN the System SHALL generate a vector embedding representing the semantic meaning
2. WHEN an embedding is generated THEN the System SHALL store it as a VECTOR(1024) in the materials table
3. WHEN embedding generation succeeds THEN the System SHALL ensure the embedding is indexed for fast similarity search
4. WHEN embedding generation fails THEN the System SHALL update the material status to 'failed' and log the error
5. WHEN a material has no text content THEN the System SHALL skip embedding generation and mark status as 'completed'

### Requirement 4

**User Story:** As a student, I want to search my materials by meaning, so that I can quickly find relevant content even if I don't remember exact keywords.

#### Acceptance Criteria

1. WHEN a user submits a semantic search query THEN the System SHALL generate an embedding for the query text
2. WHEN a query embedding is generated THEN the System SHALL perform vector similarity search against material embeddings
3. WHEN similarity search executes THEN the System SHALL return materials ranked by semantic relevance
4. WHEN returning search results THEN the System SHALL include material metadata and relevance scores
5. WHEN a course has no processed materials THEN the System SHALL return an empty result set

### Requirement 5

**User Story:** As a student, I want the AI to automatically reference my uploaded materials when answering questions, so that responses are grounded in my course content.

#### Acceptance Criteria

1. WHEN a user sends a chat message THEN the System SHALL perform semantic search on course materials using the message as query
2. WHEN relevant materials are found THEN the System SHALL retrieve the top 3 most relevant material excerpts
3. WHEN materials are retrieved THEN the System SHALL include them as context in the AI prompt
4. WHEN the AI generates a response THEN the System SHALL ensure the response references the provided material context
5. WHEN no relevant materials are found THEN the System SHALL proceed with the chat request without material context

### Requirement 6

**User Story:** As a student, I want to see the processing status of my uploaded materials, so that I know when they're ready to be used by the AI.

#### Acceptance Criteria

1. WHEN a user views material details THEN the System SHALL display the current processing status
2. WHEN a material is pending processing THEN the System SHALL display status as 'pending'
3. WHEN a material is being processed THEN the System SHALL display status as 'processing'
4. WHEN processing completes successfully THEN the System SHALL display status as 'completed' with timestamp
5. WHEN processing fails THEN the System SHALL display status as 'failed' with error information

### Requirement 7

**User Story:** As a developer, I want the system to communicate with the local AI Brain service, so that OCR and embedding operations use local models without external API dependencies.

#### Acceptance Criteria

1. WHEN implementing OCR services THEN the System SHALL send requests to the AI Brain service /router endpoint
2. WHEN implementing embedding services THEN the System SHALL send requests to the AI Brain service /utility/embed endpoint
3. WHEN the AI Brain service is unavailable THEN the System SHALL update material status to 'failed' with appropriate error message
4. WHEN processing materials THEN the System SHALL verify the AI Brain service is running before initiating processing
5. WHEN the AI Brain service returns an error THEN the System SHALL log the error and mark the material as 'failed'

### Requirement 8

**User Story:** As a system administrator, I want background processing to be reliable and fault-tolerant, so that material processing doesn't fail silently or block user operations.

#### Acceptance Criteria

1. WHEN material processing is initiated THEN the System SHALL execute processing asynchronously without blocking the upload response
2. WHEN processing encounters an error THEN the System SHALL log detailed error information for debugging
3. WHEN processing fails THEN the System SHALL update the material status to 'failed' with error details
4. WHEN processing times out THEN the System SHALL mark the material as 'failed' and allow retry
5. WHEN the system restarts THEN the System SHALL resume processing of materials in 'pending' or 'processing' status

### Requirement 9

**User Story:** As a developer, I want the database schema to efficiently support vector operations, so that semantic search performs well at scale.

#### Acceptance Criteria

1. WHEN the materials table is created THEN the System SHALL include columns for extracted_text, embedding, processing_status, and processed_at
2. WHEN embeddings are stored THEN the System SHALL use the VECTOR(1024) data type for efficient storage
3. WHEN the materials table is indexed THEN the System SHALL create an HNSW index on the embedding column for fast similarity search
4. WHEN querying by status THEN the System SHALL have an index on processing_status for efficient filtering
5. WHEN querying by course THEN the System SHALL maintain the existing index on course_id for efficient lookups

### Requirement 10

**User Story:** As a system administrator, I want the AI Brain service to manage model lifecycle efficiently, so that system resources are optimized during material processing.

#### Acceptance Criteria

1. WHEN the AI Brain service processes OCR requests THEN the System SHALL use qwen3-vl:2b model loaded on demand
2. WHEN the AI Brain service generates embeddings THEN the System SHALL use mxbai-embed-large model loaded on demand
3. WHEN specialist models complete processing THEN the AI Brain service SHALL unload them to free VRAM
4. WHEN the backend starts THEN the System SHALL verify the AI Brain service is accessible at the configured endpoint
5. WHEN material processing requires AI operations THEN the System SHALL handle AI Brain service connection errors gracefully
