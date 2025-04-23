"""
timetable_agent.py - Multi-agent workflow for timetable generation feature
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
import datetime
import calendar
from document_processor import extract_document_text
from journal_utils import JournalExtractor
import requests
from icalendar import Calendar, Event
from datetime import datetime as dt, timedelta

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

    def analyze_journal_entries(
        self,
        journal_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Agent 3 (Journal Augmentation): Extract structured time commitments from journal entries

        Args:
            journal_entries: List of user journal entries

        Returns:
            Dictionary containing structured commitments and other metadata
        """
        logger.info(f"Analyzing {len(journal_entries) if journal_entries else 0} journal entries for commitments")

        if not journal_entries:
            return {
                "commitments": [],
                "analysis_timestamp": datetime.datetime.utcnow().isoformat(),
                "message": "No journal entries provided for analysis"
            }

        # Format journal entries for the prompt
        journal_context = JournalExtractor.get_memory_context(journal_entries, max_entries=30)

        # Call Azure OpenAI API for journal analysis
        url = f"{self.openai_endpoint}/openai/deployments/{self.openai_deployment}/chat/completions?api-version={self.openai_api_version}"

        system_message = """
        You are a Journal Analysis Agent specialized in identifying time commitments and appointments from user journal entries.
        Your task is to analyze the provided journal entries and extract any information about:
        1. Appointments (meetings, classes, events, etc.)
        2. Deadlines (assignments, projects, exams, etc.)
        3. Regular commitments (work shifts, club meetings, etc.)
        4. Any other time-specific obligations

        For each commitment, extract:
        - description: What the commitment is
        - date: The date of the commitment in YYYY-MM-DD format, infer the year if not specified using current context
        - start_time: The start time in 24-hour format (HH:MM), if available
        - end_time: The end time in 24-hour format (HH:MM), if available
        - duration: The duration in minutes, if explicitly stated or can be calculated
        - priority: The priority level ("high", "medium", "low") based on context
        - location: The location, if mentioned
        - notes: Any additional relevant information

        Format your response as a JSON object with a "commitments" key containing an array of commitment objects.
        If a commitment lacks certain information, use null for that field. Avoid including commitments that are too vague or lack a specific date.

        Today's date for reference: {current_date}
        """

        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        system_message = system_message.format(current_date=current_date)

        user_message = f"""
        Please analyze the following journal entries and extract all time commitments:

        USER JOURNAL ENTRIES:
        {journal_context}

        Return your analysis as a well-formed JSON object with the commitments array as specified.
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

        try:
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
                    commitments_data = json.loads(json_str)
                else:
                    # If no JSON object found, try to parse the whole response
                    commitments_data = json.loads(ai_response)

                # Add analysis timestamp
                commitments_data['analysis_timestamp'] = datetime.datetime.utcnow().isoformat()

                return commitments_data

            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from AI journal analysis response")
                return {
                    "error": "Failed to extract structured commitments",
                    "commitments": [],
                    "raw_response": ai_response[:500]  # Include part of the raw response for debugging
                }

        except Exception as e:
            logger.error(f"Error analyzing journal entries with AI: {str(e)}")
            return {
                "error": str(e),
                "commitments": [],
                "message": "There was an error analyzing your journal entries."
            }

    def generate_timetable(
        self,
        extracted_topics: Dict[str, Any],
        journal_entries: List[Dict[str, Any]],
        timeframe: str
    ) -> Dict[str, Any]:
        """
        Multi-agent workflow for generating a timetable:
        1. Agent 1 (Topic Extractor) - Already called to extract topics
        2. Agent 3 (Journal Augmentation) - Analyze journal entries to extract commitments
        3. Agent 2 (Timetable Generator) - Create timetable with topics and avoiding commitments

        Args:
            extracted_topics: Topics extracted by Agent 1
            journal_entries: User journal entries for context
            timeframe: User-specified timeframe for the study plan

        Returns:
            Dictionary containing the generated timetable
        """
        logger.info("Starting multi-agent timetable generation workflow")

        try:
            # Format topics for the prompt
            topics_text = json.dumps(extracted_topics, indent=2)

            # AGENT 3: Analyze journal entries to extract structured commitments
            commitments_data = self.analyze_journal_entries(journal_entries)
            commitments_text = json.dumps(commitments_data, indent=2)

            # Calculate study timeframe
            start_date = datetime.datetime.now() + datetime.timedelta(days=1)  # Start from tomorrow
            timeframe_info = self._calculate_timeframe(timeframe, start_date)

            # AGENT 2: Generate timetable based on topics and commitments
            timetable_data = self._generate_timetable_with_conflicts(
                extracted_topics=extracted_topics,
                commitments_data=commitments_data,
                timeframe=timeframe,
                timeframe_info=timeframe_info
            )

            return timetable_data

        except Exception as e:
            logger.error(f"Error in timetable generation workflow: {str(e)}")
            return {
                "error": str(e),
                "timetable": [],
                "overview": "There was an error generating your timetable."
            }

    def _calculate_timeframe(self, timeframe_text: str, start_date: datetime.datetime) -> Dict[str, Any]:
        """
        Calculate actual start and end dates based on user-specified timeframe

        Args:
            timeframe_text: User-specified timeframe (e.g., "next 2 weeks", "3 days")
            start_date: Starting date for the timetable (usually tomorrow)

        Returns:
            Dictionary with start_date, end_date, and duration_days
        """
        # Default to 7 days if unable to parse
        default_days = 7
        end_date = start_date + datetime.timedelta(days=default_days)

        try:
            # Call Azure OpenAI to parse the timeframe
            url = f"{self.openai_endpoint}/openai/deployments/{self.openai_deployment}/chat/completions?api-version={self.openai_api_version}"

            system_message = """
            You are a Date Parser specialized in converting natural language timeframes into precise durations.
            Your task is to analyze the provided timeframe text and extract:
            1. The number of days this timeframe represents

            Format your response as a JSON object with:
            - days: The number of days (integer)

            Examples:
            "next 2 weeks" -> {"days": 14}
            "3 days" -> {"days": 3}
            "by Friday" -> {"days": X} (where X is the number of days until Friday)
            "2 months" -> {"days": 60}
            """

            user_message = f"""
            Please parse the following timeframe and convert it to a number of days:

            TIMEFRAME: {timeframe_text}
            TODAY: {start_date.strftime('%Y-%m-%d')} ({start_date.strftime('%A')})

            Return your analysis as a well-formed JSON object with days specified as an integer.
            """

            payload = {
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.3,
                "top_p": 0.95,
                "max_tokens": 500
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
                    duration_data = json.loads(json_str)
                else:
                    # If no JSON object found, try to parse the whole response
                    duration_data = json.loads(ai_response)

                days = duration_data.get('days', default_days)
                # Ensure reasonable limits
                days = min(max(1, days), 90)  # Between 1 and 90 days

                end_date = start_date + datetime.timedelta(days=days)

            except (json.JSONDecodeError, KeyError):
                logger.error("Failed to parse timeframe duration")
                # Fallback to default duration
                days = default_days
                end_date = start_date + datetime.timedelta(days=days)

        except Exception as e:
            logger.error(f"Error calculating timeframe: {str(e)}")
            days = default_days
            end_date = start_date + datetime.timedelta(days=days)

        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "duration_days": (end_date - start_date).days,
            "start_day_name": start_date.strftime("%A"),
            "end_day_name": end_date.strftime("%A"),
        }

    def _generate_timetable_with_conflicts(
        self,
        extracted_topics: Dict[str, Any],
        commitments_data: Dict[str, Any],
        timeframe: str,
        timeframe_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent 2 (Timetable Generator): Generate a timetable based on topics and commitments

        Args:
            extracted_topics: Topics extracted by Agent 1
            commitments_data: Commitments extracted by Agent 3
            timeframe: Original user-specified timeframe text
            timeframe_info: Calculated timeframe information

        Returns:
            Dictionary containing the generated timetable with conflicts highlighted
        """
        logger.info("Generating timetable with conflict awareness")

        try:
            # Format topics and commitments for the prompt
            topics_text = json.dumps(extracted_topics.get("topics", {}), indent=2)
            commitments = commitments_data.get("commitments", [])
            commitments_text = json.dumps(commitments, indent=2)

            # Call Azure OpenAI API for timetable generation
            url = f"{self.openai_endpoint}/openai/deployments/{self.openai_deployment}/chat/completions?api-version={self.openai_api_version}"

            system_message = f"""
            You are a Study Timetable Generation Agent specialized in creating personalized study plans.
            Your task is to create a detailed, structured study timetable based on:
            1. The topics that need to be covered
            2. The user's timeframe for studying
            3. The user's existing commitments

            IMPORTANT INSTRUCTIONS:
            - The study timetable should START from {timeframe_info['start_date']} ({timeframe_info['start_day_name']})
              and END on {timeframe_info['end_date']} ({timeframe_info['end_day_name']})
            - Clearly mark any study sessions that conflict with the user's commitments as "CONFLICT" in a separate field
            - Avoid scheduling study sessions during times when the user has commitments if possible
            - If conflicts are unavoidable, clearly identify them so they can be visualized differently

            Format your response as a JSON object with these keys:
            - timetable: An array of study sessions, each with:
                - day: The day for the session (e.g., "Monday, April 24, 2025")
                - date: The date in YYYY-MM-DD format
                - time: Suggested time block (e.g., "9:00 AM - 10:30 AM")
                - start_time: Start time in 24-hour format (e.g., "09:00")
                - end_time: End time in 24-hour format (e.g., "10:30")
                - topics: Topics to cover in this session
                - activities: Suggested study activities
                - duration: Estimated duration in minutes
                - priority: Priority level ("high", "medium", "low")
                - has_conflict: Boolean indicating whether this session conflicts with a commitment
                - conflict_details: Details of the conflict if has_conflict is true (otherwise null)
            - overview: A short textual overview of the timetable
            - suggestions: Additional study tips or suggestions based on the topics
            - conflicts_summary: A summary of any scheduling conflicts identified

            Focus on creating a practical timetable that helps the student cover all important topics within the specified timeframe.
            """

            user_message = f"""
            Please create a personalized study timetable based on the following information:

            TIMEFRAME: {timeframe}
            CALCULATED STUDY PERIOD: {timeframe_info['start_date']} to {timeframe_info['end_date']} ({timeframe_info['duration_days']} days)

            TOPICS TO STUDY:
            {topics_text}

            USER COMMITMENTS:
            {commitments_text}

            Please return a well-structured JSON timetable that covers all important topics within the specified timeframe
            while respecting the user's commitments. Clearly mark any conflicts between study sessions and commitments.
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

                # Add generated metadata
                timetable_data['generated_at'] = datetime.datetime.utcnow().isoformat()
                timetable_data['timeframe'] = timeframe
                timetable_data['study_start_date'] = timeframe_info['start_date']
                timetable_data['study_end_date'] = timeframe_info['end_date']

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

    def generate_ics_calendar(self, timetable_data: Dict[str, Any]) -> bytes:
        """
        Generate an iCalendar (.ics) file from the timetable data

        Args:
            timetable_data: Timetable data generated by the agent

        Returns:
            Bytes containing the iCalendar file content
        """
        logger.info("Generating iCalendar file from timetable data")

        try:
            # Create a calendar
            cal = Calendar()
            cal.add('prodid', '-//Student AI Assistant//Timetable Generator//EN')
            cal.add('version', '2.0')
            cal.add('calscale', 'GREGORIAN')
            cal.add('method', 'PUBLISH')
            cal.add('x-wr-calname', 'Study Timetable')
            cal.add('x-wr-timezone', 'UTC')

            # Add study sessions as events
            timetable = timetable_data.get('timetable', [])
            for session in timetable:
                event = Event()

                # Required event properties
                session_date = session.get('date')
                start_time = session.get('start_time')
                end_time = session.get('end_time')

                # Default values if parsing fails
                default_start = dt.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
                default_duration = timedelta(hours=1)

                # Parse date and times
                try:
                    if session_date and start_time:
                        dt_start = dt.strptime(f"{session_date} {start_time}", "%Y-%m-%d %H:%M")
                    else:
                        # Fall back to date from day string if available
                        day_str = session.get('day', '')
                        day_date_match = re.search(r'([A-Za-z]+, [A-Za-z]+ \d{1,2}, \d{4})', day_str)
                        if day_date_match:
                            try:
                                parsed_date = dt.strptime(day_date_match.group(1), "%A, %B %d, %Y")
                                time_str = session.get('time', '09:00 AM - 10:00 AM')
                                start_time_match = re.search(r'(\d{1,2}:\d{2} [AP]M)', time_str)
                                if start_time_match:
                                    dt_start = dt.strptime(
                                        f"{parsed_date.strftime('%Y-%m-%d')} {start_time_match.group(1)}",
                                        "%Y-%m-%d %I:%M %p"
                                    )
                                else:
                                    dt_start = parsed_date.replace(hour=9, minute=0)
                            except:
                                dt_start = default_start
                        else:
                            dt_start = default_start

                    # Determine end time or use duration
                    if session_date and end_time:
                        dt_end = dt.strptime(f"{session_date} {end_time}", "%Y-%m-%d %H:%M")
                    else:
                        duration_minutes = session.get('duration')
                        if duration_minutes and isinstance(duration_minutes, (int, float)):
                            dt_end = dt_start + timedelta(minutes=duration_minutes)
                        else:
                            # Try to parse from time string
                            time_str = session.get('time', '')
                            end_time_match = re.search(r'- (\d{1,2}:\d{2} [AP]M)', time_str)
                            if end_time_match:
                                try:
                                    dt_end = dt.strptime(
                                        f"{dt_start.strftime('%Y-%m-%d')} {end_time_match.group(1)}",
                                        "%Y-%m-%d %I:%M %p"
                                    )
                                except:
                                    dt_end = dt_start + default_duration
                            else:
                                dt_end = dt_start + default_duration
                except Exception as e:
                    logger.error(f"Error parsing study session date/time: {str(e)}")
                    dt_start = default_start
                    dt_end = dt_start + default_duration

                # Set event properties
                event.add('summary', f"Study: {', '.join(session['topics']) if isinstance(session['topics'], list) else session['topics']}")
                event.add('dtstart', dt_start)
                event.add('dtend', dt_end)
                event.add('dtstamp', dt.now())

                # Generate unique ID
                event.add('uid', f"{dt_start.strftime('%Y%m%dT%H%M%S')}-{hash(str(session))}")

                # Add description with activities and conflict info
                description_parts = []
                if session.get('activities'):
                    activities = session['activities']
                    if isinstance(activities, list):
                        description_parts.append("Activities: " + ", ".join(activities))
                    else:
                        description_parts.append(f"Activities: {activities}")

                description_parts.append(f"Priority: {session.get('priority', 'medium')}")

                if session.get('has_conflict'):
                    event.add('status', 'TENTATIVE')
                    if session.get('conflict_details'):
                        description_parts.append(f"CONFLICT: {session.get('conflict_details')}")
                    else:
                        description_parts.append("CONFLICT: This study session conflicts with another commitment")
                    # Set color class for visual indication in calendar apps that support it
                    event.add('class', 'PRIVATE')
                    event.add('color', '#FF0000')  # Red for conflicts
                else:
                    event.add('status', 'CONFIRMED')
                    event.add('class', 'PUBLIC')

                event.add('description', '\n'.join(description_parts))

                # Add to calendar
                cal.add_component(event)

            # Add overview as a separate all-day event
            if timetable_data.get('overview'):
                overview_event = Event()
                overview_event.add('summary', "Study Plan Overview")
                # Set as all-day event at the beginning of study period
                start_date_str = timetable_data.get('study_start_date')
                try:
                    start_date = dt.strptime(start_date_str, "%Y-%m-%d") if start_date_str else dt.now()
                except:
                    start_date = dt.now()
                overview_event.add('dtstart', start_date.date())
                overview_event.add('dtend', (start_date + timedelta(days=1)).date())  # End is exclusive in iCal
                overview_event.add('description', timetable_data.get('overview'))
                overview_event.add('uid', f"overview-{dt.now().strftime('%Y%m%dT%H%M%S')}")
                overview_event.add('dtstamp', dt.now())
                cal.add_component(overview_event)

            # Return the calendar as bytes
            return cal.to_ical()

        except Exception as e:
            logger.error(f"Error generating iCalendar file: {str(e)}")
            # Return a minimal valid calendar if there's an error
            cal = Calendar()
            cal.add('prodid', '-//Student AI Assistant//Timetable Generator Error//EN')
            cal.add('version', '2.0')
            error_event = Event()
            error_event.add('summary', "Error Generating Study Timetable")
            error_event.add('dtstart', dt.now())
            error_event.add('dtend', dt.now() + timedelta(hours=1))
            error_event.add('description', f"There was an error generating your study timetable: {str(e)}")
            error_event.add('uid', f"error-{dt.now().strftime('%Y%m%dT%H%M%S')}")
            error_event.add('dtstamp', dt.now())
            cal.add_component(error_event)
            return cal.to_ical()