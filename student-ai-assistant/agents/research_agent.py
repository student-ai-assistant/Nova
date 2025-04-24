
import os

from dotenv import load_dotenv
load_dotenv('../.env')


import os
from getpass import getpass
import urllib3
import json
import os

urllib3.disable_warnings()


def get_api_key(key_name):
    if key_name in os.environ:
        return os.environ[key_name]
    else:
        key = getpass(f'Enter {key_name}: ')
        os.environ[key_name] = key
        return key


LLAMA_CLOUD_API_KEY = get_api_key('LLAMA_CLOUD_API_KEY')
TOGETHER_API_KEY = get_api_key('TOGETHER_API_KEY')
GROQ_API_KEY = get_api_key('GROQ_API_KEY')


NUM_SEARCH_RESULTS = 10

SEMANTIC_API_MAX_RETRIES = 10

PAPER_SAVE_DIR = 'papers'
REMOVE_REFERENCE_SECTION_FROM_PDF = False
REFERENCE_TITLES = ["references", "bibliography"]

USE_CACHE_FOR_PDF_PARSING = True
USE_CACHE_FOR_SUMMARIZATION = True



from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(
    model="llama3-70b-8192",
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ["GROQ_API_KEY"],
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": False,
        "family": "unknown",
    },
)


# model_client_together = OpenAIChatCompletionClient(
#     model="meta-llama/Llama-Vision-Free",
#     base_url="https://api.together.xyz/v1",
#     max_tokens=10000,
#     api_key=TOGETHER_API_KEY,
#     model_info={
#         "vision": False,
#         "function_calling": True,
#         "json_output": False,
#         "functional_calling": True,
#         "family": "unknown",
#     }
# )







from autogen_ext.models.openai import AzureOpenAIChatCompletionClient


model_client_bm = AzureOpenAIChatCompletionClient(
    model="gpt-4o-mini",
    azure_deployment="gpt-4o-mini",
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-12-01-preview",
    model_info={
        "json_output": False,
        "function_calling": True,
        "vision": False,
        "family": "unknown",
        "structured_output": False,
    },
)



import requests
import fitz
import time



def download_pdf(session, url: str, path: str):
    headers = { 'user-agent': 'requests/2.0.0'}
    with session.get(url, headers=headers, stream=True, verify=False) as response:
        response.raise_for_status()
        if response.headers['content-type'] != 'application/pdf':
            raise Exception('The response is not a pdf')

        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    return None


def query_semantic_scholar(query: str, limit: int, ntries:int = None):
    if ntries is None:
        ntries = int(SEMANTIC_API_MAX_RETRIES)
    if ntries <= 0:
        print("Semantic Scholar API rate limit exceeded, exiting...")
        return [] 

    url = (
        f"https://api.semanticscholar.org/graph/v1/paper/search?"
        f"query={query}&openAccessPdf&limit={limit}&fields=title,year,abstract,isOpenAccess,openAccessPdf"
    )
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("data", [])
    elif response.status_code == 429:
        #print("Semantic Scholar API rate limit exceeded, retrying...")
        time.sleep(SEMANTIC_API_MAX_RETRIES - ntries)
        return query_semantic_scholar(query, limit, ntries - 1)
    else:
        print("Semantic Scholar API error:", response.status_code)
        return []



def remove_reference_section(pdf_path: str, out_path: str):
    doc = fitz.open(pdf_path)    

    def get_reference_page_number(doc):
        toc = doc.get_toc()
        for item in reversed(toc):
            title = item[1].lower()
            if any(ref_title in title for ref_title in REFERENCE_TITLES):
                return item[2]
        return None

    ref_num = get_reference_page_number(doc)
    if ref_num is None:
        doc.save(out_path)
        print("Couldn't locate reference section")
        return None

    # remove pages after the reference section
    ref_page = get_reference_page_number(doc) - 1 # since pages are 1-indexed
    page_to_remove = ref_page + 1 # since reference can start from middle of the page
    # print("Reference page:", page_to_remove)
    if ref_page:
        # print(f"Deleting pages from {page_to_remove+1} to {doc.page_count}")
        doc.delete_pages(page_to_remove, doc.page_count - 1)

    doc.save(out_path)
    doc.close()
    return None


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    # Define the set of invalid characters (Windows)
    invalid_chars = r'[<>:"/\\|?*]'
    # Replace each invalid character with the replacement (e.g., underscore)
    return re.sub(invalid_chars, replacement, filename)


def get_papers(query: str, num_papers: int):
    '''
    Downloads papers from Semantic Scholar API
    Args:
        query: str: search query
        num_papers: int: number of papers to download
    Returns:
        papers: list of dictionaries containing paper metadata
    '''
    papers = []
    
    for paper in query_semantic_scholar(query, NUM_SEARCH_RESULTS):
        try:
            fname = paper['title'].replace(' ', '_') 
            fname = sanitize_filename(fname)
            paper_folder = os.path.join(PAPER_SAVE_DIR, fname)
            os.makedirs(paper_folder, exist_ok=True)
            out_path = os.path.join(paper_folder, f"paper.pdf")
            download_pdf(requests.Session(), paper['openAccessPdf']['url'], out_path)

        except Exception as e:
            os.rmdir(paper_folder)
            print(f"Failed to download {paper['title']}: {e}")
            continue

        if REMOVE_REFERENCE_SECTION_FROM_PDF:
            out_path_no_ref = os.path.join(paper_folder, f"paper_no_ref.pdf")
            remove_reference_section(out_path, out_path_no_ref)


        papers.append({
            "title": paper["title"],
            "year": paper["year"],
            "abstract": paper["abstract"],
            "pdf_path": out_path,
        }
        )
        print(f"Downloaded : {paper['title']}")
        if len(papers) == num_papers:
            break

    print(f"Downloaded {len(papers)} papers")
    return papers






from llama_cloud_services import LlamaParse
import asyncio

parser = LlamaParse(
    api_key=LLAMA_CLOUD_API_KEY,
    result_type="markdown",  # "markdown" and "text" are available
    num_workers=4,  # if multiple files passed, split in `num_workers` API calls
    verbose=True,
    language="en",  # Optionally you can define a language, default=en
)


async def parse_pdf(pdf_path):
    parsed_data = await parser.aload_data(pdf_path)
    return parsed_data



async def parse_all_papers(papers):
    tasks = [parse_pdf(paper["pdf_path"]) for paper in papers]  # Create tasks
    results = await asyncio.gather(*tasks)  # Run all tasks in parallel
    
    # Store results back in papers
    for paper, parsed_data in zip(papers, results):
        content = '\n'.join(doc.text for doc in parsed_data)
        paper["parsed_data"] = content

    return papers






import re
def clean_text(text):
    # replace links with "<LINK>" token
    text = re.sub(r'http\S+', '<LINK>', text)
    
    # remove the references section
    for ref_title in REFERENCE_TITLES:
        ref_start = text.lower().find(f'# {ref_title.lower()}')
        if ref_start != -1:
            text = text[:ref_start]

    # remove anything in square brackets
    text = re.sub(r'\[.*?\]', '', text)

    # remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    return text




from autogen_core.models import AssistantMessage, UserMessage, SystemMessage
from autogen_core import (
    MessageContext,
    RoutedAgent,
    TopicId,
    FunctionCall,
    message_handler,
    type_subscription,
)


from autogen_core.models import ChatCompletionClient
from autogen_core.tools import FunctionTool
from autogen_core import CancellationToken
from autogen_core.models import FunctionExecutionResult
from autogen_core.tools import FunctionTool




from dataclasses import dataclass, field

@dataclass
class Message:
    display_msg: str
    hidden_content: dict = field(default_factory=dict)



DEBUG = False

def log_msg(agent, msg: Message):
    print(f"{'-'*80}\n{agent.id.type}:")
    if DEBUG:
        print(f"{msg.display_msg}\n")



search_topic_type = "SearchAgent"
paper_summarizer = "SummarizerAgent"
report_generator_type = "ReportGeneratorAgent"
user_agent_type = "UserAgent"
feedback_handler_agent_type = "FeedbackHandlerAgent"




SEARCH_AGENT_PROMPT = (
"You are an agent in a multi-agent system designed for generating literature review. "
"Your task is to refine the literature review topic provided by the user for a better search on semantic scholar. "
"When provided with a literature review topic by the user and number of papers to search. "
"You should refine the topic by fixing typos, expanding abbreviations, and adding relevant synonyms. "
"You have access to the Semantic Scholar API to search for papers on the refined topic. "
"Once you have refined the topic, you should call the Semantic Scholar API to search for papers on the refined topic. "
)


search_papers_tool = FunctionTool(
    func=get_papers,
    name="search_papers",
    description="Search for papers on a given topic using Semantic Scholar API"
)

    

@type_subscription(topic_type=search_topic_type)
class SearchAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A search agent")
        self._system_message = SystemMessage(content=SEARCH_AGENT_PROMPT)
        self._model_client = model_client
        self._search_papers_tool = search_papers_tool

    @message_handler
    async def on_message(self, message: Message, ctx: MessageContext) -> None:
        prompt = message.display_msg
        llm_result = await self._model_client.create(
            messages=[self._system_message, UserMessage(content=prompt, source=self.id.key)],
            cancellation_token=ctx.cancellation_token,
            tools=[self._search_papers_tool],
        )
        if isinstance(llm_result.content, str):
            log_msg(self, Message(display_msg=llm_result.content))
            return None
        
        papers, arguments = await self._handle_tool_call(llm_result)
        
        refined_title = arguments['query']
        num_papers = len(papers)
        message_to_report_generator = Message(
            display_msg = f"Found {num_papers} papers on the topic '{refined_title}'",
            hidden_content = {'num_papers': num_papers }
        )
        log_msg(self, message_to_report_generator)
        await self.publish_message(message_to_report_generator, topic_id=TopicId(report_generator_type, source=self.id.key))
        
        msg_tasks = []
        for paper in papers:
            message_to_summarizer = Message(
                display_msg= f'PDF for the paper "{paper["title"]}" is saved at path - "{paper["pdf_path"]}"',
                hidden_content = {'pdf_path': paper["pdf_path"], 'title': paper["title"] }
            )
            log_msg(self, message_to_summarizer)
            tsk = self.publish_message(message_to_summarizer, topic_id=TopicId(paper_summarizer, source=self.id.key))
            msg_tasks.append(tsk)

        await asyncio.gather(*msg_tasks)
        return None


    # Refer - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/components/tools.html#tool-equipped-agent
    async def _handle_tool_call(self, llm_result):
        if not( isinstance(llm_result.content, list) and all(isinstance(call, FunctionCall) for call in llm_result.content) ):
            raise RuntimeError("Not a valid tool call")

        if len(llm_result.content) != 1:
            raise ValueError("Expected a single tool call")
        
        tool_call = llm_result.content[0]
        if tool_call.name != self._search_papers_tool.name:
            raise ValueError(f'Unexpected tool call: {tool_call.name}')
        
        arguments = json.loads(tool_call.arguments)
        result = await self._search_papers_tool.run_json(arguments, CancellationToken())
        return result, arguments
        



SUMMARIZER_AGENT_PROMPT = (
"You are an agent in a multi-agent system designed for generating literature review. "
"Your task is to provide a comprehensive summary of a technical paper in less than 500 words. "
"The summary you provide will be used by another agent responsible for synthesizing summaries from related papers to generate a literature review report. "
"Therefore, ensure that the summary you write is informative enough to be used in a literature review. "
)


async def parse_pdf_and_save(pdf_path: str):
    dir_path = os.path.dirname(pdf_path)
    out_path = os.path.join(dir_path, "parsed_data.md")

    if USE_CACHE_FOR_PDF_PARSING and os.path.exists(out_path):
        with open(out_path, 'r') as f:
            return f.read()
        

    parsed_data = await parser.aload_data(pdf_path)
    content = '\n'.join(doc.text for doc in parsed_data)
    content = clean_text(content)
    with open(out_path, 'w') as f:
        f.write(content)

    return content



@type_subscription(topic_type=paper_summarizer)
class SummarizerAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A paper summarizer agent")
        self._system_message = SystemMessage(content=SUMMARIZER_AGENT_PROMPT)
        self._model_client = model_client


    @message_handler
    async def on_message(self, message: Message, ctx: MessageContext) -> None:
        try:
            pdf_path = message.hidden_content['pdf_path']
            title = message.hidden_content['title']
        except KeyError as e:
            print(f"Invalid message received in {self.id.type}: {message.display_msg}")
            raise e
        
        summary_path = os.path.join(os.path.dirname(pdf_path), "summary.md")

        if USE_CACHE_FOR_SUMMARIZATION and os.path.exists(summary_path):
            pass
        else:
            content = await parse_pdf_and_save(pdf_path)
            content = f"Summarize the paper titled '{title}.'\n Below is the content - {content}"
            llm_result = await self._model_client.create(
                messages=[self._system_message, UserMessage(content=content, source=self.id.key)],
                cancellation_token=ctx.cancellation_token,
            )

            summary = llm_result.content
            assert isinstance(summary, str)

        
            with open(summary_path, 'w') as f:
                f.write(summary)

        message_to_reporter = Message(
            display_msg = f'Summary for the paper "{title}" is saved at path - "{summary_path}"',
            hidden_content = {'summary_path': summary_path, 'title': title}
        )
        log_msg(self, message_to_reporter)
        await self.publish_message(message_to_reporter, topic_id=TopicId(report_generator_type, source=self.id.key))
        return None



REPORT_GENERATOR_AGENT_PROMPT = (
"You are an agent in a multi-agent system designed for literature review. "
"You will be provided with summaries of various technical papers. "
"Your task is to create a comprehensive literature review report by combining the summaries of the papers. "
"Your goal is to synthesize the key findings, methodologies, and conclusions from each summary into a cohesive and well-structured document. "
"The report you generate should be atleast 500 words long. "
'''
Instructions
1. Introduction:
   - Begin with a brief introduction that outlines the purpose of the literature review and the scope of the technical papers being reviewed.

2. Body:
   - Organize the summaries thematically or chronologically, depending on the nature of the papers.
   - For each summary:
     - Highlight the main objectives and research questions addressed by the paper.
     - Describe the methodologies or approaches used.
     - Summarize the key findings and their significance.
     - Discuss any limitations or gaps identified in the research.
   - Ensure that each summary flows logically into the next, maintaining a coherent narrative throughout the report.

3. Comparison and Analysis:
   - Compare and contrast the findings across the different papers.
   - Identify common themes, trends, or disagreements among the studies.
   - Analyze how the findings contribute to the broader field of study.

4. Conclusion:
   - Summarize the overall insights gained from the literature review.
   - Suggest areas for future research based on the identified gaps or limitations.
   - Provide a concluding statement that ties back to the purpose of the review.

5. Formatting:
   - Use clear headings and subheadings to structure the report.
   - Cite the original papers appropriately within the text.
   - Ensure the language is formal and suitable for an academic audience.

Example Structure:
- Introduction
- Methodologies and Approaches
- Key Findings
- Comparative Analysis
- Conclusion and Future Directions
- References

Note:
- Avoid plagiarism by paraphrasing the summaries and adding your own analytical insights.
- Maintain a consistent tone and style throughout the report.


'''
)



@type_subscription(topic_type=report_generator_type)
class ReportGeneratorAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("A paper summarizer agent")
        self._system_message = SystemMessage(content=REPORT_GENERATOR_AGENT_PROMPT)
        self._model_client = model_client
        self.num_papers = None
        self.summaries = []


    @message_handler
    async def on_message(self, message: Message, ctx: MessageContext) -> None:
        if 'num_papers' in message.hidden_content:
            num_papers = message.hidden_content['num_papers']
            self.num_papers = num_papers
            if len(self.summaries) > 0:
                raise ValueError("Summaries should be empty when num_papers is set")
            return None

        if self.num_papers is None:
            raise ValueError(f"Number of papers should be set before receiving summaries. Got: {message.display_msg}")
        
        
        title, summary_path = message.hidden_content['title'], message.hidden_content['summary_path']
        with open(summary_path, 'r') as f:
            summary = f.read()
            self.summaries.append((title, summary))

        if len(self.summaries) == self.num_papers:
            content = f'Below are the summaries of {self.num_papers} papers:\n\n'
            for title, summary in self.summaries:
                content += f'Paper: {title}\n{summary}\n\n'
                
            llm_result = await self._model_client.create(
                messages=[self._system_message, UserMessage(content=content, source=self.id.key)],
                cancellation_token=ctx.cancellation_token,
            )

            report = llm_result.content
            assert isinstance(report, str)

            report_path = os.path.join(PAPER_SAVE_DIR, "initial_report.md")
            with open(report_path, 'w') as f:
                f.write(report)

            message_to_user = Message(
                display_msg = f"Report is saved at path - {report_path}\n\n Here is the content:\n{report}",
                hidden_content = {'initial_report': report, 'report_path': report_path}
            )
            log_msg(self, message_to_user)
            await self.publish_message(Termination(reason="Report generated"), DefaultTopicId())
            # await self.publish_message(message_to_user, topic_id=TopicId(user_agent_type, source=self.id.key))
        

        return None


@type_subscription(topic_type=user_agent_type)
class UserAgent(RoutedAgent):
    def __init__(self, disp_prompt: str, to_topic_type: str) -> None:
        super().__init__("User")
        self._disp_prompt = disp_prompt
        self._to_topic_type = to_topic_type   

    @message_handler
    async def on_message(self, message: Message, ctx: MessageContext) -> None:
        user_msg = input(self._disp_prompt)
        hidden_content = message.hidden_content 
        msg = Message(display_msg=user_msg, hidden_content=hidden_content)
        log_msg(self, msg)
        await self.publish_message(msg, topic_id=TopicId(self._to_topic_type, source=self.id.key))
        return None



from autogen_core import DefaultInterventionHandler, DefaultTopicId

@dataclass
class Termination:
    reason: str


# Below class is from AutoGen tutorial -  https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/cookbook/termination-with-intervention.html#termination-using-intervention-handler
class TerminationHandler(DefaultInterventionHandler):
    def __init__(self) -> None:
        self._termination_value: Termination | None = None

    async def on_publish(self, message, *, message_context: MessageContext):
        if isinstance(message, Termination):
            self._termination_value = message
        return message

    @property
    def termination_value(self) -> Termination | None:
        return self._termination_value

    @property
    def has_terminated(self) -> bool:
        return self._termination_value is not None



FEEDBACK_HANDLER_PROMPT = (
"You are an agent in a multi-agent system designed for literature review. "
"You will be given a literature review report generated by the system and a feedback from the user on the report. "
"Your task is to handle the feedback appropriately and provide a response to the user. "
)


# Tutorial on how to maintain history of chat messages - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/custom-agents.html#using-custom-model-clients-in-custom-agents


@type_subscription(topic_type=feedback_handler_agent_type)
class FeedbackHandlerAgent(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, approve_word: str, max_message_count: int) -> None:
        super().__init__("A paper summarizer agent")
        self._system_message = SystemMessage(content=REPORT_GENERATOR_AGENT_PROMPT)
        self._model_client = model_client
        self._chat_history = []
        self.approve_word = approve_word.lower()
        self.updated_report_path = os.path.join(PAPER_SAVE_DIR, "updated_report.md")
        self.msg_count = 0
        self.max_message_count = max_message_count



    @message_handler
    async def on_message(self, message: Message, ctx: MessageContext) -> None:
        self.msg_count += 1

        user_feedback = message.display_msg
        if 'initial_report' in message.hidden_content:
            initial_report = message.hidden_content['initial_report']
            msg_content = f"Initial report:\n{initial_report}\n\n{user_feedback}"
            self._chat_history.append(UserMessage(content=msg_content, source='User'))
        else:
            self._chat_history.append(UserMessage(content=user_feedback, source='User'))


        if user_feedback.lower() == self.approve_word:
            log_msg(self, Message("Thank you for your feedback. I'm glad you found the report helpful."))
            await self.publish_message(Termination(reason="User approved the report"), DefaultTopicId())

        else:
            llm_response = await self._model_client.create(
                messages=[self._system_message] + self._chat_history,
                cancellation_token=ctx.cancellation_token,
            )
            response = llm_response.content

            with open(self.updated_report_path, 'w') as f:
                f.write(response)

            self._chat_history.append(AssistantMessage(content=response, source=self.id.key))
            log_msg(self, Message(display_msg=response, hidden_content={}))

            if self.msg_count > self.max_message_count:
                await self.publish_message(Termination(reason="Reached maximum number of messages"), DefaultTopicId())

            await self.publish_message(Message(display_msg=None, hidden_content={}), topic_id=TopicId(user_agent_type, source=self.id.key))




from autogen_core import SingleThreadedAgentRuntime





async def literature_review(user_query):
    termination_handler = TerminationHandler()
    runtime = SingleThreadedAgentRuntime(intervention_handlers=[termination_handler])
    await SearchAgent.register(
        runtime, type=search_topic_type, factory=lambda: SearchAgent(model_client=model_client)
    )

    await SummarizerAgent.register(
        runtime, type=paper_summarizer, factory=lambda: SummarizerAgent(model_client=model_client_bm)
    )
        
    await ReportGeneratorAgent.register(
        runtime, type=report_generator_type, factory=lambda: ReportGeneratorAgent(model_client=model_client_bm)
    )

    # await UserAgent.register(
    #     runtime, type=user_agent_type, factory=lambda: UserAgent(disp_prompt="Enter your feedback: ", to_topic_type=feedback_handler_agent_type)
    # )

    # MAX_FEEDBACK_MESSAGES = 5

    # await FeedbackHandlerAgent.register(
    #     runtime, type=feedback_handler_agent_type, factory=lambda: FeedbackHandlerAgent(model_client=model_client_bm, approve_word="approve", max_message_count=MAX_FEEDBACK_MESSAGES)
    # )



    runtime.start()

    await runtime.publish_message(
        Message(user_query),
        topic_id=TopicId(search_topic_type, source="default"),
    )

    await runtime.stop_when(lambda: termination_handler.has_terminated)

    return os.path.join(PAPER_SAVE_DIR, "initial_report.md")



def run_lit_review(user_msg):
    """Synchronous wrapper for the async run_journal_agent function."""
    return asyncio.run(literature_review(user_msg))


