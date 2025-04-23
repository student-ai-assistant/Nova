"""
journal_utils.py - Utilities for managing and extracting information for memory journals
"""

import logging
import re
from typing import Dict, Any, List, Optional
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JournalExtractor:
    """Class for extracting important information from conversations for memory journals"""
    
    # Keywords that might indicate important information to save
    IMPORTANT_KEYWORDS = [
        "remember", "don't forget", "important", "note", "save",
        "my name is", "I am", "I'm", "I like", "I need", "I want",
        "I have to", "I must", "my goal is", "my preference is",
        "key concept", "crucial", "essential", "vital", "significant",
        "critical", "fundamental", "key point", "deadline", "due date",
        "exam", "test", "quiz", "assignment", "project", "paper",
        "remember that", "keep in mind", "make sure to"
    ]
    
    # AI-specific keywords that indicate information worth saving from AI responses
    AI_IMPORTANT_KEYWORDS = [
        "key concept", "important to remember", "critical point", 
        "essential information", "remember that", "don't forget",
        "make note of", "take note", "helpful tip", "important formula",
        "key definition", "fundamental principle", "crucial detail",
        "this is important", "mark this", "highlight this"
    ]
    
    # Information patterns to look for in text
    INFORMATION_PATTERNS = [
        r"(?:my name is|I am|I'm)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Name
        r"(?:I|my) (?:have|need|want) to\s+(.+?)(?:\.|$)",  # Task/need
        r"(?:deadline|due date).*?(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)",  # Date pattern
        r"(?:I|my) (?:preference|like) (?:is|for)\s+(.+?)(?:\.|$)",  # Preference
        r"(?:my goal is|trying to)\s+(.+?)(?:\.|$)"  # Goal
    ]
    
    @staticmethod
    def should_save_ai_response(info: Dict[str, Any]) -> bool:
        """
        Determine if information from an AI response should be saved to the journal
        
        Args:
            info: Dictionary containing extracted information
            
        Returns:
            Boolean indicating whether to save this information
        """
        # Check if there's content to save
        if not info or 'content' not in info:
            return False
            
        content = info.get('content', '').lower()
        
        # Skip very short content or generic negative responses
        if len(content.split()) < 5 or content.startswith("i don't know") or "no information" in content:
            return False
            
        # Check for AI-specific important keywords (high priority)
        for keyword in JournalExtractor.AI_IMPORTANT_KEYWORDS:
            if keyword.lower() in content:
                logger.info(f"Saving AI response with important keyword: {keyword}")
                return True
                
        # Check for educational content markers (high priority)
        educational_markers = [
            "definition:", "formula:", "equation:", "theorem:", "principle:",
            "concept:", "method:", "approach:", "technique:", "strategy:",
            "rule:", "law:", "theory:", "hypothesis:", "conclusion:", "example:",
            "step 1", "step 2", "first,", "second,", "third,", "finally,",
            "remember:", "note:", "tip:", "hint:"
        ]
        
        for marker in educational_markers:
            if marker in content:
                logger.info(f"Saving AI response with educational marker: {marker}")
                return True
                
        # Check for sentences with factual statements (medium priority)
        factual_indicators = [
            " is ", " are ", " was ", " were ", " has ", " have ",
            " can ", " will ", " should ", " must ", " means ", " refers to ",
            " consists of ", " contains ", " includes ", " represents ",
            " equals ", " equals to ", " is equal to ", " is defined as "
        ]
        
        # If it's a relatively long, possibly detailed explanation 
        # that contains factual indicators, save it
        if len(content.split()) > 15:
            for indicator in factual_indicators:
                if indicator in content:
                    logger.info(f"Saving longer AI response with factual indicator: {indicator}")
                    return True
                
        # Check if the content has a keyword from the regular important keywords list
        for keyword in JournalExtractor.IMPORTANT_KEYWORDS:
            if keyword.lower() in content:
                logger.info(f"Saving AI response with general keyword: {keyword}")
                return True
                
        # Additional heuristic: Save content that appears to be structured knowledge
        if any(char in content for char in [':', '-', '•', '*', '1.', '2.']):
            if len(content.split('\n')) > 1 or len(content.split()) > 20:
                logger.info("Saving AI response with structured content")
                return True
                
        return False
    
    @staticmethod
    def extract_important_information(text: str) -> List[Dict[str, Any]]:
        """
        Extract important information from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of dictionaries containing extracted information
        """
        # Check if there's any text to analyze
        if not text or len(text.strip()) == 0:
            return []
        
        extracted_info = []
        
        # Check for keywords
        for keyword in JournalExtractor.IMPORTANT_KEYWORDS:
            if keyword.lower() in text.lower():
                # Find the sentence containing the keyword
                sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
                
                for sentence in sentences:
                    if keyword.lower() in sentence.lower():
                        # Clean up the sentence
                        clean_sentence = sentence.strip()
                        
                        # Create an entry
                        entry = {
                            "content": clean_sentence,
                            "keyword": keyword,
                            "extracted_at": datetime.datetime.utcnow()
                        }
                        
                        extracted_info.append(entry)
        
        # Check for information patterns
        for pattern in JournalExtractor.INFORMATION_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for match in matches:
                if match:
                    # Get the context (full sentence containing the match)
                    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
                    context = ""
                    
                    for sentence in sentences:
                        if match.lower() in sentence.lower():
                            context = sentence.strip()
                            break
                    
                    entry = {
                        "content": context if context else f"Information: {match}",
                        "matched_text": match,
                        "pattern": pattern,
                        "extracted_at": datetime.datetime.utcnow()
                    }
                    
                    extracted_info.append(entry)
        
        return extracted_info
    
    @staticmethod
    def get_memory_context(journal_entries: List[Dict[str, Any]], max_entries: int = 5) -> str:
        """
        Convert journal entries to context for AI model
        
        Args:
            journal_entries: List of journal entries
            max_entries: Maximum number of entries to include
            
        Returns:
            Context string for AI prompt
        """
        if not journal_entries:
            return ""
        
        # Limit the number of entries
        limited_entries = journal_entries[:max_entries]
        
        # Format entries into context string
        context_parts = []
        
        for entry in limited_entries:
            timestamp = entry.get('timestamp', entry.get('extracted_at'))
            date_str = timestamp.strftime('%Y-%m-%d') if timestamp else 'Unknown date'
            
            content = entry.get('content', '')
            if content:
                context_parts.append(f"[{date_str}] {content}")
        
        return "\n".join(context_parts)
    
    @staticmethod
    def prepare_journal_entry(text: str, session_id: str, subject_id: str = None) -> Dict[str, Any]:
        """
        Prepare a journal entry from text
        
        Args:
            text: Text to save in journal
            session_id: Session ID
            subject_id: Optional subject ID for subject journal
            
        Returns:
            Journal entry dictionary
        """
        entry = {
            "content": text,
            "session_id": session_id,
            "timestamp": datetime.datetime.utcnow()
        }
        
        if subject_id:
            entry["subject_id"] = subject_id
            
        return entry