# Hugging Face Dataset Integration Guide

## Overview

The chatbot now fetches its FAQ data from the **MakTek/Customer_support_faqs_dataset** on Hugging Face, which contains **200 comprehensive customer support Q&A pairs**. The old `maktek_qa.json` file has been removed.

## What Changed

### 1. **New Module: `src/rag/huggingface_loader.py`**
   - `HuggingFaceDatasetLoader` class: Handles loading from Hugging Face with smart caching
   - `load_faqs_from_huggingface()` function: Convenience wrapper
   - Features:
     - **Intelligent caching**: Caches data locally in `data/.hf_cache/faqs.json` for faster subsequent loads
     - **Fallback support**: Falls back to local file if HF is unreachable
     - **No internet required**: After first download, uses local cache

### 2. **Updated: `src/rag/vector_store.py`**
   - Modified `load_documents()` to use `HuggingFaceDatasetLoader`
   - Attempts HF load first, falls back to cache/local file
   - Now loads **200 FAQs** instead of the previous 29

### 3. **Updated: `src/rag/__init__.py`**
   - Exports `HuggingFaceDatasetLoader` and `load_faqs_from_huggingface`

### 4. **Deleted: `data/maktek_qa.json`**
   - Old FAQ file removed (replaced by HF dataset)
   - Local cache now stored in: `data/.hf_cache/faqs.json`

## Dependencies

```bash
# Install datasets library (already installed in your environment)
pip install datasets
```

## Usage Examples

### Basic Usage: Load FAQs
```python
from src.rag.huggingface_loader import load_faqs_from_huggingface

# Load 200 FAQs (uses cache if available)
docs = load_faqs_from_huggingface(
    use_cache=True,
    prefer_cache=True,
    fallback_path="data/.hf_cache/faqs.json"
)

print(f"Loaded {len(docs)} documents")
# Output: Loaded 200 documents
```

### Advanced Usage: Configure Loader
```python
from src.rag.huggingface_loader import HuggingFaceDatasetLoader

loader = HuggingFaceDatasetLoader(
    use_cache=True,                    # Cache to local file
    fallback_path="data/.hf_cache/faqs.json"
)

# Load with cache preference (faster)
data = loader.load(prefer_cache=True)

# Force re-download from HF (skip cache)
data = loader.load(prefer_cache=False)

# Load from cache only
data = loader.load_from_cache()
```

### Vector Store Integration
```python
from src.rag.vector_store import get_vector_store_manager

# Vector store automatically uses HF dataset via the loader
manager = get_vector_store_manager()
manager.initialize_vector_store()

# Search in all 200 FAQs
results = manager.similarity_search_with_score("How does shipping work?", k=5)
```

## Dataset Information

### Source
- **URL**: https://huggingface.co/datasets/MakTek/Customer_support_faqs_dataset
- **Size**: 200 FAQ pairs
- **Format**: JSON (question, answer)
- **License**: Apache 2.0

### Sample Questions Covered
- Account management (create, reset password, update info)
- Payment methods and pricing
- Order tracking and management
- Shipping and delivery
- Returns and refunds
- Product availability (pre-order, backorder, etc.)
- Warranties and guarantees
- Customer support channels

### Caching

**First Load** (from Hugging Face):
```
Loading dataset from Hugging Face: MakTek/Customer_support_faqs_dataset...
✓ Cached 200 FAQs to data/.hf_cache/faqs.json
✓ Loaded 200 FAQs from Hugging Face
```

**Subsequent Loads** (from cache, ~instant):
```
✓ Loaded 200 FAQs from cache
```

**Cache Details**:
- Location: `data/.hf_cache/faqs.json`
- Size: ~48 KB
- Created: On first load
- Auto-updated: When `prefer_cache=False`

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **FAQ Count** | 29 local FAQs | 200 curated FAQs |
| **Data Source** | Local JSON file | Hugging Face dataset |
| **Caching** | None | Intelligent local caching |
| **Updates** | Manual file edits | HF dataset versioning |
| **Maintenance** | Manual sync | Automatic with HF |
| **Scalability** | Limited | 200 FAQs + easy to add more |

## Troubleshooting

### Issue: "Warning: 'datasets' library not found"
**Solution**: Install it with:
```bash
pip install datasets
```

### Issue: "Could not connect to Hugging Face"
**Solution**: The system automatically falls back to cache. If cache doesn't exist:
1. Ensure internet connection
2. First load will download and cache
3. Subsequent loads use cache (no internet needed)

### Issue: Want to refresh data from HF
**Solution**: Delete cache and reload:
```bash
rm data/.hf_cache/faqs.json
```
Then next load will fetch fresh data from Hugging Face.

## Technical Details

### Load Priority (in `load()` method)
1. **Cache** (if `prefer_cache=True`) - Fastest
2. **Hugging Face** - Downloads 200 FAQs if not cached
3. **Fallback** - Local file if HF unavailable
4. **Empty** - Returns empty list if all fail

### Data Structure
Each FAQ entry:
```json
{
  "question": "How can I create an account?",
  "answer": "To create an account, click on the 'Sign Up' button..."
}
```

Converted to LangChain Document:
```python
Document(
    page_content="Question: How can I create an account?\n\nAnswer: To create an account...",
    metadata={
        "source": "huggingface_customer_support_faqs",
        "question": "How can I create an account?",
        "answer": "To create an account...",
        "doc_id": "0"
    }
)
```

## Integration with Chatbot

The vector store and retriever agents automatically use the 200 FAQs:

```
User Query
    ↓
[Input Guardrail] (abuse detection)
    ↓
[Supervisor Agent] (routes to retriever)
    ↓
[Retriever Agent] → [Vector Store] ← [200 HF FAQs (cached)]
    ↓
[Generator Agent] (creates response)
    ↓
Chatbot Response with FAQ-backed answer
```

## Next Steps

1. **Restart API Server** (if running) to use new 200 FAQs:
   ```bash
   pkill -f "python api.py"
   python api.py
   ```

2. **Test Chat**: Ask questions like:
   - "How long does shipping take?"
   - "What's your return policy?"
   - "Can I change my order?"

3. **Monitor Retrieval**: The system will now search across 200 FAQs instead of 29

---

**Status**: ✅ Successfully integrated HF dataset with 200 FAQs and intelligent caching
