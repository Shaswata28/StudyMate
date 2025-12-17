# Gemini Embedding API Quota Guide

## Issue: Quota Exceeded for Embeddings

If you're seeing this error:
```
429 You exceeded your current quota, please check your plan and billing details.
* Quota exceeded for metric: generativelanguage.googleapis.com/embed_content_free_tier_requests
```

This means your Gemini API free tier quota for embeddings has been exhausted.

## Understanding Gemini API Quotas

Google Gemini API has **separate quotas** for different operations:
- **Text Generation** (chat, OCR): Higher free tier limits
- **Embeddings** (vector generation): Lower free tier limits or may be set to 0

Even though you use the same API key, embeddings have much stricter limits on the free tier.

## Solutions

### Option 1: Wait for Quota Reset (Free Tier)
Free tier quotas reset daily (Pacific Time). Wait 24 hours and try again.

**Check your quota usage:**
- Visit: https://ai.dev/usage?tab=rate-limit
- Sign in with your Google account
- View your current usage and limits

### Option 2: Upgrade to Paid Tier (Recommended)
The paid tier provides much higher limits for embeddings:
- Visit: https://ai.google.dev/pricing
- Enable billing on your Google Cloud project
- Embeddings are very affordable (typically $0.00001 per 1K characters)

### Option 3: Use a Separate API Key for Embeddings
If you have access to multiple Google Cloud projects or API keys:

1. Create a new API key from a different project
2. Add it to your `.env` file:
   ```bash
   GEMINI_API_KEY=your_main_api_key_here
   GEMINI_EMBEDDING_API_KEY=your_separate_embedding_key_here
   ```
3. The system will automatically use the separate key for embeddings

### Option 4: Reduce Test Iterations (Development)
For development and testing, reduce the number of property test iterations:

In `test_gemini_embedding_property.py`, change:
```python
@settings(
    max_examples=100,  # Reduce this to 10 or 20 for testing
    deadline=60000,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
```

## Checking Your Quota

### Via Google AI Studio
1. Visit: https://aistudio.google.com/
2. Sign in with your Google account
3. Click on "Get API key" in the left sidebar
4. View your quota usage and limits

### Via API Response
The error message includes detailed quota information:
```
violations {
  quota_metric: "generativelanguage.googleapis.com/embed_content_free_tier_requests"
  quota_id: "EmbedContentRequestsPerDayPerProjectPerModel-FreeTier"
}
```

This tells you which specific quota was exceeded.

## Best Practices

### For Development
1. **Use mock providers** for most testing (see `test_embedding_structure.py`)
2. **Reduce test iterations** to minimize API calls
3. **Cache embeddings** during development to avoid regenerating
4. **Use separate API keys** for development and production

### For Production
1. **Enable billing** to get higher quotas
2. **Implement rate limiting** to prevent quota exhaustion
3. **Monitor usage** regularly via Google Cloud Console
4. **Set up alerts** for quota usage thresholds
5. **Consider caching** frequently used embeddings

## Configuration Reference

### Environment Variables
```bash
# Main API key (required)
GEMINI_API_KEY=your_api_key_here

# Optional: Separate key for embeddings
GEMINI_EMBEDDING_API_KEY=your_embedding_key_here

# Embedding model (default: models/embedding-001)
GEMINI_EMBEDDING_MODEL=models/embedding-001

# Processing timeout (default: 300 seconds)
MATERIAL_PROCESSING_TIMEOUT=300
```

### Code Configuration
The system automatically uses the separate embedding key if configured:
```python
from services.ai_provider_factory import get_ai_provider

provider = get_ai_provider()
# Will use GEMINI_EMBEDDING_API_KEY for embeddings if set
# Otherwise falls back to GEMINI_API_KEY
```

## Testing Without API Calls

Use the mock provider for testing logic without API calls:
```bash
python test_embedding_structure.py
```

This validates the test structure without consuming API quota.

## Links

- **Gemini API Pricing**: https://ai.google.dev/pricing
- **Quota Management**: https://ai.dev/usage
- **API Documentation**: https://ai.google.dev/gemini-api/docs
- **Get API Key**: https://makersuite.google.com/app/apikey
- **Google Cloud Console**: https://console.cloud.google.com/

## Support

If you continue to experience quota issues:
1. Check your Google Cloud billing status
2. Verify your API key is valid and active
3. Review your project's quota limits in Google Cloud Console
4. Consider requesting a quota increase for your project
