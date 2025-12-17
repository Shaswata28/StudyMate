# Router Implementation Checklist

## 📋 Complete Implementation Checklist

---

## ✅ Phase 1: Backend Changes (COMPLETE)

- [x] Create `intent_classifier.py` service
- [x] Add `/classify` endpoint to `brain.py`
- [x] Add `/chat` endpoint to `brain.py`
- [x] Update `context_service.py` with `build_adaptive_context()`
- [x] Update `local_ai_service.py` with `generate_chat_response()`
- [x] Refactor `chat.py` router to use intent classification
- [x] Create `test_router_integration.py`
- [x] Create deployment documentation
- [x] Create summary documentation

---

## 🎯 Phase 2: Model Training (YOUR TASK)

### Step 1: Prepare Dataset
- [ ] Navigate to `Dataset/dataset_router/`
- [ ] Run `bash combine_datasets.sh` (or manually combine)
- [ ] Upload `combined_router.jsonl` to Colab
- [ ] Verify dataset format (ChatML messages)

### Step 2: Fine-tune in Colab
- [ ] Install Unsloth: `pip install unsloth`
- [ ] Load Gemma 3 270M base model
- [ ] Configure training parameters:
  ```python
  max_seq_length = 1024  # Short for classification
  learning_rate = 2e-4
  num_train_epochs = 3
  per_device_train_batch_size = 4
  ```
- [ ] Train model on `combined_router.jsonl`
- [ ] Evaluate on test set (target: >90% accuracy)
- [ ] Export as GGUF format (q4_k_m quantization)

### Step 3: Download Model
- [ ] Download GGUF file from Colab
- [ ] Save as `studymate-router-q4_k_m.gguf`
- [ ] Verify file size (~270MB)

---

## 🚀 Phase 3: Deployment (AFTER TRAINING)

### Step 1: Create Modelfile
- [ ] Create `Modelfile.router` (template in deployment guide)
- [ ] Set correct template for Gemma 3
- [ ] Configure parameters (temp=0.1, top_p=0.9)
- [ ] Add system prompt

### Step 2: Import to Ollama
- [ ] Run: `ollama create studymate-router -f Modelfile.router`
- [ ] Verify: `ollama list | grep studymate-router`
- [ ] Test: `ollama run studymate-router "test query"`

### Step 3: Start Services
- [ ] Terminal 1: `cd ai-brain && python brain.py`
- [ ] Terminal 2: `cd python-backend && uvicorn main:app --reload`
- [ ] Check logs for router model loading
- [ ] Verify no errors

---

## 🧪 Phase 4: Testing

### Basic Tests
- [ ] Run: `python test_router_integration.py`
- [ ] Test classification endpoint:
  ```bash
  curl -X POST http://localhost:8001/classify \
    -F "query=Hello!" \
    -F "subject=General" \
    -F "grade=Bachelor"
  ```
- [ ] Verify response format
- [ ] Check classification speed (<40ms)

### Intent Tests
- [ ] Test chitchat: "Hello, how are you?"
  - Expected: `{"intent": "chat", "needs_rag": false}`
- [ ] Test academic: "Explain photosynthesis"
  - Expected: `{"intent": "academic", "needs_rag": true}`
- [ ] Test follow-up: "Why did you say that?"
  - Expected: `{"intent": "followup", "needs_history": true}`
- [ ] Test debug: "Fix this code error"
  - Expected: `{"intent": "debug", "needs_history": true}`
- [ ] Test safety: "How to hack a website"
  - Expected: `{"intent": "safety", "needs_rag": false}`

### Integration Tests
- [ ] Test full chat flow with chitchat query
- [ ] Test full chat flow with academic query
- [ ] Verify RAG search is skipped for chitchat
- [ ] Verify RAG search runs for academic
- [ ] Check response quality (no regression)

### Performance Tests
- [ ] Measure classification latency
- [ ] Measure end-to-end latency (chitchat)
- [ ] Measure end-to-end latency (academic)
- [ ] Verify token savings in logs
- [ ] Compare with baseline (before router)

---

## 📊 Phase 5: Monitoring

### Metrics to Track
- [ ] Classification accuracy by intent
- [ ] Average classification latency
- [ ] Token savings percentage
- [ ] Response time improvements
- [ ] RAG search reduction percentage
- [ ] Safety query blocking rate

### Logs to Monitor
- [ ] Intent distribution (what users ask)
- [ ] Classification confidence scores
- [ ] Fallback frequency (classification failures)
- [ ] Error rates
- [ ] User feedback

---

## 🔧 Phase 6: Optimization (Optional)

### If Classification Accuracy < 90%
- [ ] Review misclassified examples
- [ ] Add more training data for weak categories
- [ ] Adjust training hyperparameters
- [ ] Retrain model
- [ ] Re-evaluate

### If Performance Not Improved
- [ ] Check if router model is loaded in VRAM
- [ ] Verify RAG searches are actually skipped
- [ ] Profile bottlenecks
- [ ] Optimize context building
- [ ] Consider smaller quantization

### If Response Quality Degraded
- [ ] Review ChatML format
- [ ] Check system prompt construction
- [ ] Verify history is included when needed
- [ ] Test with more examples
- [ ] Adjust context building logic

---

## 🎯 Success Criteria

### Must Have
- [x] Backend changes implemented
- [ ] Router model trained (>90% accuracy)
- [ ] Model deployed to Ollama
- [ ] All tests passing
- [ ] No errors in logs
- [ ] Response quality maintained

### Should Have
- [ ] Chitchat queries 30% faster
- [ ] Token usage reduced 60-90% for simple queries
- [ ] RAG searches reduced by 50%
- [ ] Safety queries blocked automatically
- [ ] Classification latency <40ms

### Nice to Have
- [ ] Monitoring dashboard
- [ ] A/B testing framework
- [ ] Automated retraining pipeline
- [ ] User feedback collection
- [ ] Performance analytics

---

## 📝 Documentation Checklist

- [x] `ROUTER_IMPLEMENTATION_PLAN.md` - Complete technical guide
- [x] `ROUTER_QUICK_SUMMARY.md` - Executive summary
- [x] `ROUTER_DEPLOYMENT_GUIDE.md` - Deployment instructions
- [x] `BACKEND_CHANGES_SUMMARY.md` - What was changed
- [x] `ROUTER_CHECKLIST.md` - This file
- [x] `test_router_integration.py` - Testing script
- [x] Code comments in all modified files

---

## 🚨 Troubleshooting

### Issue: Router model not found
**Solution**: 
```bash
ollama list
ollama create studymate-router -f Modelfile.router
```

### Issue: Classification returns wrong intent
**Solution**: 
- Check training data quality
- Verify model fine-tuning
- Test with more examples
- Consider retraining

### Issue: Backend errors
**Solution**:
```bash
tail -f python-backend/logs/app.log
# Check for connection errors, model loading issues
```

### Issue: Performance not improved
**Solution**:
- Verify RAG searches are skipped
- Check classification latency
- Monitor token usage in logs
- Profile with `test_router_integration.py`

---

## 📞 Next Steps

1. **NOW**: Fine-tune router model in Colab
2. **THEN**: Deploy model following deployment guide
3. **AFTER**: Run tests and verify everything works
4. **FINALLY**: Monitor performance and iterate

---

## 🎉 When Complete

You'll have:
- ✅ Smart intent classification (Gemma 3 270M)
- ✅ Adaptive context selection
- ✅ 60-90% token savings for simple queries
- ✅ 30% faster responses for chitchat
- ✅ Automatic safety filtering
- ✅ ChatML format (fixes hallucinations)
- ✅ Better user experience

---

**Current Status**: Backend ready, waiting for model training
**Next Action**: Fine-tune Gemma 3 270M in Colab
**Estimated Time**: 2-3 hours (training + deployment)
