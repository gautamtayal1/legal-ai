"""
LLM answer generation service for legal document queries.
Implements Step 14 from architecture: LLM Answer Generation
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain.schema import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from .hybrid_retriever import SearchResult
from .query_processor import ProcessedQuery


@dataclass
class GeneratedAnswer:
    """Represents a generated answer with metadata."""
    answer: str
    confidence: float
    citations: List[Dict[str, Any]]
    sources_used: int
    query_intent: str
    processing_time: float
    warnings: List[str]


class AnswerGenerator:
    """
    Generates comprehensive, cited legal answers using LLM.
    Uses LangChain for prompt engineering and response generation.
    """
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.1):
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=2000
        )
        
        # Initialize output parser
        self.output_parser = StrOutputParser()
        
        # Legal answer prompt template
        self.legal_prompt = PromptTemplate(
            input_variables=["query", "context", "intent", "confidence"],
            template="""
You are a legal AI assistant specializing in contract analysis and legal document interpretation. 
Your task is to provide comprehensive, accurate answers based ONLY on the provided context.

CRITICAL INSTRUCTIONS:
1. Base your answer ONLY on the provided context - do not add external legal knowledge
2. Cite every factual claim using [cite_N] format where N is the citation number
3. If information is incomplete or missing, clearly state this limitation
4. Structure your answer with clear sections and bullet points where appropriate
5. Use precise legal language while remaining accessible
6. Indicate confidence levels for different aspects of your answer

USER QUERY: {query}
QUERY INTENT: {intent}
QUERY CONFIDENCE: {confidence}

CONTEXT FROM LEGAL DOCUMENTS:
{context}

RESPONSE FORMAT:
## Summary
[Brief 2-3 sentence summary with key findings]

## Detailed Analysis
[Comprehensive analysis with citations]

## Key Points
- [Important point 1] [cite_N]
- [Important point 2] [cite_N]
- [Additional points as needed]

## Limitations & Caveats
[Any limitations in the available information or analysis]

## Confidence Assessment
- High confidence: [Aspects you're confident about]
- Medium confidence: [Aspects with some uncertainty]
- Low confidence: [Aspects requiring additional information]

Remember: Every factual claim must have a citation [cite_N]. If you cannot find relevant information in the context, explicitly state this rather than providing general legal knowledge.
"""
        )
        
        # Definition-specific prompt
        self.definition_prompt = PromptTemplate(
            input_variables=["query", "context", "term"],
            template="""
You are a legal AI assistant specializing in contract definitions and legal terminology.
Provide a precise definition based ONLY on the provided context.

USER QUERY: {query}
TERM TO DEFINE: {term}

CONTEXT FROM LEGAL DOCUMENTS:
{context}

RESPONSE FORMAT:
## Definition
[Precise definition with citation]

## Usage Context
[How the term is used in the document with examples]

## Related Terms
[Any related defined terms mentioned in the context]

## Source Location
[Where in the document this definition appears]

Cite every statement using [cite_N] format. If no definition is found, clearly state this.
"""
        )
        
        # Create chains
        self.legal_chain = self.legal_prompt | self.llm | self.output_parser
        self.definition_chain = self.definition_prompt | self.llm | self.output_parser

    async def generate_answer(self, 
                            query: str,
                            search_results: List[SearchResult],
                            processed_query: ProcessedQuery) -> GeneratedAnswer:
        """
        Generate a comprehensive legal answer from search results.
        
        Args:
            query: The original user query
            search_results: Results from hybrid search
            processed_query: Processed query with intent and analysis
            
        Returns:
            GeneratedAnswer object with complete response
        """
        try:
            import time
            start_time = time.time()
            
            # Prepare context from search results
            context, citations = self._prepare_context(search_results)
            
            # Generate warnings
            warnings = self._generate_warnings(search_results, processed_query)
            
            # Choose appropriate chain based on query intent
            if processed_query.intent.value == "definition":
                # Extract term to define
                term = self._extract_definition_term(query, processed_query)
                
                answer = await self.definition_chain.ainvoke({
                    "query": query,
                    "context": context,
                    "term": term
                })
            else:
                # Use general legal chain
                answer = await self.legal_chain.invoke({
                    "query": query,
                    "context": context,
                    "intent": processed_query.intent.value,
                    "confidence": processed_query.confidence
                })
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Calculate confidence based on results quality
            confidence = self._calculate_answer_confidence(
                search_results, processed_query, answer
            )
            
            generated_answer = GeneratedAnswer(
                answer=answer,
                confidence=confidence,
                citations=citations,
                sources_used=len(search_results),
                query_intent=processed_query.intent.value,
                processing_time=processing_time,
                warnings=warnings
            )
            
            self.logger.info(f"Generated answer for query: {query}, "
                           f"confidence: {confidence:.2f}, "
                           f"sources: {len(search_results)}")
            
            return generated_answer
            
        except Exception as e:
            self.logger.error(f"Answer generation failed: {str(e)}")
            
            # Return error response
            return GeneratedAnswer(
                answer="I apologize, but I encountered an error while processing your query. Please try again.",
                confidence=0.0,
                citations=[],
                sources_used=0,
                query_intent=processed_query.intent.value,
                processing_time=0.0,
                warnings=["Error occurred during answer generation"]
            )

    def _prepare_context(self, search_results: List[SearchResult]) -> tuple[str, List[Dict[str, Any]]]:
        """
        Prepare context string and citations from search results.
        
        Args:
            search_results: List of search results
            
        Returns:
            Tuple of (context_string, citations_list)
        """
        context_parts = []
        citations = []
        
        for i, result in enumerate(search_results):
            cite_num = i + 1
            
            # Add to context
            context_part = f"[cite_{cite_num}] {result.content}"
            if result.metadata.get("parent_section"):
                context_part += f" (Section: {result.metadata['parent_section']})"
            
            context_parts.append(context_part)
            
            # Add to citations
            citation = {
                "citation_number": cite_num,
                "chunk_id": result.chunk_id,
                "document_id": result.document_id,
                "content": result.content,
                "score": result.score,
                "source": result.source,
                "metadata": result.metadata,
                "highlights": result.highlights
            }
            citations.append(citation)
        
        context_string = "\n\n".join(context_parts)
        return context_string, citations

    def _generate_warnings(self, 
                         search_results: List[SearchResult], 
                         processed_query: ProcessedQuery) -> List[str]:
        """Generate warnings about result quality or limitations."""
        warnings = []
        
        # Check for low confidence in query processing
        if processed_query.confidence < 0.7:
            warnings.append("Query interpretation confidence is low - results may not be optimal")
        
        # Check for few results
        if len(search_results) < 3:
            warnings.append("Limited relevant content found - answer may be incomplete")
        
        # Check for low-scoring results
        if search_results and max(r.score for r in search_results) < 0.5:
            warnings.append("Search results have low relevance scores - verify answer accuracy")
        
        # Check for mixed document sources
        doc_ids = set(r.document_id for r in search_results)
        if len(doc_ids) > 1:
            warnings.append(f"Answer draws from {len(doc_ids)} different documents")
        
        return warnings

    def _extract_definition_term(self, query: str, processed_query: ProcessedQuery) -> str:
        """Extract the term to be defined from the query."""
        # Look for quoted terms first
        import re
        quoted_terms = re.findall(r'"([^"]*)"', query)
        if quoted_terms:
            return quoted_terms[0]
        
        # Look for "define X" or "what is X" patterns
        define_patterns = [
            r'define\s+(.+?)(?:\s+in|$)',
            r'what\s+is\s+(.+?)(?:\s+in|$)',
            r'meaning\s+of\s+(.+?)(?:\s+in|$)'
        ]
        
        for pattern in define_patterns:
            matches = re.findall(pattern, query.lower())
            if matches:
                return matches[0].strip()
        
        # Fallback to legal concepts if found
        if processed_query.legal_concepts:
            return processed_query.legal_concepts[0]
        
        # Last resort - extract entities
        if processed_query.entities:
            return processed_query.entities[0]
        
        return "unknown term"

    def _calculate_answer_confidence(self, 
                                   search_results: List[SearchResult],
                                   processed_query: ProcessedQuery,
                                   answer: str) -> float:
        """Calculate confidence score for the generated answer."""
        confidence = 0.5  # Base confidence
        
        # Boost based on search result quality
        if search_results:
            avg_score = sum(r.score for r in search_results) / len(search_results)
            confidence += min(0.3, avg_score)
        
        # Boost based on query processing confidence
        confidence += processed_query.confidence * 0.2
        
        # Boost based on number of quality sources
        quality_sources = len([r for r in search_results if r.score > 0.5])
        confidence += min(0.2, quality_sources * 0.05)
        
        # Reduce if answer is very short (likely incomplete)
        if len(answer) < 100:
            confidence -= 0.1
        
        # Reduce if no citations found in answer
        import re
        citation_count = len(re.findall(r'\[cite_\d+\]', answer))
        if citation_count == 0:
            confidence -= 0.2
        
        return min(1.0, max(0.0, confidence))

    async def generate_follow_up_questions(self, 
                                         query: str,
                                         generated_answer: GeneratedAnswer) -> List[str]:
        """
        Generate relevant follow-up questions based on the answer.
        
        Args:
            query: Original query
            generated_answer: Generated answer object
            
        Returns:
            List of follow-up questions
        """
        try:
            followup_prompt = PromptTemplate(
                input_variables=["query", "answer", "intent"],
                template="""
Based on the user's query and the generated answer, suggest 3-5 relevant follow-up questions that would help the user better understand the legal implications or get more specific information.

Original Query: {query}
Query Intent: {intent}
Generated Answer: {answer}

Generate follow-up questions that are:
1. Specific to the legal content discussed
2. Practical and actionable
3. Build upon the information provided
4. Help clarify potential ambiguities

Format as a simple list:
1. [Question 1]
2. [Question 2]
3. [Question 3]
4. [Question 4]
5. [Question 5]
"""
            )
            
            followup_chain = followup_prompt | self.llm | self.output_parser
            
            followup_response = await followup_chain.ainvoke({
                "query": query,
                "answer": generated_answer.answer,
                "intent": generated_answer.query_intent
            })
            
            # Parse questions from response
            questions = []
            for line in followup_response.split('\n'):
                if line.strip() and (line.strip().startswith(tuple('123456789')) or line.strip().startswith('-')):
                    # Remove numbering and clean up
                    question = line.strip()
                    question = question.lstrip('0123456789.-) ').strip()
                    if question:
                        questions.append(question)
            
            return questions[:5]  # Limit to 5 questions
            
        except Exception as e:
            self.logger.error(f"Follow-up question generation failed: {str(e)}")
            return []

    def format_answer_for_display(self, generated_answer: GeneratedAnswer) -> Dict[str, Any]:
        """
        Format the generated answer for frontend display.
        
        Args:
            generated_answer: The generated answer object
            
        Returns:
            Formatted response dictionary
        """
        return {
            "answer": generated_answer.answer,
            "confidence": generated_answer.confidence,
            "citations": generated_answer.citations,
            "metadata": {
                "sources_used": generated_answer.sources_used,
                "query_intent": generated_answer.query_intent,
                "processing_time": generated_answer.processing_time,
                "warnings": generated_answer.warnings
            }
        }