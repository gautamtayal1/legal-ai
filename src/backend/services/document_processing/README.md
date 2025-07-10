# Document Processing Services

This module contains all services for processing legal documents in the RAG pipeline. The services are organized into specialized modules that handle different aspects of document processing.

## 📁 Directory Structure

```
document_processing/
├── __init__.py                 # Main module exports
├── requirements.txt            # Dependencies for all services
├── README.md                  # This documentation
│
├── pipeline/                  # Main orchestration service
│   ├── __init__.py
│   ├── base.py               # Main pipeline orchestrator
│   ├── background_processor.py
│   ├── status_tracker.py
│   ├── error_handler.py
│   ├── job_queue.py
│   └── workflow_manager.py
│
├── text_extraction/          # Text extraction from files
│   ├── __init__.py
│   ├── base.py              # Main extraction service
│   ├── pdf_extractor.py     # PDF text extraction
│   ├── docx_extractor.py    # Word document extraction
│   ├── ocr_extractor.py     # OCR for scanned documents
│   └── text_extractor.py    # Plain text files
│
├── structure_analysis/       # Document structure analysis
│   ├── __init__.py
│   ├── base.py              # Main structure analyzer
│   ├── legal_structure_analyzer.py
│   ├── section_extractor.py
│   └── hierarchy_builder.py
│
├── legal_extraction/         # Legal content extraction
│   ├── __init__.py
│   ├── base.py              # Main legal extractor
│   ├── definitions_extractor.py
│   ├── cross_reference_extractor.py
│   ├── obligations_extractor.py
│   ├── parties_extractor.py
│   └── dates_extractor.py
│
├── chunking/                 # Document chunking services
│   ├── __init__.py
│   ├── base.py              # Main chunking service
│   ├── semantic_chunker.py
│   ├── legal_chunker.py     # Legal-specific chunking
│   ├── overlap_manager.py
│   └── chunk_metadata.py
│
├── embedding/                # Vector embedding generation
│   ├── __init__.py
│   ├── base.py              # Main embedding service
│   ├── openai_embeddings.py
│   ├── huggingface_embeddings.py
│   ├── embedding_cache.py
│   └── batch_processor.py
│
├── vector_store/             # Vector database operations
│   ├── __init__.py
│   ├── base.py              # Main vector store service
│   ├── pinecone_store.py
│   ├── weaviate_store.py
│   ├── chroma_store.py
│   ├── pgvector_store.py
│   └── similarity_search.py
│
├── search_indexing/          # Full-text search indexing
│   ├── __init__.py
│   ├── base.py              # Main search service
│   ├── elasticsearch_indexer.py
│   ├── legal_analyzer.py
│   ├── boolean_search.py
│   ├── hybrid_search.py
│   └── index_manager.py
│
├── config/                   # Configuration management
│   ├── __init__.py
│   ├── base.py
│   ├── embedding_config.py
│   ├── vector_store_config.py
│   ├── search_config.py
│   ├── chunking_config.py
│   └── extraction_config.py
│
└── utils/                    # Shared utilities
    ├── __init__.py
    ├── text_utils.py
    ├── legal_patterns.py
    ├── file_utils.py
    ├── metadata_utils.py
    └── logging_utils.py
```

## 🔄 Processing Pipeline Flow

The document processing follows this sequence:

1. **Text Extraction** (`text_extraction/`)

   - Extract raw text from PDF, DOCX, or other formats
   - Handle OCR for scanned documents
   - Preserve formatting and structure information

2. **Structure Analysis** (`structure_analysis/`)

   - Identify document hierarchy (sections, subsections)
   - Extract headers, footers, and legal patterns
   - Build document structure tree

3. **Legal Content Extraction** (`legal_extraction/`)

   - Extract definitions and defined terms
   - Find cross-references between sections
   - Identify legal obligations and parties
   - Extract dates, deadlines, and amounts

4. **Document Chunking** (`chunking/`)

   - Split document into semantically meaningful chunks
   - Preserve legal context and section boundaries
   - Add metadata for citations and references

5. **Embedding Generation** (`embedding/`)

   - Convert text chunks to vector embeddings
   - Support multiple embedding models (OpenAI, HuggingFace)
   - Batch processing for efficiency

6. **Vector Storage** (`vector_store/`)

   - Store embeddings in vector database
   - Support multiple backends (Pinecone, Weaviate, etc.)
   - Enable similarity search capabilities

7. **Search Indexing** (`search_indexing/`)
   - Index chunks in Elasticsearch for keyword search
   - Configure legal-specific text analysis
   - Enable hybrid search (semantic + keyword)

## 🎯 Key Services

### DocumentProcessingPipeline

Main orchestrator that coordinates all services and manages the processing workflow.

### TextExtractionService

Handles text extraction from various file formats with fallback to OCR for scanned documents.

### LegalContentExtractor

Specialized service for extracting legal-specific content like definitions, obligations, and cross-references.

### LegalChunkingService

Intelligent chunking that preserves legal meaning and maintains proper context for citations.

### VectorStoreService

Manages vector database operations with support for multiple backends and similarity search.

### SearchIndexingService

Handles full-text search indexing with legal-specific analyzers and hybrid search capabilities.

## 🔧 Configuration

Each service has its own configuration module in `config/` that manages:

- API keys and credentials
- Processing parameters (chunk sizes, overlap, etc.)
- Model selection and settings
- Environment-specific configurations

## 📚 Dependencies

See `requirements.txt` for the complete list of dependencies. Key categories include:

- **Text Extraction**: PyPDF2, pdfplumber, python-docx, pytesseract
- **NLP**: spaCy, transformers, sentence-transformers, langchain
- **Vector Databases**: pinecone-client, weaviate-client, chromadb
- **Search**: elasticsearch, opensearch-py
- **Background Jobs**: celery, redis, rq

## 🚀 Usage

```python
from services.document_processing import DocumentProcessingPipeline

# Initialize the pipeline
pipeline = DocumentProcessingPipeline()

# Process a document
result = await pipeline.process_document(
    document_id=123,
    s3_url="https://bucket.s3.amazonaws.com/document.pdf"
)

# Check processing status
status = await pipeline.get_processing_status(document_id=123)
```

## 🧪 Testing

Each service module should include comprehensive tests covering:

- Unit tests for individual components
- Integration tests for service interactions
- End-to-end tests for complete workflows
- Performance tests for large documents

## 📊 Monitoring

The services include built-in monitoring and logging:

- Processing status tracking
- Performance metrics
- Error handling and reporting
- Progress updates for long-running operations

## 🔄 Background Processing

The pipeline supports asynchronous background processing using:

- Celery for distributed task processing
- Redis for message queuing
- Status tracking for real-time updates
- Error handling and retry logic

This architecture ensures scalable, reliable document processing for the legal AI system.
