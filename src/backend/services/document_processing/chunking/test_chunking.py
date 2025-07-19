
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from chunking_service import DocumentChunkingService
from base import ChunkConfig, ChunkingStrategy
from overlap_manager import OverlapConfig


async def test_chunking_service():
    sample_legal_text = """
    ARTICLE 1: DEFINITIONS
    
    1.1 "Agreement" means this Software License Agreement.
    1.2 "Company" means ABC Corporation, a Delaware corporation.
    1.3 "Software" means the computer program and related documentation.
    
    ARTICLE 2: GRANT OF LICENSE
    
    2.1 Subject to the terms and conditions of this Agreement, Company hereby grants
    to Licensee a non-exclusive, non-transferable license to use the Software.
    
    2.2 Licensee shall not distribute, sell, or transfer the Software to any third party
    without the prior written consent of Company.
    
    ARTICLE 3: OBLIGATIONS
    
    3.1 Licensee shall comply with all applicable laws and regulations.
    3.2 Licensee shall maintain the confidentiality of the Software.
    3.3 Company shall provide reasonable technical support for the Software.
    
    ARTICLE 4: TERM AND TERMINATION
    
    4.1 This Agreement shall commence on the Effective Date and shall continue
    for a period of three (3) years, unless terminated earlier in accordance
    with the provisions hereof.
    
    4.2 Either party may terminate this Agreement upon thirty (30) days written notice.
    """
    
    print("Testing Legal AI Chunking Service")
    print("=" * 50)
    
    chunk_config = ChunkConfig(
        chunk_size=500,
        chunk_overlap=100,
        strategy=ChunkingStrategy.LEGAL,
        preserve_legal_structure=True
    )
    
    overlap_config = OverlapConfig(
        overlap_size=100,
        overlap_strategy="sentence_aware"
    )
    
    try:
        chunking_service = DocumentChunkingService(
            chunk_config=chunk_config,
            overlap_config=overlap_config
        )
        
        document = {
            "id": "test_legal_doc_001",
            "content": sample_legal_text,
            "metadata": {
                "document_type": "legal_agreement",
                "source": "test_data"
            }
        }
        
        print("1. Testing Legal Document Chunking...")
        chunks = await chunking_service.chunk_document(document)
        
        print(f"   Created {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            print(f"\n   Chunk {i+1}:")
            print(f"   - ID: {chunk.id}")
            print(f"   - Type: {chunk.metadata.get('chunk_type', 'unknown')}")
            print(f"   - Method: {chunk.metadata.get('chunking_method', 'unknown')}")
            print(f"   - Length: {len(chunk.content)} characters")
            print(f"   - Section: {chunk.parent_section}")
            print(f"   - Content preview: {chunk.content[:100]}...")
            
            if chunk.legal_context:
                print(f"   - Legal context: {chunk.legal_context}")
        
        print("\n2. Testing Statistics...")
        stats = chunking_service.get_chunk_statistics(chunks)
        print(f"   Statistics: {stats}")
        
        print("\n3. Testing Semantic Chunking...")
        semantic_chunks = await chunking_service.chunk_text(
            sample_legal_text,
            "test_semantic_doc_001",
            strategy=ChunkingStrategy.SEMANTIC
        )
        
        print(f"   Created {len(semantic_chunks)} semantic chunks")
        
        semantic_stats = chunking_service.get_chunk_statistics(semantic_chunks)
        print(f"   Semantic stats: {semantic_stats}")
        
        print("\n4. Testing Multiple Documents...")
        documents = [
            {
                "id": "doc_1",
                "content": sample_legal_text[:500],
                "metadata": {"type": "fragment"}
            },
            {
                "id": "doc_2", 
                "content": sample_legal_text[500:],
                "metadata": {"type": "fragment"}
            }
        ]
        
        multi_results = await chunking_service.chunk_multiple_documents(documents)
        print(f"   Processed {len(multi_results)} documents")
        
        for doc_id, doc_chunks in multi_results.items():
            print(f"   - {doc_id}: {len(doc_chunks)} chunks")
        
        print("\n5. Testing Configuration Optimization...")
        optimized_config = chunking_service.optimize_chunking_config(
            sample_legal_text, 
            target_chunk_count=6
        )
        
        print(f"   Optimized config: {optimized_config}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_chunking_service())