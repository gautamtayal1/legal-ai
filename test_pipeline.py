import asyncio
import os
from src.backend.services.document_pipeline import DocumentPipeline
from src.backend.services.document_processing.chunking.base import ChunkingStrategy

async def test_pipeline():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    pipeline = DocumentPipeline(openai_api_key=api_key)
    
    sample_doc = {
        "id": "test_contract_001",
        "content": """
        AGREEMENT FOR LEGAL SERVICES
        
        This Agreement is made between Client and Attorney. The parties agree to the following terms:
        
        1. SCOPE OF SERVICES
        Attorney shall provide legal representation in matters relating to contract law, including but not limited to contract review, negotiation, and drafting.
        
        2. FEES AND PAYMENT
        Client agrees to pay Attorney at the rate of $300 per hour for all services rendered. Payment is due within 30 days of invoice date.
        
        3. CONFIDENTIALITY
        Attorney agrees to maintain the confidentiality of all information provided by Client, except as required by law or court order.
        
        4. TERMINATION
        Either party may terminate this agreement with 30 days written notice.
        """,
        "metadata": {
            "document_type": "legal_agreement",
            "practice_area": "contract_law",
            "date_created": "2024-01-15"
        }
    }
    
    print("Processing document...")
    result = await pipeline.process_document(sample_doc, strategy=ChunkingStrategy.LEGAL)
    print(f"Processing result: {result}")
    
    if result.get("success"):
        print(f"Successfully processed {result['chunks_processed']} chunks")
        
        print("\nTesting search...")
        search_results = await pipeline.search_documents(
            query="confidentiality agreement",
            n_results=3
        )
        
        print(f"Found {len(search_results)} results:")
        for i, result in enumerate(search_results):
            print(f"\nResult {i+1}:")
            print(f"Similarity: {result['similarity']:.3f}")
            print(f"Content: {result['content'][:100]}...")
            print(f"Metadata: {result['metadata']}")
    
    print(f"\nPipeline stats: {pipeline.get_pipeline_stats()}")
    
    print(f"Documents in storage: {pipeline.list_documents()}")

if __name__ == "__main__":
    asyncio.run(test_pipeline())