"""
Quiz Generation Agent for Nova

This module provides functionality to generate multiple-choice quizzes
based on provided document content and specified topics.
"""
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuizGenerator:
    """
    Quiz Generator Agent that creates multiple-choice questions based on document content.
    It uses Azure OpenAI to generate quiz questions and options.
    """

    def __init__(self, openai_endpoint, openai_api_key, openai_api_version, openai_deployment):
        """
        Initialize the Quiz Generator with Azure OpenAI credentials.

        Args:
            openai_endpoint: Azure OpenAI API endpoint
            openai_api_key: Azure OpenAI API key
            openai_api_version: Azure OpenAI API version
            openai_deployment: Azure OpenAI deployment name
        """
        self.openai_endpoint = openai_endpoint
        self.openai_api_key = openai_api_key
        self.openai_api_version = openai_api_version
        self.openai_deployment = openai_deployment

    def generate_quiz(self, documents, topic, num_questions=5, options_per_question=4):
        """
        Generate a quiz based on the provided documents and topic.

        Args:
            documents: List of document metadata dictionaries with file paths
            topic: The specific topic to focus on
            num_questions: Number of questions to generate (default: 5)
            options_per_question: Number of options per question (default: 4)

        Returns:
            List of question dictionaries, each containing:
            - question: The question text
            - options: List of possible answers
            - correct_answer: Index of the correct answer
        """
        try:
            logger.info(f"Generating quiz on topic: '{topic}' from {len(documents)} documents")

            # Extract relevant content from documents related to the topic
            document_content = self._extract_document_content(documents)

            if not document_content or document_content.strip() == "":
                logger.warning("No document content could be extracted.")
                return []

            # Generate quiz questions using Azure OpenAI
            quiz_questions = self._generate_questions_with_openai(document_content, topic, num_questions, options_per_question)

            logger.info(f"Successfully generated {len(quiz_questions)} quiz questions")
            return quiz_questions

        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            raise

    def _extract_document_content(self, documents, upload_folder=None):
        """
        Extract text content from the provided documents.

        Args:
            documents: List of document metadata dictionaries
            upload_folder: Optional folder path where documents are stored

        Returns:
            String containing combined document text content relevant to the quiz
        """
        try:
            from document_processor import extract_document_text

            combined_content = []

            for doc in documents:
                if 'storage_path' in doc:
                    # Construct the full file path
                    if '_upload_folder' in doc:  # Check for upload_folder in document metadata
                        file_path = os.path.join(doc['_upload_folder'], doc['storage_path'])
                    elif upload_folder:  # Fallback to parameter
                        file_path = os.path.join(upload_folder, doc['storage_path'])
                    else:  # No folder provided, use storage_path directly
                        file_path = doc['storage_path']

                    # Check if file exists
                    if os.path.exists(file_path):
                        # Extract text from document
                        doc_text = extract_document_text(file_path)
                        if doc_text:
                            # Add document name as header for context
                            combined_content.append(f"Document: {doc.get('filename', 'Unnamed Document')}")
                            combined_content.append(doc_text)
                            combined_content.append("\n---\n")

            return "\n".join(combined_content)

        except Exception as e:
            logger.error(f"Error extracting document content: {str(e)}")
            return ""

    def _generate_questions_with_openai(self, document_content, topic, num_questions, options_per_question):
        """
        Generate quiz questions using Azure OpenAI based on document content and topic.

        Args:
            document_content: Text content extracted from documents
            topic: The specific topic to focus on
            num_questions: Number of questions to generate
            options_per_question: Number of options per question

        Returns:
            List of question dictionaries
        """
        import requests
        import json

        try:
            # Build the API URL
            url = f"{self.openai_endpoint}/openai/deployments/{self.openai_deployment}/chat/completions?api-version={self.openai_api_version}"

            # Prepare the system prompt
            system_prompt = f"""You are a professional educational quiz creator.

Your task is to create {num_questions} high-quality multiple-choice questions based on the document content provided.
Focus specifically on the topic: {topic}.

Each question should:
1. Be clear, concise, and based solely on the provided content
2. Have exactly {options_per_question} options
3. Have exactly one correct answer
4. Be challenging but fair, testing understanding rather than trivial details
5. Cover different aspects of the topic for a well-rounded assessment

For each question, provide:
- The question text
- {options_per_question} possible answers
- The index (0-based) of the correct answer

Format your response as a JSON array of objects, where each object follows this structure:
{{
    "question": "The question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 2  // indicating the 3rd option (0-indexed)
}}

Only include the JSON array in your response, no other text or formatting."""

            # Prepare the user prompt
            user_prompt = f"""Please create a quiz about {topic} based on the following document content:

{document_content}

Remember to focus only on the topic "{topic}" and create {num_questions} multiple-choice questions with {options_per_question} options each, following the format specified in your instructions.
"""

            # Prepare the API request
            headers = {
                'Content-Type': 'application/json',
                'api-key': self.openai_api_key
            }

            payload = {
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.7,
                'top_p': 0.95,
                'max_tokens': 2000,
                'stream': False
            }

            # Make the request to Azure OpenAI
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            # Extract the generated content
            generated_content = result['choices'][0]['message']['content']

            # Parse the JSON response to get quiz questions
            try:
                # Extract JSON part if there's any prefix or suffix text
                if '```json' in generated_content:
                    generated_content = generated_content.split('```json')[1].split('```')[0].strip()
                elif '```' in generated_content:
                    generated_content = generated_content.split('```')[1].strip()

                quiz_questions = json.loads(generated_content)

                # Validate the structure of each question
                validated_questions = []
                for q in quiz_questions:
                    if (isinstance(q, dict) and
                        'question' in q and
                        'options' in q and
                        'correct_answer' in q and
                        isinstance(q['options'], list) and
                        isinstance(q['correct_answer'], int) and
                        0 <= q['correct_answer'] < len(q['options'])):
                        validated_questions.append(q)
                    else:
                        logger.warning(f"Skipping invalid question format: {q}")

                return validated_questions

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse quiz questions JSON: {str(e)}")
                logger.error(f"Generated content: {generated_content}")
                return []

        except Exception as e:
            logger.error(f"Error in OpenAI quiz generation: {str(e)}")
            return []

    def score_quiz(self, user_answers, quiz_data):
        """
        Score a completed quiz based on user answers and original quiz data.

        Args:
            user_answers: List of integers representing the user's selected answers
            quiz_data: Original quiz data with questions, options and correct answers

        Returns:
            Dictionary with scoring results including score, total, and detailed results
        """
        try:
            if len(user_answers) != len(quiz_data):
                raise ValueError("Number of user answers doesn't match number of questions")

            score = 0
            results = []

            for i, (user_answer, question_data) in enumerate(zip(user_answers, quiz_data)):
                is_correct = user_answer == question_data['correct_answer']
                if is_correct:
                    score += 1

                result = {
                    'question': question_data['question'],
                    'options': question_data['options'],
                    'correctAnswer': question_data['correct_answer'],
                    'userAnswer': user_answer,
                    'isCorrect': is_correct
                }
                results.append(result)

            return {
                'score': score,
                'total': len(quiz_data),
                'results': results
            }

        except Exception as e:
            logger.error(f"Error scoring quiz: {str(e)}")
            raise