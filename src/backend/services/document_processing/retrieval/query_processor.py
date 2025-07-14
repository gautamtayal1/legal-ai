"""
Query preprocessing service for legal document retrieval.
Implements Step 12 from architecture: Query Preprocessing
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate


class QueryIntent(Enum):
    DEFINITION = "definition"
    OBLIGATIONS = "obligations"
    TERMINATION = "termination"
    PARTIES = "parties"
    DEADLINES = "deadlines"
    RIGHTS = "rights"
    GENERAL = "general"


@dataclass
class ProcessedQuery:
    original_query: str
    intent: QueryIntent
    entities: List[str]
    expanded_terms: List[str]
    legal_concepts: List[str]
    search_variations: List[str]
    confidence: float


class QueryProcessor:
    """
    Processes user queries for optimal legal document retrieval.
    Handles intent detection, entity extraction, and query expansion.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Legal term patterns
        self.legal_patterns = {
            QueryIntent.DEFINITION: [
                r"what is|what are|define|definition|meaning of|means",
                r"shall mean|is defined as|refers to"
            ],
            QueryIntent.OBLIGATIONS: [
                r"must|shall|required|obligation|duty|responsible",
                r"comply|perform|deliver|provide"
            ],
            QueryIntent.TERMINATION: [
                r"terminat|end|cancel|expire|dissolution",
                r"breach|default|notice period"
            ],
            QueryIntent.PARTIES: [
                r"party|parties|company|client|contractor",
                r"who is|which party|responsible party"
            ],
            QueryIntent.DEADLINES: [
                r"when|deadline|due date|within|days|months",
                r"notice period|time limit|expiration"
            ],
            QueryIntent.RIGHTS: [
                r"rights|entitle|may|can|permitted",
                r"intellectual property|ownership|license"
            ]
        }
        
        # Legal concept synonyms
        self.legal_synonyms = {
            "termination": ["ending", "cancellation", "expiration", "dissolution"],
            "obligations": ["duties", "responsibilities", "requirements"],
            "parties": ["entities", "signatories", "contractors"],
            "breach": ["violation", "default", "non-compliance"],
            "notice": ["notification", "warning", "communication"],
            "deadline": ["due date", "time limit", "expiration"],
            "rights": ["entitlements", "privileges", "permissions"],
            "liability": ["responsibility", "accountability", "damages"],
            "intellectual property": ["IP", "patents", "copyrights", "trademarks"],
            "confidential": ["proprietary", "sensitive", "non-disclosure"]
        }
        
        # Common legal entities
        self.legal_entities = [
            "company", "corporation", "LLC", "partnership", "client",
            "contractor", "vendor", "supplier", "licensor", "licensee",
            "employer", "employee", "party", "parties"
        ]

    async def process_query(self, query: str) -> ProcessedQuery:
        """
        Process a user query for legal document retrieval.
        
        Args:
            query: The user's natural language query
            
        Returns:
            ProcessedQuery object with analyzed query components
        """
        try:
            # Clean and normalize query
            cleaned_query = self._clean_query(query)
            
            # Detect intent
            intent = self._detect_intent(cleaned_query)
            
            # Extract entities
            entities = self._extract_entities(cleaned_query)
            
            # Extract legal concepts
            legal_concepts = self._extract_legal_concepts(cleaned_query)
            
            # Expand query terms
            expanded_terms = self._expand_query_terms(cleaned_query, legal_concepts)
            
            # Generate search variations
            search_variations = self._generate_search_variations(cleaned_query, expanded_terms)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(intent, entities, legal_concepts)
            
            processed_query = ProcessedQuery(
                original_query=query,
                intent=intent,
                entities=entities,
                expanded_terms=expanded_terms,
                legal_concepts=legal_concepts,
                search_variations=search_variations,
                confidence=confidence
            )
            
            self.logger.info(f"Processed query: {query} -> Intent: {intent.value}, "
                           f"Entities: {len(entities)}, Concepts: {len(legal_concepts)}")
            
            return processed_query
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            # Return basic processed query on error
            return ProcessedQuery(
                original_query=query,
                intent=QueryIntent.GENERAL,
                entities=[],
                expanded_terms=[query],
                legal_concepts=[],
                search_variations=[query],
                confidence=0.5
            )

    def _clean_query(self, query: str) -> str:
        """Clean and normalize the query text."""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Convert to lowercase for processing
        query = query.lower()
        
        # Remove common question words that don't add value
        query = re.sub(r'\b(what|when|where|why|how|can|could|should|would|will)\b', '', query)
        
        # Remove extra punctuation
        query = re.sub(r'[^\w\s\-\']', ' ', query)
        
        return query.strip()

    def _detect_intent(self, query: str) -> QueryIntent:
        """Detect the intent of the query based on legal patterns."""
        intent_scores = {}
        
        for intent, patterns in self.legal_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query, re.IGNORECASE))
                score += matches
            intent_scores[intent] = score
        
        # Return the intent with highest score, or GENERAL if no clear intent
        if intent_scores and max(intent_scores.values()) > 0:
            return max(intent_scores, key=intent_scores.get)
        
        return QueryIntent.GENERAL

    def _extract_entities(self, query: str) -> List[str]:
        """Extract legal entities from the query."""
        entities = []
        
        # Extract legal entities
        for entity in self.legal_entities:
            if entity.lower() in query.lower():
                entities.append(entity)
        
        # Extract potential proper nouns (capitalized words)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', query)
        entities.extend(proper_nouns)
        
        # Extract numbers and dates
        numbers = re.findall(r'\b\d+\b', query)
        entities.extend(numbers)
        
        # Extract quoted terms
        quoted_terms = re.findall(r'"([^"]*)"', query)
        entities.extend(quoted_terms)
        
        return list(set(entities))  # Remove duplicates

    def _extract_legal_concepts(self, query: str) -> List[str]:
        """Extract legal concepts and terms from the query."""
        concepts = []
        
        # Check for legal concepts in our synonym dictionary
        for concept, synonyms in self.legal_synonyms.items():
            if concept.lower() in query.lower():
                concepts.append(concept)
            
            # Check for synonyms
            for synonym in synonyms:
                if synonym.lower() in query.lower():
                    concepts.append(concept)
                    break
        
        # Extract common legal phrases
        legal_phrases = [
            "notice period", "breach of contract", "intellectual property",
            "confidentiality agreement", "non-disclosure", "force majeure",
            "governing law", "dispute resolution", "limitation of liability",
            "indemnification", "warranty", "representation"
        ]
        
        for phrase in legal_phrases:
            if phrase.lower() in query.lower():
                concepts.append(phrase)
        
        return list(set(concepts))

    def _expand_query_terms(self, query: str, legal_concepts: List[str]) -> List[str]:
        """Expand query terms with synonyms and related terms."""
        expanded_terms = [query]
        
        # Add synonyms for identified legal concepts
        for concept in legal_concepts:
            if concept in self.legal_synonyms:
                expanded_terms.extend(self.legal_synonyms[concept])
        
        # Add common legal variations
        variations = {
            "terminate": ["end", "cancel", "dissolve"],
            "contract": ["agreement", "arrangement"],
            "payment": ["compensation", "remuneration"],
            "deliverable": ["work product", "output"],
            "confidential": ["proprietary", "sensitive"]
        }
        
        for term, synonyms in variations.items():
            if term.lower() in query.lower():
                expanded_terms.extend(synonyms)
        
        return list(set(expanded_terms))

    def _generate_search_variations(self, query: str, expanded_terms: List[str]) -> List[str]:
        """Generate different search variations for the query."""
        variations = [query]
        
        # Add expanded terms as separate searches
        variations.extend(expanded_terms)
        
        # Create phrase variations
        words = query.split()
        if len(words) > 1:
            # Add partial phrases
            for i in range(len(words) - 1):
                phrase = " ".join(words[i:i+2])
                variations.append(phrase)
        
        # Add boolean variations for complex queries
        if len(words) > 2:
            # AND variation
            and_query = " AND ".join(words)
            variations.append(and_query)
            
            # OR variation
            or_query = " OR ".join(words)
            variations.append(or_query)
        
        return list(set(variations))

    def _calculate_confidence(self, intent: QueryIntent, entities: List[str], 
                            legal_concepts: List[str]) -> float:
        """Calculate confidence score for the processed query."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on intent detection
        if intent != QueryIntent.GENERAL:
            confidence += 0.2
        
        # Boost confidence based on entity extraction
        if entities:
            confidence += min(0.2, len(entities) * 0.05)
        
        # Boost confidence based on legal concept detection
        if legal_concepts:
            confidence += min(0.3, len(legal_concepts) * 0.1)
        
        # Cap confidence at 1.0
        return min(1.0, confidence)

    def get_search_strategy(self, processed_query: ProcessedQuery) -> Dict[str, Any]:
        """
        Get search strategy recommendations based on processed query.
        
        Args:
            processed_query: The processed query object
            
        Returns:
            Dictionary containing search strategy recommendations
        """
        strategy = {
            "vector_search_weight": 0.6,
            "keyword_search_weight": 0.4,
            "filters": {},
            "boost_fields": [],
            "search_type": "hybrid"
        }
        
        # Adjust weights based on intent
        if processed_query.intent == QueryIntent.DEFINITION:
            strategy["keyword_search_weight"] = 0.7
            strategy["vector_search_weight"] = 0.3
            strategy["boost_fields"] = ["legal_definitions"]
        
        elif processed_query.intent == QueryIntent.OBLIGATIONS:
            strategy["vector_search_weight"] = 0.8
            strategy["keyword_search_weight"] = 0.2
            strategy["boost_fields"] = ["legal_obligations"]
        
        elif processed_query.intent == QueryIntent.PARTIES:
            strategy["keyword_search_weight"] = 0.6
            strategy["vector_search_weight"] = 0.4
            strategy["boost_fields"] = ["legal_parties"]
        
        # Add filters based on legal concepts
        if "confidential" in processed_query.legal_concepts:
            strategy["filters"]["has_legal_context"] = True
        
        return strategy