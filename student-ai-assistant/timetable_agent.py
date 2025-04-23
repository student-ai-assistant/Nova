"""
timetable_agent.py - Multi-agent workflow for timetable generation feature
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
import datetime
from document_processor import extract_document_text
from journal_utils import JournalExtractor
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimetableAgentSystem:
    """Multi-agent system for timetable generation"""

    def __init__(
        self,
        openai_endpoint: str,
        openai_api_key: str,
        openai_api_version: str,
        openai_deployment: str,
        document_intelligence_endpoint: str = None,
        document_intelligence_key: str = None
    ):
        """
        Initialize the timetable agent system

        Args:
            openai_endpoint: Azure OpenAI endpoint URL
            openai_api_key: Azure OpenAI API key
            openai_api_version: Azure OpenAI API version
            openai_deployment: Azure OpenAI deployment name for chat model
            document_intelligence_endpoint: Azure Document Intelligence endpoint URL (optional)
            document_intelligence_key: Azure Document Intelligence API key (optional)
        """
        self.openai_endpoint = openai_endpoint
        self.openai_api_key = openai_api_key
        self.openai_api_version = openai_api_version
        self.openai_deployment = openai_deployment
        self.document_intelligence_endpoint = document_intelligence_endpoint
        self.document_intelligence_key = document_intelligence_key

    def extract_topics_from_documents(self, documents: List[Dict[str, Any]], upload_folder: str, scope: str) -> Dict[str, Any]:
        """
        Agent 1 (Topic Extractor): Extract topics from documents based on specified scope

        Args:
            documents: List of document metadata
            upload_folder: Path to folder containing uploaded documents
            scope: User-specified scope of topics to focus on

        Returns:
            Dictionary containing extracted topics and other metadata
        """
        logger.info(f"Extracting topics from {len(documents)} documents with scope: {scope}")

        all_document_text = []
        documents_info = []

        # Process each document to extract text
        for doc in documents:
            try:
                file_path = os.path.join(upload_folder, doc['storage_path'])
                filename = doc['filename']

                # Gather document details
                doc_info = {
                    "filename": filename,
                    "id": doc['_id']
                }

                # Extract text using existing document processor
                document_text = extract_document_text(file_path)

                if document_text:
                    # Keep track of document text for topic extraction
                    all_document_text.append({
                        "filename": filename,
                        "text": document_text[:10000],  # Limit text size for API calls
                        "info": doc_info
                    })

                documents_info.append(doc_info)

            except Exception as e:
                logger.error(f"Error processing document {doc.get('filename', 'unknown')}: {str(e)}")

        # Use Azure OpenAI to extract topics from document text
        extracted_topics = self._extract_topics_with_ai(all_document_text, scope)

        return {
            "documents": documents_info,
            "topics": extracted_topics,
            "extraction_timestamp": datetime.datetime.utcnow().isoformat(),
            "scope": scope
        }

    def _extract_topics_with_ai(self, document_texts: List[Dict[str, Any]], scope: str) -> Dict[str, Any]:
        """
        Use Azure OpenAI to extract topics from document text

        Args:
            document_texts: List of dictionaries containing document texts
            scope: User-specified scope to focus on

        Returns:
            Dictionary with extracted topics
        """
        if not document_texts:
            logger.warning("No document texts provided for topic extraction")
            return {
                "main_topics": ["No documents provided"],
                "subtopics": {},
                "error": "No document content available"
            }

        try:
            # Prepare combined document text samples
            combined_text = ""
            for doc in document_texts:
                # Add document name and a sample of content (first ~5000 chars)
                sample_text = doc["text"][:5000] + "..." if len(doc["text"]) > 5000 else doc["text"]
                combined_text += f"\n\n## Document: {doc['filename']}\n{sample_text}"

            # Call Azure OpenAI API for topic extraction
            url = f"{self.openai_endpoint}/openai/deployments/{self.openai_deployment}/chat/completions?api-version={self.openai_api_version}"

            # Prepare the topic extraction prompt
            system_message = """
            You are a Topic Extraction Agent specialized in analyzing educational content and extracting key topics.
            Your task is to analyze the provided document text and extract:
            1. Main topics - The primary concepts or subject areas covered
            2. Subtopics - Important details, concepts, or sections within each main topic
            3. Key terms - Important terminology, definitions, formulas, or facts

            Format your response as a structured JSON object with these keys:
            - main_topics: An array of 3-8 main topics identified
            - subtopics: An object with main topics as keys and arrays of subtopics as values
            - key_terms: An object with main topics as keys and arrays of key terms/definitions/formulas as values

            Ensure your JSON is well-formed. Focus your analysis on the scope provided by the user.
            """

            user_message = f"""
            Please analyze the following document content and extract the main topics, subtopics, and key terms.

            USER SCOPE/FOCUS: {scope}

            DOCUMENT CONTENT:
            {combined_text}

            Return your analysis as a well-formed JSON object with main_topics, subtopics, and key_terms as specified.
            """

            payload = {
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.3,
                "top_p": 0.95,
                "max_tokens": 2000
            }

            headers = {
                "Content-Type": "application/json",
                "api-key": self.openai_api_key
            }

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            ai_response = result['choices'][0]['message']['content']

            # Try to extract the JSON part from the response
            try:
                # Look for JSON object in the response
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = ai_response[json_start:json_end]
                    topics_data = json.loads(json_str)
                else:
                    # If no JSON object found, try to parse the whole response
                    topics_data = json.loads(ai_response)

                return topics_data

            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from AI response")
                return {
                    "main_topics": ["Error extracting structured topics"],
                    "subtopics": {},
                    "key_terms": {},
                    "raw_response": ai_response[:500]  # Include part of the raw response for debugging
                }

        except Exception as e:
            logger.error(f"Error extracting topics with AI: {str(e)}")
            return {
                "main_topics": ["Error in topic extraction"],
                "subtopics": {},
                "key_terms": {},
                "error": str(e)
            }

    def generate_timetable(
        self,
        extracted_topics: Dict[str, Any],
        journal_entries: List[Dict[str, Any]],
        timeframe: str
    ) -> Dict[str, Any]:
        """
        Agent 2 (Timetable Generator): Generate a timetable based on topics and journal context

        Args:
            extracted_topics: Topics extracted by Agent 1
            journal_entries: User journal entries for context
            timeframe: User-specified timeframe for the study plan

        Returns:
            Dictionary containing the generated timetable
        """
        logger.info("Generating timetable based on extracted topics and journal entries")

        try:
            # Format topics for the prompt
            topics_text = json.dumps(extracted_topics, indent=2)

            # Format journal entries for context
            journal_context = JournalExtractor.get_memory_context(journal_entries, max_entries=15)

            # Call Azure OpenAI API for timetable generation
            url = f"{self.openai_endpoint}/openai/deployments/{self.openai_deployment}/chat/completions?api-version={self.openai_api_version}"

            system_message = f"""
            You are a Study Timetable Generation Agent specialized in creating personalized study plans.
            Your task is to create a detailed, structured study timetable based on:
            1. The topics that need to be covered
            2. The user's timeframe for studying
            3. The user's existing commitments from their journal entries

            Consider the user's existing commitments mentioned in their journal entries when planning.
            Mention the commitments during the time period in the overview.
            Reduce the session durations **drastically** leading up to the day of commitments and the day of the commitments itself.

            Format your response as a JSON object with these keys:
            - timetable: An array of study sessions, each with:
                - day: The day for the session, if possible the dates (e.g., "Day 1", "Monday, April 25")
                - time: Suggested time block (e.g., "9:00 AM - 10:30 AM")
                - topics: Topics to cover in this session
                - activities: Suggested study activities
                - duration: Estimated duration in minutes
                - priority: Priority level ("high", "medium", "low")
            - overview: A short textual overview of the timetable
            - suggestions: Additional study tips or suggestions

            Focus on the specified timeframe and ensure all important topics are covered.
            """

            user_message = f"""
            Please create a personalized study timetable based on the following information:

            TIMEFRAME: {timeframe}

            TOPICS TO STUDY:
            {topics_text}

            USER JOURNAL ENTRIES (showing existing commitments):
            {journal_context if journal_context else "No journal entries available"}

            Please return a well-structured JSON timetable that covers all important topics within the specified timeframe
            while respecting any commitments mentioned in the journal entries.
            """

            payload = {
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "top_p": 0.95,
                "max_tokens": 3000
            }

            headers = {
                "Content-Type": "application/json",
                "api-key": self.openai_api_key
            }

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()
            ai_response = result['choices'][0]['message']['content']

            # Try to extract the JSON part from the response
            try:
                # Look for JSON object in the response
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = ai_response[json_start:json_end]
                    timetable_data = json.loads(json_str)
                else:
                    # If no JSON object found, try to parse the whole response
                    timetable_data = json.loads(ai_response)

                # Add generation timestamp
                timetable_data['generated_at'] = datetime.datetime.utcnow().isoformat()
                timetable_data['timeframe'] = timeframe

                return timetable_data

            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from AI timetable response")
                return {
                    "error": "Failed to generate structured timetable",
                    "timetable": [],
                    "overview": "There was an error generating your timetable.",
                    "raw_response": ai_response[:500]  # Include part of the raw response for debugging
                }

        except Exception as e:
            logger.error(f"Error generating timetable with AI: {str(e)}")
            return {
                "error": str(e),
                "timetable": [],
                "overview": "There was an error generating your timetable."
            }