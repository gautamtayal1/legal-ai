"""
Handles query analysis, intent detection, and query enhancement
for optimal search performance.
"""
import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

try:
    import contractions
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    import nltk
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


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
    keywords: List[str]
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
            
            # Extract keywords
            keywords = self._extract_keywords(processed_query)
            
            return ProcessedQuery(
                original_query=query,
                processed_query=processed_query,
                intent=intent,
                keywords=keywords,
                metadata={}
            )
            
        except Exception as e:
            self.logger.error(f"Query processing failed: {str(e)}")
            return ProcessedQuery(
                original_query=query,
                processed_query=query,
                intent=QueryIntent.GENERAL,
                keywords=[],
                metadata={}
            )
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize the query using proper libraries"""
        query = query.strip()
        
        if 'contractions' in globals():
            try:
                query = contractions.fix(query)
            except:
                pass
    
        query = re.sub(r'\s+', ' ', query)
        
        return query.lower()
    
    def _detect_intent(self, query: str) -> QueryIntent:
        """Detect the primary intent of the query"""
        query_lower = query.lower()
        
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
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords using NLTK if available, fallback to custom"""
        if NLTK_AVAILABLE:
            try:
                stop_words = set(stopwords.words('english'))
                legal_keep_words = {'will', 'shall', 'must', 'may', 'can', 'should'}
                stop_words = stop_words - legal_keep_words
                
                tokens = word_tokenize(query.lower())
                keywords = [word for word in tokens 
                           if word.isalpha() and word not in stop_words and len(word) > 2]
                return keywords
            except:
                pass
        
        legal_stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'would', 'could',
            'this', 'that', 'these', 'those'
        }
        
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in legal_stop_words and len(w) > 2]
        
        return keywords