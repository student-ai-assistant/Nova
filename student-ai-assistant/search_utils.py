"""
search_utils.py - Utility functions for Azure AI Search integration
"""

import os
import logging
from typing import Dict, Any, List, Optional
import json
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureSearchClient:
    """Class for interacting with Azure AI Search"""

    def __init__(self, endpoint: str, api_key: str, index_name: str):
        """
        Initialize the Azure Search client

        Args:
            endpoint: Azure Search endpoint URL
            api_key: Azure Search API key
            index_name: Name of the search index to use
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.index_name = index_name
        self.credential = AzureKeyCredential(api_key)
        self.search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=self.credential
        )

    def create_or_update_index(self, fields: List[Dict[str, Any]]) -> bool:
        """
        Create or update the search index

        Args:
            fields: List of field definitions for the index

        Returns:
            True if successful, False otherwise
        """
        try:
            # In a production app, use the management client to create/update the index
            # This would require more detailed field definitions
            logger.info("Index creation/update would happen here in a production app")
            return True
        except Exception as e:
            logger.error(f"Error creating/updating index: {str(e)}")
            return False

    def upload_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Upload documents to the search index

        Args:
            documents: List of document dictionaries to upload

        Returns:
            Number of documents successfully uploaded
        """
        try:
            if not documents:
                return 0

            # Upload documents in batches of 1000 (Azure Search limit)
            batch_size = 1000
            uploaded_count = 0

            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                result = self.search_client.upload_documents(documents=batch)
                succeeded = sum([1 for r in result if r.succeeded])
                uploaded_count += succeeded
                logger.info(f"Batch upload: {succeeded}/{len(batch)} succeeded")

            return uploaded_count

        except Exception as e:
            logger.error(f"Error uploading documents: {str(e)}")
            return 0

    def search(self, query: str, subject_id: str = None,
               top: int = 3, filter_condition: str = None) -> List[Dict[str, Any]]:
        """
        Search the index for documents matching the query

        Args:
            query: The search query
            subject_id: Optional subject ID to filter by
            top: Maximum number of results to return
            filter_condition: Optional additional filter condition

        Returns:
            List of search results
        """
        try:
            # Construct filter
            filters = []
            if subject_id:
                filters.append(f"subject_id eq '{subject_id}'")
            if filter_condition:
                filters.append(filter_condition)

            filter_expr = " and ".join(filters) if filters else None

            # Use basic search parameters that are supported across all versions
            results = self.search_client.search(
                search_text=query,
                filter=filter_expr,
                include_total_count=True,
                top=top
            )

            # Convert results to a list of dictionaries
            documents = []
            for result in results:
                doc_dict = {k: v for k, v in result.items()}
                documents.append(doc_dict)

            return documents

        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []

def get_relevant_context(search_client: AzureSearchClient, query: str,
                         subject_id: str, max_results: int = 3) -> str:
    """
    Get relevant context from documents based on the query

    Args:
        search_client: AzureSearchClient instance
        query: The user's question
        subject_id: ID of the subject
        max_results: Maximum number of document chunks to retrieve

    Returns:
        Concatenated relevant context as a string
    """
    try:
        # Search for relevant document chunks
        results = search_client.search(query=query, subject_id=subject_id, top=max_results)

        if not results:
            return "No relevant information found in the uploaded documents."

        # Combine the content from the results
        context_parts = []

        for i, result in enumerate(results):
            content = result.get("content", "")
            doc_name = result.get("document_name", "Unknown document")
            context_parts.append(f"Document: {doc_name}\n{content}")

        # Combine all context parts
        full_context = "\n\n---\n\n".join(context_parts)

        return full_context

    except Exception as e:
        logger.error(f"Error retrieving context: {str(e)}")
        return f"Error retrieving context: {str(e)}"