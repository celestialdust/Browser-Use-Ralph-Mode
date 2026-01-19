import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 1. Manually load the environment variables
load_dotenv()

# Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME") or "gsds-gpt-5"
TEMPERATURE = float(os.getenv("TEMPERATURE", "1.0"))

def stream_with_reasoning(prompt: str):
    # 2. Construct the exact v1 base URL Azure expects for reasoning
    # This MUST end in /openai/v1/ (with the trailing slash)
    base_url = f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/v1/"
    
    # 3. Initialize ChatOpenAI with the Responses API enabled
    llm = ChatOpenAI(
        model=DEPLOYMENT_NAME,
        api_key=AZURE_OPENAI_API_KEY, 
        base_url=base_url,
        # IMPORTANT: Azure needs the api-key header for the v1 path
        default_headers={"api-key": AZURE_OPENAI_API_KEY},
        
        # Responses API parameters
        use_responses_api=True,
        reasoning={"effort": "medium", "summary": "detailed"},
        include=["reasoning.encrypted_content"],
        
        temperature=TEMPERATURE,
        streaming=True
    )

    print(f"Targeting Endpoint: {base_url}")
    print("--- Reasoning Process ---")
    
    content_started = False
    try:
        for chunk in llm.stream([HumanMessage(content=prompt)]):
            # Capture and print the 'Thinking' process
            if "reasoning" in chunk.additional_kwargs:
                reasoning = chunk.additional_kwargs["reasoning"]
                summary = reasoning.get("summary", "")
                
                # In 2026 SDKs, this is often a list of content blocks
                if isinstance(summary, list) and len(summary) > 0:
                    summary = summary[0].get("text", "")
                
                if summary:
                    # Gray color for thoughts
                    print(f"\033[90m{summary}\033[0m", end="", flush=True)

            # Capture and print the final code/answer
            if chunk.content:
                if not content_started:
                    print("\n\n--- Final Response ---")
                    content_started = True
                print(chunk.content, end="", flush=True)
                
    except Exception as e:
        print(f"\n\n[ERROR]: {e}")

if __name__ == "__main__":
    # Test query relevant to your interest in SMC/ICT trading
    user_query = "Define a Liquidity Sweep and explain how to identify a Change of Character (CHoCH) using Python logic."
    stream_with_reasoning(user_query)
