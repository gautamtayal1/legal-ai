"""
Query Processor - Step 12: Query Preprocessing

Handles query analysis, intent detection, and query enhancement
for optimal search performance.
"""
import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class QueryIntent(Enum):
    GENERAL = "general"
    DEFINITION = "definition"
    OBLIGATION = "obligation" 
    TIMELINE = "timeline"
    PARTY = "party"
    TERMINATION = "termination"
    PAYMENT = "payment"
    LIABILITY = "liability"


@dataclass
class ProcessedQuery:
    original_query: str
    processed_query: str
    intent: QueryIntent
    entities: List[str]
    keywords: List[str]
    synonyms: List[str]
    query_variations: List[str]
    metadata: Dict[str, Any]


class QueryProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Legal intent patterns
        self.intent_patterns = {
            QueryIntent.DEFINITION: [
                r'what\s+(?:is|are|does|means?)\s+',
                r'define\s+',
                r'definition\s+of\s+',
                r'meaning\s+of\s+'
            ],
            QueryIntent.OBLIGATION: [
                r'(?:must|shall|required?|obligat\w+|duty|responsible)',
                r'what\s+(?:do|does)\s+\w+\s+(?:have\s+to|need\s+to)',
                r'responsibilities?\s+of\s+'
            ],
            QueryIntent.TIMELINE: [
                r'(?:when|timeline|deadline|due\s+date|within\s+\d+)',
                r'how\s+long\s+',
                r'\d+\s+days?\s+'
            ],
            QueryIntent.PARTY: [
                r'(?:who\s+is|which\s+party|company|client|contractor)',
                r'parties?\s+(?:to|in)\s+'
            ],
            QueryIntent.TERMINATION: [
                r'(?:terminat\w+|end\w+|cancel\w+|expir\w+)',
                r'how\s+to\s+(?:end|stop|cancel)',
                r'grounds?\s+for\s+termination'
            ],
            QueryIntent.PAYMENT: [
                r'(?:payment|fee|cost|price|amount|invoice|bill)',
                r'how\s+much\s+',
                r'money|dollars?\s+'
            ],
            QueryIntent.LIABILITY: [
                r'(?:liability|liable|responsible|damages?|indemnif\w+)',
                r'who\s+(?:pays?|is\s+responsible)',
                r'damages?\s+for\s+'
            ]
        }
        
        # Legal term synonyms
        self.synonyms = {
            'termination': ['cancellation', 'ending', 'expiration', 'dissolution'],
            'obligation': ['duty', 'responsibility', 'requirement', 'commitment'],
            'party': ['entity', 'company', 'organization', 'contractor'],
            'payment': ['fee', 'compensation', 'amount', 'cost', 'price'],
            'liability': ['responsibility', 'accountability', 'damages'],
            'agreement': ['contract', 'deal', 'arrangement', 'understanding']
        }
        
        # Common legal entities
        self.legal_entities = [
            'company', 'corporation', 'client', 'contractor', 'vendor',
            'supplier', 'customer', 'buyer', 'seller', 'lessor', 'lessee'
        ]
    
    def process_query(self, query: str) -> ProcessedQuery:
        """
        Process a user query for optimal retrieval.
        
        This implements Step 12: Query Preprocessing from the architecture.
        """
        try:
            # Clean and normalize query
            processed_query = self._clean_query(query)
            
            # Detect intent
            intent = self._detect_intent(query)
            
            # Extract entities
            entities = self._extract_entities(query)
            
            # Extract keywords
            keywords = self._extract_keywords(processed_query)
            
            # Generate synonyms
            synonyms = self._generate_synonyms(keywords)
            
            # Create query variations
            variations = self._create_query_variations(processed_query, synonyms)
            
            # Add metadata
            metadata = {
                'confidence': self._calculate_intent_confidence(query, intent),
                'complexity': self._assess_query_complexity(query),
                'legal_context': self._detect_legal_context(query)
            }
            
            return ProcessedQuery(
                original_query=query,
                processed_query=processed_query,
                intent=intent,
                entities=entities,
                keywords=keywords,
                synonyms=synonyms,
                query_variations=variations,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Query processing failed: {str(e)}")
            return ProcessedQuery(
                original_query=query,
                processed_query=query,
                intent=QueryIntent.GENERAL,
                entities=[],
                keywords=[],
                synonyms=[],
                query_variations=[query],
                metadata={'error': str(e)}
            )
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize the query"""
        # Convert to lowercase
        query = query.lower().strip()
        
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query)
        
        # Normalize contractions
        contractions = {
            "what's": "what is",
            "what're": "what are", 
            "who's": "who is",
            "how's": "how is",
            "can't": "cannot",
            "won't": "will not",
            "shouldn't": "should not"
        }
        
        for contraction, expansion in contractions.items():
            query = query.replace(contraction, expansion)
        
        return query
    
    def _detect_intent(self, query: str) -> QueryIntent:
        """Detect the primary intent of the query"""
        query_lower = query.lower()
        
        # Score each intent
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query_lower))
                score += matches
            intent_scores[intent] = score
        
        # Return intent with highest score, or GENERAL if no matches
        if max(intent_scores.values()) > 0:
            return max(intent_scores, key=intent_scores.get)
        
        return QueryIntent.GENERAL
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract legal entities from the query"""
        entities = []
        query_lower = query.lower()
        
        # Find legal entities
        for entity in self.legal_entities:
            if entity in query_lower:
                entities.append(entity)
        
        # Extract quoted terms (likely definitions or specific clauses)
        quoted_terms = re.findall(r'"([^"]*)"', query)
        entities.extend(quoted_terms)
        
        # Extract section references
        section_refs = re.findall(r'section\s+(\d+(?:\.\d+)*)', query_lower)
        entities.extend([f"section {ref}" for ref in section_refs])
        
        return list(set(entities))
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from the query"""
        # Remove common stop words but keep legal stop words
        legal_stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Split into words and filter
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in legal_stop_words and len(w) > 2]
        
        return keywords
    
    def _generate_synonyms(self, keywords: List[str]) -> List[str]:
        """Generate synonyms for keywords"""
        synonyms = []
        for keyword in keywords:
            if keyword in self.synonyms:
                synonyms.extend(self.synonyms[keyword])
        
        return list(set(synonyms))
    
    def _create_query_variations(self, query: str, synonyms: List[str]) -> List[str]:
        """Create variations of the query using synonyms"""
        variations = [query]
        
        # Create synonym variations
        for base_word, synonym_list in self.synonyms.items():
            if base_word in query:
                for synonym in synonym_list[:2]:  # Limit to 2 synonyms to avoid explosion
                    variation = query.replace(base_word, synonym)
                    variations.append(variation)
        
        return list(set(variations))
    
    def _calculate_intent_confidence(self, query: str, intent: QueryIntent) -> float:
        """Calculate confidence score for the detected intent"""
        if intent == QueryIntent.GENERAL:
            return 0.5
        
        query_lower = query.lower()
        patterns = self.intent_patterns.get(intent, [])
        
        total_matches = sum(len(re.findall(pattern, query_lower)) for pattern in patterns)
        
        # Simple confidence based on pattern matches
        return min(1.0, 0.6 + (total_matches * 0.2))
    
    def _assess_query_complexity(self, query: str) -> str:
        """Assess query complexity"""
        word_count = len(query.split())
        
        if word_count <= 3:
            return "simple"
        elif word_count <= 10:
            return "medium"
        else:
            return "complex"
    
    def _detect_legal_context(self, query: str) -> Dict[str, bool]:
        """Detect legal context indicators"""
        query_lower = query.lower()
        
        return {
            'has_section_reference': bool(re.search(r'section\s+\d+', query_lower)),
            'has_legal_terms': any(term in query_lower for term in 
                                 ['contract', 'agreement', 'clause', 'provision', 'term']),
            'has_obligations': any(term in query_lower for term in 
                                 ['must', 'shall', 'required', 'obligation']),
            'has_parties': any(term in query_lower for term in self.legal_entities)
        } 