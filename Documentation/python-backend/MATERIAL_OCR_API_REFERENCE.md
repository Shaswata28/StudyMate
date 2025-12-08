# Material OCR & Embedding - API Reference

Complete API reference for material upload, processing, search, and RAG endpoints.

## Base URL

```
http://localhost:8000/api
```

## Authentication

All endpoints require JWT authentication via Bearer token:

```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## Endpoints

### 1. Upload Material

Upload a file to a course and queue it for OCR and embedding processing.

**Endpoint**: `POST /api/courses/{course_id}/materials`

**Authentication**: Required

**Path Parameters**:
- `course_id` (string, required): UUID of the course

**Request Body**:
- Content-Type: `multipart/form-data`
- `file` (file, required): File to upload

**Supported File Types**:
- `application/pdf`
- `image/jpeg`
- `image/png`
- `image/gif`
- `image/webp`

**File Size Limit**: 10MB (configurable)

**Response**: `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "course_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "lecture-notes.pdf",
  "file_path": "user_id/course_id/lecture-notes.pdf",
  "file_type": "application/pdf",
  "file_size": 1024000,
  "processing_status": "pending",
  "processed_at": null,
  "error_message": null,
  "has_embedding": false,
  "created_at": "2024-01-01T00:00:00.000Z",
  "updated_at": "2024-01-01T00:00:00.000Z"
}
```

**Processing Status Values**:
- `pending`: Uploaded, waiting for background processing
- `processing`: Currently extracting text and generating embedding
- `completed`: Successfully processed with text and embedding
- `failed`: Processing failed (see error_message)

**Error Responses**:

`400 Bad Request`:
```json
{
  "detail": "File type image/bmp not allowed"
}
```

`404 Not Found`:
```json
{
  "detail": "Course not found"
}
```

`500 Internal Server Error`:
```json
{
  "detail": "Failed to upload material: Connection timeout"
}
```

**Example**:

```bash
curl -X POST "http://localhost:8000/api/courses/550e8400-e29b-41d4-a716-446655440001/materials" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "file=@/path/to/document.pdf"
```

**Python Example**:

```python
import requests

url = "http://localhost:8000/api/courses/{course_id}/materials"
headers = {"Authorization": f"Bearer {token}"}
files = {"file": open("document.pdf", "rb")}

response = requests.post(url, headers=headers, files=files)
material = response.json()
print(f"Uploaded: {material['id']}, Status: {material['processing_status']}")
```

**JavaScript Example**:

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch(`/api/courses/${courseId}/materials`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const material = await response.json();
console.log(`Uploaded: ${material.id}, Status: ${material.processing_status}`);
```

---

### 2. List Materials

Get all materials for a course with their processing status.

**Endpoint**: `GET /api/courses/{course_id}/materials`

**Authentication**: Required

**Path Parameters**:
- `course_id` (string, required): UUID of the course

**Response**: `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "course_id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "lecture-notes.pdf",
    "file_path": "user_id/course_id/lecture-notes.pdf",
    "file_type": "application/pdf",
    "file_size": 2048000,
    "processing_status": "completed",
    "processed_at": "2024-01-01T00:05:00.000Z",
    "error_message": null,
    "has_embedding": true,
    "created_at": "2024-01-01T00:00:00.000Z",
    "updated_at": "2024-01-01T00:05:00.000Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "course_id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "textbook-chapter.pdf",
    "file_path": "user_id/course_id/textbook-chapter.pdf",
    "file_type": "application/pdf",
    "file_size": 5120000,
    "processing_status": "processing",
    "processed_at": null,
    "error_message": null,
    "has_embedding": false,
    "created_at": "2024-01-01T00:10:00.000Z",
    "updated_at": "2024-01-01T00:10:30.000Z"
  }
]
```

**Sorting**: Results are sorted by `created_at` in descending order (newest first)

**Error Responses**:

`404 Not Found`:
```json
{
  "detail": "Course not found"
}
```

**Example**:

```bash
curl -X GET "http://localhost:8000/api/courses/550e8400-e29b-41d4-a716-446655440001/materials" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### 3. Get Material Details

Get metadata for a specific material including processing status.

**Endpoint**: `GET /api/materials/{material_id}`

**Authentication**: Required

**Path Parameters**:
- `material_id` (string, required): UUID of the material

**Response**: `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "course_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "textbook-chapter.pdf",
  "file_path": "user_id/course_id/textbook-chapter.pdf",
  "file_type": "application/pdf",
  "file_size": 5120000,
  "processing_status": "completed",
  "processed_at": "2024-01-01T00:10:00.000Z",
  "error_message": null,
  "has_embedding": true,
  "created_at": "2024-01-01T00:00:00.000Z",
  "updated_at": "2024-01-01T00:10:00.000Z"
}
```

**Error Responses**:

`404 Not Found`:
```json
{
  "detail": "Material not found"
}
```

**Example**:

```bash
curl -X GET "http://localhost:8000/api/materials/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Use Case**: Poll this endpoint to monitor processing status after upload

```python
import time
import requests

def wait_for_processing(material_id, token, timeout=300):
    """Wait for material processing to complete"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(
            f"http://localhost:8000/api/materials/{material_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        material = response.json()
        status = material["processing_status"]
        
        if status == "completed":
            return material
        elif status == "failed":
            raise Exception(f"Processing failed: {material['error_message']}")
        
        time.sleep(5)  # Check every 5 seconds
    
    raise TimeoutError("Processing timeout")
```

---

### 4. Semantic Search

Search materials by semantic meaning using vector similarity.

**Endpoint**: `GET /api/courses/{course_id}/materials/search`

**Authentication**: Required

**Path Parameters**:
- `course_id` (string, required): UUID of the course

**Query Parameters**:
- `query` (string, required): Search query text (1-500 characters)
- `limit` (integer, optional): Maximum results to return (1-10, default: 3)

**Response**: `200 OK`

```json
[
  {
    "material_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "lecture-notes.pdf",
    "excerpt": "This chapter covers the fundamentals of machine learning, including supervised and unsupervised learning algorithms. We explore decision trees, neural networks, and support vector machines...",
    "similarity_score": 0.87,
    "file_type": "application/pdf"
  },
  {
    "material_id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "textbook-chapter.pdf",
    "excerpt": "Neural networks are computational models inspired by biological neural networks. They consist of interconnected nodes organized in layers that process information...",
    "similarity_score": 0.82,
    "file_type": "application/pdf"
  },
  {
    "material_id": "550e8400-e29b-41d4-a716-446655440003",
    "name": "research-paper.pdf",
    "excerpt": "Deep learning has revolutionized computer vision and natural language processing. Convolutional neural networks excel at image recognition tasks...",
    "similarity_score": 0.78,
    "file_type": "application/pdf"
  }
]
```

**Response Fields**:
- `material_id`: UUID of the material
- `name`: Original filename
- `excerpt`: First 500 characters of extracted text
- `similarity_score`: Cosine similarity score (0-1, higher is more relevant)
- `file_type`: MIME type of the file

**Sorting**: Results are sorted by similarity score in descending order (most relevant first)

**Empty Results**: Returns empty array `[]` if no materials match or no materials are processed

**Error Responses**:

`400 Bad Request`:
```json
{
  "detail": "Query parameter cannot be empty"
}
```

`404 Not Found`:
```json
{
  "detail": "Course not found"
}
```

`500 Internal Server Error`:
```json
{
  "detail": "Failed to search materials: AI Brain service unavailable"
}
```

**Example**:

```bash
curl -X GET "http://localhost:8000/api/courses/550e8400-e29b-41d4-a716-446655440001/materials/search?query=machine%20learning%20basics&limit=3" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Python Example**:

```python
import requests

url = "http://localhost:8000/api/courses/{course_id}/materials/search"
headers = {"Authorization": f"Bearer {token}"}
params = {
    "query": "What is gradient descent?",
    "limit": 3
}

response = requests.get(url, headers=headers, params=params)
results = response.json()

for result in results:
    print(f"{result['name']} (Score: {result['similarity_score']:.2f})")
    print(f"Excerpt: {result['excerpt'][:200]}...\n")
```

**JavaScript Example**:

```javascript
const query = encodeURIComponent("neural networks");
const response = await fetch(
  `/api/courses/${courseId}/materials/search?query=${query}&limit=3`,
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);

const results = await response.json();
results.forEach(result => {
  console.log(`${result.name} (Score: ${result.similarity_score.toFixed(2)})`);
});
```

---

### 5. Chat with RAG

Send a chat message with automatic retrieval of relevant course materials.

**Endpoint**: `POST /api/courses/{course_id}/chat`

**Authentication**: Required

**Path Parameters**:
- `course_id` (string, required): UUID of the course

**Request Body**:

```json
{
  "message": "What are the key concepts in machine learning?",
  "history": [
    {
      "role": "user",
      "content": "Hello"
    },
    {
      "role": "model",
      "content": "Hi! How can I help you with your course today?"
    }
  ],
  "attachments": []
}
```

**Request Fields**:
- `message` (string, required): User's chat message
- `history` (array, optional): Previous conversation messages
- `attachments` (array, optional): File attachments (currently unused)

**Response**: `201 Created`

```json
{
  "response": "Based on your course materials, the key concepts in machine learning include:\n\n1. **Supervised Learning**: Training models on labeled data to make predictions. This includes algorithms like decision trees, neural networks, and support vector machines.\n\n2. **Unsupervised Learning**: Finding patterns in unlabeled data through clustering and dimensionality reduction.\n\n3. **Neural Networks**: Computational models inspired by biological neural networks, consisting of interconnected nodes that process information in layers.\n\nYour lecture notes mention that deep learning has revolutionized computer vision and natural language processing, with convolutional neural networks excelling at image recognition tasks.",
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

**How RAG Works**:
1. System performs semantic search using the message as query
2. Retrieves top 3 most relevant material excerpts
3. Augments the AI prompt with material context
4. AI generates response grounded in course materials
5. Conversation is saved to chat_history table

**Material Context Format**:
```
--- RELEVANT COURSE MATERIALS ---

[Material 1: lecture-notes.pdf]
This chapter covers the fundamentals of machine learning...
(Relevance: 0.87)

[Material 2: textbook-chapter.pdf]
Neural networks are computational models inspired by...
(Relevance: 0.82)

--- END OF COURSE MATERIALS ---

Based on the course materials above, please answer the following question:

What are the key concepts in machine learning?
```

**Error Responses**:

`404 Not Found`:
```json
{
  "detail": "Course not found"
}
```

`503 Service Unavailable`:
```json
{
  "error": "AI Brain service not available",
  "code": "LOCAL_AI_API_ERROR"
}
```

`500 Internal Server Error`:
```json
{
  "error": "Something went wrong. Please try again.",
  "code": "INTERNAL_ERROR"
}
```

**Example**:

```bash
curl -X POST "http://localhost:8000/api/courses/550e8400-e29b-41d4-a716-446655440001/chat" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain backpropagation",
    "history": [],
    "attachments": []
  }'
```

**Python Example**:

```python
import requests

url = "http://localhost:8000/api/courses/{course_id}/chat"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
data = {
    "message": "What is supervised learning?",
    "history": [],
    "attachments": []
}

response = requests.post(url, headers=headers, json=data)
chat_response = response.json()
print(f"AI: {chat_response['response']}")
```

**JavaScript Example**:

```javascript
const response = await fetch(`/api/courses/${courseId}/chat`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: "Explain neural networks",
    history: conversationHistory,
    attachments: []
  })
});

const data = await response.json();
console.log(`AI: ${data.response}`);
```

---

### 6. Download Material

Download the original uploaded file.

**Endpoint**: `GET /api/materials/{material_id}/download`

**Authentication**: Required

**Path Parameters**:
- `material_id` (string, required): UUID of the material

**Response**: `200 OK` (file stream)

**Headers**:
- `Content-Type`: Original file MIME type
- `Content-Disposition`: `attachment; filename="original-filename.pdf"`

**Error Responses**:

`404 Not Found`:
```json
{
  "detail": "Material not found"
}
```

**Example**:

```bash
curl -X GET "http://localhost:8000/api/materials/550e8400-e29b-41d4-a716-446655440000/download" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -o downloaded-file.pdf
```

**Python Example**:

```python
import requests

url = f"http://localhost:8000/api/materials/{material_id}/download"
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(url, headers=headers)

with open("downloaded-file.pdf", "wb") as f:
    f.write(response.content)
```

---

### 7. Delete Material

Delete a material and its file from storage.

**Endpoint**: `DELETE /api/materials/{material_id}`

**Authentication**: Required

**Path Parameters**:
- `material_id` (string, required): UUID of the material

**Response**: `200 OK`

```json
{
  "message": "Material deleted successfully"
}
```

**Error Responses**:

`404 Not Found`:
```json
{
  "detail": "Material not found"
}
```

**Example**:

```bash
curl -X DELETE "http://localhost:8000/api/materials/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### 8. Get Chat History

Get all chat messages for a course.

**Endpoint**: `GET /api/courses/{course_id}/chat`

**Authentication**: Required

**Path Parameters**:
- `course_id` (string, required): UUID of the course

**Response**: `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "course_id": "550e8400-e29b-41d4-a716-446655440001",
    "history": [
      {
        "role": "user",
        "content": "What is machine learning?"
      },
      {
        "role": "model",
        "content": "Machine learning is a subset of artificial intelligence..."
      }
    ],
    "created_at": "2024-01-01T00:00:00.000Z"
  }
]
```

**Sorting**: Results are sorted by `created_at` in ascending order (chronological)

**Error Responses**:

`404 Not Found`:
```json
{
  "detail": "Course not found"
}
```

**Example**:

```bash
curl -X GET "http://localhost:8000/api/courses/550e8400-e29b-41d4-a716-446655440001/chat" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Rate Limiting

Chat endpoints are rate limited:
- **Default**: 10 requests per 60 seconds per IP
- **Configurable**: Set `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW` in `.env`

**Rate Limit Response**: `429 Too Many Requests`

```json
{
  "detail": "Rate limit exceeded"
}
```

---

## Error Codes

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 400 | - | Invalid request (bad parameters, file type, etc.) |
| 404 | - | Resource not found (course, material) |
| 429 | - | Rate limit exceeded |
| 500 | INTERNAL_ERROR | Unexpected server error |
| 500 | SERVICE_ERROR | AI service error |
| 503 | LOCAL_AI_API_ERROR | AI Brain service unavailable |
| 503 | TIMEOUT_ERROR | AI Brain service timeout |

---

## Data Models

### MaterialResponse

```typescript
interface MaterialResponse {
  id: string;                    // UUID
  course_id: string;              // UUID
  name: string;                   // Original filename
  file_path: string;              // Storage path
  file_type: string;              // MIME type
  file_size: number;              // Bytes
  processing_status: "pending" | "processing" | "completed" | "failed";
  processed_at: string | null;   // ISO 8601 timestamp
  error_message: string | null;  // Error details if failed
  has_embedding: boolean;         // Whether embedding exists
  created_at: string;             // ISO 8601 timestamp
  updated_at: string;             // ISO 8601 timestamp
}
```

### MaterialSearchResult

```typescript
interface MaterialSearchResult {
  material_id: string;            // UUID
  name: string;                   // Original filename
  excerpt: string;                // First 500 chars of text
  similarity_score: number;       // 0-1, higher is more relevant
  file_type: string;              // MIME type
}
```

### ChatRequest

```typescript
interface ChatRequest {
  message: string;                // User message
  history: Message[];             // Conversation history
  attachments: any[];             // File attachments (optional)
}

interface Message {
  role: "user" | "model";
  content: string;
}
```

### ChatResponse

```typescript
interface ChatResponse {
  response: string;               // AI response
  timestamp: string;              // ISO 8601 timestamp
}
```

---

## Best Practices

### 1. Polling for Processing Status

```python
import time

def wait_for_completion(material_id, token, max_wait=300):
    """Poll until processing completes or times out"""
    start = time.time()
    while time.time() - start < max_wait:
        response = requests.get(
            f"/api/materials/{material_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        material = response.json()
        
        if material["processing_status"] == "completed":
            return material
        elif material["processing_status"] == "failed":
            raise Exception(material["error_message"])
        
        time.sleep(5)
    
    raise TimeoutError("Processing timeout")
```

### 2. Error Handling

```python
try:
    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()
    material = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 400:
        print(f"Invalid request: {e.response.json()['detail']}")
    elif e.response.status_code == 404:
        print("Course not found")
    elif e.response.status_code == 503:
        print("AI service unavailable, try again later")
    else:
        print(f"Error: {e}")
```

### 3. Batch Upload

```python
import asyncio
import aiohttp

async def upload_materials(course_id, files, token):
    """Upload multiple files concurrently"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for file_path in files:
            task = upload_single_file(session, course_id, file_path, token)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results

async def upload_single_file(session, course_id, file_path, token):
    url = f"http://localhost:8000/api/courses/{course_id}/materials"
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(file_path, "rb") as f:
        data = aiohttp.FormData()
        data.add_field('file', f, filename=file_path)
        
        async with session.post(url, headers=headers, data=data) as response:
            return await response.json()
```

### 4. Search with Fallback

```python
def search_with_fallback(course_id, query, token):
    """Search with fallback to empty results"""
    try:
        response = requests.get(
            f"/api/courses/{course_id}/materials/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"query": query, "limit": 3}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError:
        # Return empty results on error
        return []
```

---

## Testing

### cURL Examples

```bash
# Upload
curl -X POST "http://localhost:8000/api/courses/{COURSE_ID}/materials" \
  -H "Authorization: Bearer {TOKEN}" \
  -F "file=@test.pdf"

# List
curl -X GET "http://localhost:8000/api/courses/{COURSE_ID}/materials" \
  -H "Authorization: Bearer {TOKEN}"

# Get details
curl -X GET "http://localhost:8000/api/materials/{MATERIAL_ID}" \
  -H "Authorization: Bearer {TOKEN}"

# Search
curl -X GET "http://localhost:8000/api/courses/{COURSE_ID}/materials/search?query=test&limit=3" \
  -H "Authorization: Bearer {TOKEN}"

# Chat
curl -X POST "http://localhost:8000/api/courses/{COURSE_ID}/chat" \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"message":"test","history":[],"attachments":[]}'

# Download
curl -X GET "http://localhost:8000/api/materials/{MATERIAL_ID}/download" \
  -H "Authorization: Bearer {TOKEN}" \
  -o file.pdf

# Delete
curl -X DELETE "http://localhost:8000/api/materials/{MATERIAL_ID}" \
  -H "Authorization: Bearer {TOKEN}"
```

---

## Additional Resources

- **Complete Guide**: `MATERIAL_OCR_EMBEDDING_GUIDE.md`
- **Quick Start**: `MATERIAL_OCR_QUICKSTART.md`
- **Design Document**: `.kiro/specs/material-ocr-embedding/design.md`
- **Requirements**: `.kiro/specs/material-ocr-embedding/requirements.md`

---

*Last Updated: December 2024*
