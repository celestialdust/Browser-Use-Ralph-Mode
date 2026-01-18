"""Configuration and model setup for browser automation agent."""

import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

# Load environment variables
load_dotenv()


class Config:
    """Configuration for the browser automation agent."""
    
    # Azure OpenAI settings
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "https://DM-OPENAI-DEV-SWEDEN.openai.azure.com")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    OPENAI_API_VERSION: str = os.getenv("OPENAI_API_VERSION", "2025-01-01-preview")
    DEPLOYMENT_NAME: str = os.getenv("DEPLOYMENT_NAME", "gsds-gpt-5")
    
    # Model parameters
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "1.0"))
    
    # Browser streaming settings
    BASE_STREAM_PORT: int = int(os.getenv("AGENT_BROWSER_STREAM_PORT", "9223"))
    MAX_PORT_OFFSET: int = 1000
    
    # Ralph Mode settings
    DEFAULT_MAX_ITERATIONS: int = 5
    
    # Tool categorization
    APPROVAL_REQUIRED_TOOLS = {
        "browser_click",
        "browser_fill",
        "browser_type",
        "browser_navigate",
        "browser_submit",
        "browser_press_key",
        "browser_eval",
    }
    
    AUTO_APPROVED_TOOLS = {
        "browser_snapshot",
        "browser_get_info",
        "browser_screenshot",
        "browser_is_visible",
        "browser_is_enabled",
        "browser_is_checked",
        "browser_get_url",
        "browser_get_title",
    }
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.AZURE_OPENAI_ENDPOINT or not cls.AZURE_OPENAI_API_KEY:
            raise ValueError(
                "Missing required environment variables: "
                "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set in .env"
            )


def get_llm(
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
    api_version: Optional[str] = None,
    deployment_name: Optional[str] = None,
    temperature: Optional[float] = None,
) -> AzureChatOpenAI:
    """Get configured Azure OpenAI LLM instance.
    
    Args:
        endpoint: Azure OpenAI endpoint (defaults to Config.AZURE_OPENAI_ENDPOINT)
        api_key: API key (defaults to Config.AZURE_OPENAI_API_KEY)
        api_version: API version (defaults to Config.OPENAI_API_VERSION)
        deployment_name: Deployment name (defaults to Config.DEPLOYMENT_NAME)
        temperature: Temperature setting (defaults to Config.TEMPERATURE)
        
    Returns:
        AzureChatOpenAI: Configured language model instance
    """
    Config.validate()
    
    return AzureChatOpenAI(
        azure_endpoint=endpoint or Config.AZURE_OPENAI_ENDPOINT,
        api_key=api_key or Config.AZURE_OPENAI_API_KEY,
        api_version=api_version or Config.OPENAI_API_VERSION,
        deployment_name=deployment_name or Config.DEPLOYMENT_NAME,
        temperature=temperature if temperature is not None else Config.TEMPERATURE,
    )
