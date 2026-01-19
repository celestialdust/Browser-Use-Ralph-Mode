"""Configuration and model setup for browser automation agent."""

import os
import warnings
from typing import Literal, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()


class Config:
    """Configuration for the browser automation agent."""

    # DEPRECATED: Azure OpenAI settings are deprecated and will be removed in a future version.
    # Please migrate to using direct OpenAI API (USE_AZURE=false) with OPENAI_API_KEY.
    # These settings are kept for backwards compatibility only.
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "https://DM-OPENAI-DEV-SWEDEN.openai.azure.com")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    OPENAI_API_VERSION: str = os.getenv("OPENAI_API_VERSION", "2025-01-01-preview")
    DEPLOYMENT_NAME: str = os.getenv("DEPLOYMENT_NAME", "gsds-gpt-5")

    # OpenAI settings (for direct OpenAI API usage)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")

    # Reasoning API settings
    REASONING_ENABLED: bool = os.getenv("REASONING_ENABLED", "true").lower() == "true"
    REASONING_EFFORT: str = os.getenv("REASONING_EFFORT", "medium")
    REASONING_SUMMARY: str = os.getenv("REASONING_SUMMARY", "detailed")

    # DEPRECATED: USE_AZURE is deprecated along with Azure settings above.
    # Use Azure endpoint by default (set to false for direct OpenAI API)
    USE_AZURE: bool = os.getenv("USE_AZURE", "true").lower() == "true"

    # Model parameters
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "1.0"))
    
    # Browser streaming settings
    BASE_STREAM_PORT: int = int(os.getenv("AGENT_BROWSER_STREAM_PORT", "9223"))
    MAX_PORT_OFFSET: int = 1000

    # CDP (Chrome DevTools Protocol) settings
    # When enabled, connects to an existing browser instead of launching a new one
    # Start Chrome with: google-chrome --remote-debugging-port=9222
    USE_CDP: bool = os.getenv("USE_CDP", "false").lower() == "true"
    CDP_PORT: int = int(os.getenv("CDP_PORT", "9222"))
    
    # Ralph Mode settings
    DEFAULT_MAX_ITERATIONS: int = 5

    # Tool categorization - Since the agent runs in a sandboxed browser,
    # approval is not needed for any actions. All tools are auto-approved.
    # For advanced agent-browser commands not exposed as tools, the agent
    # can use the Bash tool after consulting agent-browser --help.
    APPROVAL_REQUIRED_TOOLS = set()  # Empty - no approvals needed in sandbox

    AUTO_APPROVED_TOOLS = {
        # All browser tools are auto-approved
        "browser_navigate",
        "browser_snapshot",
        "browser_click",
        "browser_fill",
        "browser_type",
        "browser_press_key",
        "browser_screenshot",
        "browser_wait",
        "browser_close",
        "browser_back",
        "browser_forward",
        "browser_reload",
        "browser_get_info",
        "browser_is_visible",
        "browser_is_enabled",
        "browser_is_checked",
        "browser_console",
    }
    
    @classmethod
    def validate(cls, use_azure: Optional[bool] = None) -> None:
        """Validate required configuration.

        Args:
            use_azure: If True, validate Azure config. If False, validate OpenAI config.
                       If None, uses Config.USE_AZURE.
        """
        check_azure = use_azure if use_azure is not None else cls.USE_AZURE

        if check_azure:
            if not cls.AZURE_OPENAI_ENDPOINT or not cls.AZURE_OPENAI_API_KEY:
                raise ValueError(
                    "Missing required environment variables: "
                    "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set in .env"
                )
        else:
            if not cls.OPENAI_API_KEY:
                raise ValueError(
                    "Missing required environment variable: "
                    "OPENAI_API_KEY must be set in .env"
                )


def get_llm(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    reasoning_enabled: Optional[bool] = None,
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None,
    reasoning_summary: Optional[Literal["brief", "detailed"]] = None,
    use_azure: Optional[bool] = None,
    endpoint: Optional[str] = None,
    streaming: bool = True,
) -> ChatOpenAI:
    """Get configured ChatOpenAI LLM instance with reasoning API support.

    Uses ChatOpenAI for both Azure OpenAI and direct OpenAI API.
    When USE_AZURE=true (default), configures ChatOpenAI to use Azure's
    /openai/v1/ endpoint with the Responses API.

    Args:
        api_key: API key (defaults based on USE_AZURE setting)
        model: Model/deployment name (defaults based on USE_AZURE setting)
        temperature: Temperature setting (defaults to Config.TEMPERATURE)
        reasoning_enabled: Enable reasoning API (defaults to Config.REASONING_ENABLED)
        reasoning_effort: Reasoning effort level (defaults to Config.REASONING_EFFORT)
        reasoning_summary: Summary type (defaults to Config.REASONING_SUMMARY)
        use_azure: Use Azure OpenAI endpoint (defaults to Config.USE_AZURE)
        endpoint: Azure OpenAI endpoint (defaults to Config.AZURE_OPENAI_ENDPOINT)
        streaming: Enable streaming (defaults to True)

    Returns:
        ChatOpenAI: Configured language model instance with reasoning support
    """
    _use_azure = use_azure if use_azure is not None else Config.USE_AZURE

    Config.validate(use_azure=_use_azure)

    # Get reasoning configuration
    _reasoning_enabled = (
        reasoning_enabled if reasoning_enabled is not None else Config.REASONING_ENABLED
    )
    _reasoning_effort = reasoning_effort if reasoning_effort is not None else Config.REASONING_EFFORT
    _reasoning_summary = reasoning_summary if reasoning_summary is not None else Config.REASONING_SUMMARY
    _temperature = temperature if temperature is not None else Config.TEMPERATURE

    # Build reasoning configuration if enabled
    reasoning_config = None
    if _reasoning_enabled:
        reasoning_config = {
            "effort": _reasoning_effort,
            "summary": _reasoning_summary,
        }

    if _use_azure:
        # Emit deprecation warning for Azure usage
        warnings.warn(
            "Azure OpenAI configuration is deprecated and will be removed in a future version. "
            "Please migrate to direct OpenAI API by setting USE_AZURE=false and OPENAI_API_KEY.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Use ChatOpenAI with Azure's /openai/v1/ endpoint for Responses API
        _endpoint = endpoint or Config.AZURE_OPENAI_ENDPOINT
        _api_key = api_key or Config.AZURE_OPENAI_API_KEY
        _model = model or Config.DEPLOYMENT_NAME

        # Construct Azure v1 base URL (must end with /openai/v1/)
        base_url = f"{_endpoint.rstrip('/')}/openai/v1/"

        return ChatOpenAI(
            model=_model,
            api_key=_api_key,
            base_url=base_url,
            # Azure requires api-key header for the v1 path
            default_headers={"api-key": _api_key},
            # Responses API parameters
            use_responses_api=_reasoning_enabled,
            reasoning=reasoning_config,
            include=["reasoning.encrypted_content"] if _reasoning_enabled else None,
            temperature=_temperature,
            streaming=streaming,
        )
    else:
        # Use ChatOpenAI with direct OpenAI API
        _api_key = api_key or Config.OPENAI_API_KEY
        _model = model or Config.OPENAI_MODEL

        return ChatOpenAI(
            model=_model,
            api_key=_api_key,
            use_responses_api=_reasoning_enabled,
            reasoning=reasoning_config,
            include=["reasoning.encrypted_content"] if _reasoning_enabled else None,
            temperature=_temperature,
            streaming=streaming,
        )
