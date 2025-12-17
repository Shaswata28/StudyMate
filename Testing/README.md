# Testing Directory

This folder contains all test files and verification scripts for the project, organized by component.

## 📁 Structure

```
Testing/
├── ai-brain/              # AI Brain service tests
├── client/                # Frontend tests
│   ├── components/        # Component tests
│   ├── lib/              # Library/utility tests
│   └── pages/            # Page component tests
└── python-backend/        # Backend API tests
```

## 🧪 Test Types

### Unit Tests
Test individual functions, classes, and modules in isolation.

### Integration Tests
Test how different components work together.

### Property-Based Tests
Test universal properties that should hold across all inputs using property-based testing frameworks.

### End-to-End (E2E) Tests
Test complete user workflows from start to finish.

### Verification Scripts
Scripts to verify system setup, configuration, and connectivity.

## 🚀 Running Tests

### Frontend Tests (Client)

```bash
# Run all client tests
pnpm test

# Run specific test file
pnpm test client/components/ChatInput.test.tsx

# Run tests in watch mode
pnpm test --watch

# Run tests with coverage
pnpm test --coverage
```

### Backend Tests (Python)

```bash
# Run all Python tests
cd python-backend
pytest

# Run specific test file
pytest test_auth_endpoints.py

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run specific test category
pytest -k "test_ai_brain"

# Run property-based tests
pytest -k "property"
```

### Verification Scripts

```bash
# Verify AI Brain setup
bash ai-brain/verify_setup.sh

# Verify database setup
python python-backend/verify_database.py

# Verify complete backend setup
python python-backend/verify_complete_setup.py

# Verify AI Brain client
python python-backend/verify_ai_brain_client.py

# Verify configuration
python python-backend/verify_configuration.py

# Verify material processing service
python python-backend/verify_material_processing_service.py
```

## 📂 Test Files by Component

### AI Brain Tests (`ai-brain/`)
- **verify_setup.sh** - Verifies AI Brain service setup and dependencies

### Client Tests (`client/`)

#### Component Tests (`components/`)
- **ChatInput.test.tsx** - Unit tests for ChatInput component
- **ChatInput.browser-compat.test.tsx** - Browser compatibility tests for ChatInput

#### Library Tests (`lib/`)
- **auth.spec.ts** - Authentication library tests
- **registration-flow.e2e.spec.ts** - End-to-end registration flow tests
- **utils.spec.ts** - Utility function tests

#### Page Tests (`pages/`)
- **Dashboard.integration.test.tsx** - Dashboard integration tests
- **Dashboard.backward-compat.test.tsx** - Dashboard backward compatibility tests
- **Questions.test.tsx** - Questions page tests

### Python Backend Tests (`python-backend/`)

#### Authentication & Authorization
- **test_auth_endpoints.py** - Authentication endpoint tests
- **test_registration.py** - User registration tests

#### Academic Features
- **test_academic_endpoints.py** - Academic endpoints tests
- **test_academic_manual.py** - Manual academic feature tests

#### AI & ML Integration
- **test_ai_brain_client.py** - AI Brain client tests
- **test_ai_brain_embedding_property.py** - Property tests for AI Brain embeddings
- **test_ai_brain_ocr_property.py** - Property tests for AI Brain OCR
- **test_ai_provider_config.py** - AI provider configuration tests
- **test_gemini_provider.py** - Gemini provider tests
- **test_gemini_embedding_property.py** - Property tests for Gemini embeddings
- **test_gemini_ocr_property.py** - Property tests for Gemini OCR

#### Material Processing
- **test_material_endpoints.py** - Material endpoints tests
- **test_material_processing_service.py** - Material processing service tests
- **test_material_search.py** - Material search functionality tests
- **test_delete_material.py** - Material deletion tests
- **test_embed_endpoint.py** - Embedding endpoint tests
- **test_embedding_structure.py** - Embedding structure validation tests

#### Context & RAG
- **test_context_integration.py** - Context integration tests
- **test_context_service_academic.py** - Academic context service tests
- **test_context_service_preferences.py** - Preferences context service tests
- **test_format_context_prompt.py** - Context prompt formatting tests
- **test_get_user_context.py** - User context retrieval tests
- **test_rag_integration.py** - RAG (Retrieval-Augmented Generation) integration tests

#### Chat & History
- **test_chat_history.py** - Chat history tests
- **test_background_queue.py** - Background queue processing tests

#### Search
- **test_search_endpoint.py** - Search endpoint tests

#### Preferences
- **test_preferences_endpoints.py** - User preferences endpoint tests

#### Error Handling & Resilience
- **test_graceful_degradation.py** - Graceful degradation tests
- **test_context_timeout.py** - Context timeout handling tests

#### Infrastructure
- **test_connection.py** - Database connection tests

#### Verification Scripts
- **verify_ai_brain_client.py** - Verifies AI Brain client setup
- **verify_complete_setup.py** - Verifies complete backend setup
- **verify_configuration.py** - Verifies configuration settings
- **verify_database.py** - Verifies database setup and connectivity
- **verify_material_processing_service.py** - Verifies material processing service

## 🎯 Test Coverage Goals

- **Unit Tests**: Cover individual functions and methods
- **Integration Tests**: Cover component interactions
- **Property Tests**: Cover universal properties and invariants
- **E2E Tests**: Cover critical user workflows
- **Verification**: Ensure proper system setup

## 🔧 Test Configuration

### Frontend (Vitest)
Configuration in `vite.config.ts`:
- Test framework: Vitest
- Test environment: jsdom (for browser APIs)
- Coverage tool: v8

### Backend (Pytest)
Configuration in `pytest.ini` or `pyproject.toml`:
- Test framework: pytest
- Property testing: hypothesis
- Coverage tool: pytest-cov

## 📝 Writing New Tests

### Frontend Test Template

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MyComponent from './MyComponent';

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });
});
```

### Backend Test Template

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_endpoint():
    response = client.get("/api/endpoint")
    assert response.status_code == 200
    assert response.json()["key"] == "expected_value"
```

### Property-Based Test Template

```python
from hypothesis import given, strategies as st

@given(st.text())
def test_property(input_text):
    result = process_text(input_text)
    # Assert universal property
    assert len(result) >= 0
```

## 🐛 Debugging Tests

### Frontend
```bash
# Run tests in debug mode
pnpm test --inspect-brk

# Run single test file with verbose output
pnpm test ChatInput.test.tsx --reporter=verbose
```

### Backend
```bash
# Run tests with verbose output
pytest -v

# Run tests with print statements
pytest -s

# Run specific test with debugging
pytest test_auth_endpoints.py::test_login -v -s

# Run with pdb debugger on failure
pytest --pdb
```

## 📊 Test Reports

### Generate Coverage Reports

**Frontend:**
```bash
pnpm test --coverage
# Report generated in coverage/
```

**Backend:**
```bash
pytest --cov=. --cov-report=html
# Report generated in htmlcov/
```

## 🔄 Continuous Integration

Tests should be run automatically on:
- Pull requests
- Commits to main branch
- Before deployments

## 📚 Best Practices

1. **Keep tests isolated** - Each test should be independent
2. **Use descriptive names** - Test names should explain what they test
3. **Test edge cases** - Include boundary conditions and error cases
4. **Mock external dependencies** - Use mocks for APIs, databases, etc.
5. **Keep tests fast** - Unit tests should run in milliseconds
6. **Maintain test data** - Use fixtures and factories for test data
7. **Update tests with code** - Keep tests in sync with implementation

## 🆘 Troubleshooting

### Common Issues

**Tests fail locally but pass in CI:**
- Check environment variables
- Verify dependencies are installed
- Check for timing issues

**Tests are slow:**
- Use mocks for external services
- Parallelize test execution
- Optimize database setup/teardown

**Flaky tests:**
- Add proper waits for async operations
- Use deterministic test data
- Avoid time-dependent assertions

## 📖 Additional Resources

- [Vitest Documentation](https://vitest.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Testing Library](https://testing-library.com/)
- [Hypothesis (Property Testing)](https://hypothesis.readthedocs.io/)

---

**Last Updated**: December 2025
