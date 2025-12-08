# Testing Index - Quick Reference

## 🎯 Quick Navigation

### By Test Type
- [Unit Tests](#unit-tests)
- [Integration Tests](#integration-tests)
- [Property-Based Tests](#property-based-tests)
- [E2E Tests](#e2e-tests)
- [Verification Scripts](#verification-scripts)

### By Component
- [AI Brain](#ai-brain-tests)
- [Frontend (Client)](#frontend-tests)
- [Backend (Python)](#backend-tests)

---

## Unit Tests

### Frontend
- `client/components/ChatInput.test.tsx`
- `client/lib/auth.spec.ts`
- `client/lib/utils.spec.ts`
- `client/pages/Questions.test.tsx`

### Backend
- `python-backend/test_auth_endpoints.py`
- `python-backend/test_material_endpoints.py`
- `python-backend/test_preferences_endpoints.py`
- `python-backend/test_academic_endpoints.py`
- `python-backend/test_search_endpoint.py`
- `python-backend/test_embed_endpoint.py`

## Integration Tests

### Frontend
- `client/pages/Dashboard.integration.test.tsx`

### Backend
- `python-backend/test_context_integration.py`
- `python-backend/test_rag_integration.py`
- `python-backend/test_material_processing_service.py`

## Property-Based Tests

### AI Brain
- `python-backend/test_ai_brain_ocr_property.py`
- `python-backend/test_ai_brain_embedding_property.py`

### Gemini
- `python-backend/test_gemini_ocr_property.py`
- `python-backend/test_gemini_embedding_property.py`

## E2E Tests

### Frontend
- `client/lib/registration-flow.e2e.spec.ts`

## Verification Scripts

### AI Brain
- `ai-brain/verify_setup.sh`
- `python-backend/verify_ai_brain_client.py`

### Backend Setup
- `python-backend/verify_complete_setup.py`
- `python-backend/verify_configuration.py`
- `python-backend/verify_database.py`
- `python-backend/verify_material_processing_service.py`

---

## AI Brain Tests

| File | Type | Description |
|------|------|-------------|
| `verify_setup.sh` | Verification | Verifies AI Brain service setup |

## Frontend Tests

### Components
| File | Type | Description |
|------|------|-------------|
| `ChatInput.test.tsx` | Unit | ChatInput component tests |
| `ChatInput.browser-compat.test.tsx` | Compatibility | Browser compatibility tests |

### Libraries
| File | Type | Description |
|------|------|-------------|
| `auth.spec.ts` | Unit | Authentication library tests |
| `registration-flow.e2e.spec.ts` | E2E | Registration flow end-to-end tests |
| `utils.spec.ts` | Unit | Utility function tests |

### Pages
| File | Type | Description |
|------|------|-------------|
| `Dashboard.integration.test.tsx` | Integration | Dashboard integration tests |
| `Dashboard.backward-compat.test.tsx` | Compatibility | Backward compatibility tests |
| `Questions.test.tsx` | Unit | Questions page tests |

## Backend Tests

### Authentication (5 files)
- `test_auth_endpoints.py` - Auth endpoint tests
- `test_registration.py` - Registration tests

### Academic (2 files)
- `test_academic_endpoints.py` - Academic endpoint tests
- `test_academic_manual.py` - Manual academic tests

### AI/ML (7 files)
- `test_ai_brain_client.py` - AI Brain client tests
- `test_ai_brain_embedding_property.py` - AI Brain embedding property tests
- `test_ai_brain_ocr_property.py` - AI Brain OCR property tests
- `test_ai_provider_config.py` - AI provider config tests
- `test_gemini_provider.py` - Gemini provider tests
- `test_gemini_embedding_property.py` - Gemini embedding property tests
- `test_gemini_ocr_property.py` - Gemini OCR property tests

### Materials (6 files)
- `test_material_endpoints.py` - Material endpoint tests
- `test_material_processing_service.py` - Material processing tests
- `test_material_search.py` - Material search tests
- `test_delete_material.py` - Material deletion tests
- `test_embed_endpoint.py` - Embedding endpoint tests
- `test_embedding_structure.py` - Embedding structure tests

### Context & RAG (6 files)
- `test_context_integration.py` - Context integration tests
- `test_context_service_academic.py` - Academic context tests
- `test_context_service_preferences.py` - Preferences context tests
- `test_format_context_prompt.py` - Context prompt formatting tests
- `test_get_user_context.py` - User context retrieval tests
- `test_rag_integration.py` - RAG integration tests

### Chat & Queue (2 files)
- `test_chat_history.py` - Chat history tests
- `test_background_queue.py` - Background queue tests

### Other (6 files)
- `test_search_endpoint.py` - Search endpoint tests
- `test_preferences_endpoints.py` - Preferences endpoint tests
- `test_graceful_degradation.py` - Graceful degradation tests
- `test_context_timeout.py` - Context timeout tests
- `test_connection.py` - Connection tests

### Verification (5 files)
- `verify_ai_brain_client.py` - Verify AI Brain client
- `verify_complete_setup.py` - Verify complete setup
- `verify_configuration.py` - Verify configuration
- `verify_database.py` - Verify database
- `verify_material_processing_service.py` - Verify material processing

---

## 🚀 Common Commands

### Run All Tests
```bash
# Frontend
pnpm test

# Backend
cd python-backend && pytest
```

### Run Specific Category
```bash
# Property tests only
pytest -k "property"

# Integration tests only
pytest -k "integration"

# Verification scripts
pytest -k "verify"
```

### Run Single File
```bash
# Frontend
pnpm test ChatInput.test.tsx

# Backend
pytest test_auth_endpoints.py
```

### With Coverage
```bash
# Frontend
pnpm test --coverage

# Backend
pytest --cov=. --cov-report=html
```

---

**Total Test Files**: 45
- AI Brain: 1
- Client: 8
- Python Backend: 36

**See [README.md](./README.md) for detailed documentation**
