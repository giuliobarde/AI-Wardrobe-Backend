import os
import logging
from typing import List, Union
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise EnvironmentError("OPENAI_API_KEY environment variable not set")


class LLMClient:
    """Interface for language model interactions"""
    
    def __init__(self, api_key: str = None, model_name: str = "gpt-3.5-turbo"):
        """Initialize LLM client with appropriate configuration"""
        self.api_key = api_key or openai_api_key
        self.model_name = model_name
        self.llm = self._create_llm(temperature=0.5)
    
    def _create_llm(self, temperature: float) -> ChatOpenAI:
        """Create a new LLM instance with the given temperature"""
        return ChatOpenAI(
            openai_api_key=self.api_key,
            temperature=temperature,
            top_p=1,
            model_name=self.model_name
        )
    
    def with_temperature(self, temperature: float) -> None:
        """Update the LLM with a new temperature setting"""
        self.llm = self._create_llm(temperature)
    
    def invoke(self, messages: List[Union[SystemMessage, HumanMessage]]) -> str:
        """Send a request to the language model and return the response"""
        try:
            response = self.llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            logger.error("Error invoking LLM: %s", e)
            raise


# Create a singleton LLM client
llm_client = LLMClient()