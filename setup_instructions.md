# Knowledge R Us - RAG Setup Instructions

## Prerequisites

1. **Install Ollama** (for local LLM):
   ```bash
   # macOS
   brew install ollama
   
   # Start Ollama service
   ollama serve
   
   # Pull Llama2 model (in another terminal)
   ollama pull llama2:7b
   ```

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Setup Steps

### 1. Environment Configuration
Create a `.env` file (optional for additional configuration):
```bash
# Optional: Custom model paths
OLLAMA_MODEL=llama2:7b
CHROMA_DB_PATH=./chroma_db
```

### 2. Initialize the System
```bash
# Test the RAG system
python -c "from news_rag_system import get_rag_system; rag = get_rag_system(); print('RAG system initialized successfully!')"
```

### 3. Run the Application

**Option A: RAG-Powered Version (Recommended)**
```bash
streamlit run streamlit_app_rag.py
```

**Option B: Original Static Version**
```bash
streamlit run streamlit_app.py
```

## First Time Usage

1. **Start the RAG app**: `streamlit run streamlit_app_rag.py`
2. **Wait for initialization**: The AI system will initialize (may take 1-2 minutes first time)
3. **Refresh news database**: Click "🔄 Refresh News Database" in sidebar
4. **Select age group**: Choose appropriate age group
5. **Enjoy personalized content**: Articles will be adapted for the selected age group

## Features

### RAG-Powered Features
- ✅ **Real-time news extraction** from RSS feeds
- ✅ **AI content adaptation** for different age groups
- ✅ **Dynamic STEM question generation**
- ✅ **Vector similarity search** for relevant articles
- ✅ **Persistent vector database** with ChromaDB

### News Sources
- Science: NASA, Science Daily, O'Reilly Radar
- Technology: TechCrunch, Wired
- Environment: National Geographic, EPA

## Troubleshooting

### Common Issues

1. **Ollama not running**:
   ```bash
   ollama serve
   ```

2. **Model not found**:
   ```bash
   ollama pull llama2:7b
   ```

3. **ChromaDB permissions**:
   ```bash
   chmod -R 755 ./chroma_db
   ```

4. **News extraction fails**:
   - Check internet connection
   - Some news sites may block automated access
   - Try refreshing the news database

### Performance Tips

1. **First run is slow**: Initial model loading and news fetching takes time
2. **Use caching**: Articles are cached for 1 hour to improve performance
3. **Smaller model**: Use `ollama pull llama2:7b-chat` for faster inference
4. **Limit articles**: Reduce article count in sidebar for faster loading

## Architecture Overview

```
News Sources (RSS) → news-please → ChromaDB → Vector Search
                                      ↓
User Query → Relevant Articles → Ollama LLM → Age-Adapted Content + Questions
```

## Development

### Adding New News Sources
Edit `news_rag_system.py` and add RSS feeds to `self.news_sources`:

```python
self.news_sources = {
    "your_category": [
        "https://example.com/rss.xml"
    ]
}
```

### Customizing Age Adaptation
Modify the prompts in `adapt_content_for_age()` method in `news_rag_system.py`.

### Changing LLM Model
```bash
# Pull different model
ollama pull mistral:7b

# Update in code
llm_model = "mistral:7b"
```
