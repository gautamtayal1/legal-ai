# Legal AI - Inquire

A sophisticated AI-powered legal document analysis and chat platform built with modern web technologies. This application enables users to upload legal documents and engage in intelligent conversations with an AI assistant that can analyze, interpret, and answer questions about the uploaded content.

## <� Architecture Overview

### Frontend
- **Framework**: Next.js 15.3.5 with React 19.0.0
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 4 with custom dark theme
- **Authentication**: Clerk
- **HTTP Client**: Axios
- **Package Manager**: pnpm

### Backend
- **Framework**: FastAPI with Python 3.11
- **Database**: PostgreSQL 15 with SQLAlchemy ORM
- **Search Engine**: Elasticsearch 8.16.1
- **Vector Database**: ChromaDB
- **AI/ML**: OpenAI GPT models, LangChain
- **File Storage**: AWS S3
- **Document Processing**: Custom pipeline with multiple processors

### Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Reverse Proxy**: Nginx with security headers and rate limiting
- **Database Migrations**: Alembic
- **Deployment**: Docker Compose

## =� Features

### Document Processing
- **Multi-format Support**: PDF, DOCX, DOC, TXT files up to 10MB
- **Intelligent Chunking**: Legal-specific text segmentation
- **Vector Embeddings**: Semantic search capabilities
- **Hybrid Search**: Combines vector similarity and keyword matching
- **Real-time Status**: Live processing status updates

### AI Chat Interface
- **Streaming Responses**: Real-time AI responses via Server-Sent Events
- **Context Awareness**: Maintains conversation history
- **Document-Aware**: AI has access to all uploaded documents in a thread
- **Rich Formatting**: Markdown support in responses

### Legal-Specific Features
- **Multi-Round Retrieval**: Advanced question-answering with context
- **Definition Resolution**: Legal term clarification
- **Obligation Analysis**: Contract and legal document analysis
- **Auto-naming**: Intelligent thread naming based on document content

### User Experience
- **Thread Management**: Organize conversations by topic
- **Responsive Design**: Mobile-friendly interface
- **Dark Theme**: Professional legal-focused design
- **Real-time Updates**: Live document processing status

## =� Project Structure

```
legal-ai/
   docker-compose.yml          # Multi-service orchestration
   nginx/                      # Reverse proxy configuration
      Dockerfile
      nginx.conf
   src/
      backend/               # FastAPI backend service
         Dockerfile
         main.py           # Application entry point
         requirements.txt  # Python dependencies
         alembic/          # Database migrations
         api/routers/      # API endpoints
            documents.py  # Document management
            threads.py    # Thread operations
            messages.py   # Message handling
            query.py      # AI chat endpoints
            clerk_webhooks.py # Authentication webhooks
         models/           # SQLAlchemy models
         services/         # Business logic
            document_processing/ # Document pipeline
         utils/            # Utilities
      frontend/             # Next.js frontend application
          Dockerfile
          package.json
          next.config.ts    # Next.js configuration
          app/              # App router structure
              components/   # React components
              hooks/        # Custom React hooks
              globals.css   # Global styles
   README.md
```

## =' API Endpoints

### Documents API (`/api/documents`)
- `GET /documents/` - List user documents
- `POST /documents/upload` - Upload new document
- `GET /documents/{doc_id}/status` - Get processing status
- `GET /documents/thread/{thread_id}` - Get thread documents

### Threads API (`/api/threads`)
- `GET /threads/{user_id}` - List user threads
- `POST /threads` - Create new thread
- `DELETE /threads/{thread_id}` - Delete thread
- `POST /threads/{thread_id}/auto-name` - Auto-generate thread name

### Messages API (`/api/messages`)
- `POST /messages/` - Create message
- `GET /messages/thread/{thread_id}` - Get thread messages

### Query API (`/api/query`)
- `POST /query/stream` - Stream AI responses
- `PUT /query/config` - Update search configuration

### Webhooks (`/webhooks`)
- `POST /webhooks` - Clerk authentication webhooks

## =� Setup and Installation

### Prerequisites
- Docker and Docker Compose
- Git
- Environment variables (see below)

### Environment Variables

Create a `.env` file in the root directory:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://yourdomain.com/api

# Authentication (Clerk)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_your_key
CLERK_SECRET_KEY=sk_live_your_key

# OpenAI
OPENAI_API_KEY=sk-your_openai_key

# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name

# Database
POSTGRES_USER=inquire_user
POSTGRES_PASSWORD=inquire_pass
POSTGRES_DB=inquire_db
POSTGRES_PORT=5432

# Elasticsearch
ELASTICSEARCH_VERSION=8.16.1
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_TRANSPORT_PORT=9300
ES_JAVA_OPTS=-Xms1g -Xmx1g

# ChromaDB
CHROMADB_VERSION=latest
CHROMADB_PORT=8080

# Additional Services
ADMINER_PORT=8081
```

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd legal-ai
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost
   - API Documentation: http://localhost/api/docs
   - Database Admin: http://localhost:8081

### Development Setup

For local development without Docker:

1. **Backend Setup**
   ```bash
   cd src/backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd src/frontend
   pnpm install
   pnpm dev
   ```

## = Security Features

- **Authentication**: Clerk-based user management with webhook integration
- **CORS Protection**: Configurable origins with credential support
- **Rate Limiting**: API endpoint protection (10 req/s general, 5 req/s auth)
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, CSP
- **Input Validation**: File type and size restrictions
- **Non-root Containers**: All Docker containers run as non-root users

## =� Monitoring and Health Checks

- **Health Endpoints**: Built-in health checks for all services
- **Service Dependencies**: Proper startup order with health checks
- **Logging**: Structured logging throughout the application
- **Error Handling**: Comprehensive error handling and user feedback

## =� Deployment

### Production Deployment

1. **Environment Configuration**
   - Set `NEXT_PUBLIC_API_URL` to your production domain
   - Configure all required environment variables
   - Ensure S3 bucket and AWS credentials are properly set

2. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

3. **SSL/HTTPS Setup**
   - Configure your reverse proxy (Cloudflare, nginx, etc.)
   - Update CORS origins for production domain
   - Set proper security headers

### Scaling Considerations

- **Database**: Consider managed PostgreSQL for production
- **File Storage**: S3 with CloudFront for global distribution
- **Search**: Elasticsearch cluster for high availability
- **Caching**: Redis for session and response caching
- **Load Balancing**: Multiple frontend/backend instances

## =' Configuration

### Document Processing Pipeline
- **Chunking**: Configurable chunk sizes and overlap
- **Embeddings**: OpenAI text-embedding-ada-002
- **Search**: Hybrid vector + keyword search with configurable weights
- **Processing**: Asynchronous background processing

### AI Configuration
- **Model**: OpenAI GPT-3.5-turbo for chat, GPT-4 for complex analysis
- **Context**: Retrieval-augmented generation (RAG) with document context
- **Streaming**: Real-time response streaming via SSE

## =� Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## =� License

This project is licensed under the MIT License - see the LICENSE file for details.

## <� Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/api/docs`
- Review the troubleshooting section below

## = Troubleshooting

### Common Issues

1. **Build Failures**
   - Ensure all environment variables are set
   - Check Docker daemon is running
   - Verify port availability (80, 5432, 9200, 8080)

2. **Authentication Issues**
   - Verify Clerk keys are correct
   - Check webhook URLs in Clerk dashboard
   - Ensure CORS origins are properly configured

3. **Document Processing Issues**
   - Verify S3 credentials and bucket access
   - Check Elasticsearch and ChromaDB connectivity
   - Monitor processing logs for errors

4. **Performance Issues**
   - Increase Elasticsearch heap size via ES_JAVA_OPTS
   - Consider database connection pooling
   - Monitor resource usage and scale accordingly# Legal AI - Last updated: Sat Jul 19 13:52:49 IST 2025
