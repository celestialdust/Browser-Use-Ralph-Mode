"""FastAPI server wrapper for browser-use agent (optional alternative to LangGraph deployment)."""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import asyncio
import uuid
from agent import graph, create_agent_state
from stream_manager import stream_manager

app = FastAPI(title="Browser-Use Agent API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (use Redis/DB for production)
sessions: Dict[str, Dict[str, Any]] = {}


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    thread_id: str
    response: str
    browser_session: Optional[Dict[str, Any]] = None
    todos: List[Dict[str, Any]] = []
    files: Dict[str, str] = {}
    approval_required: bool = False
    approval_queue: List[Dict[str, Any]] = []


class ApprovalRequest(BaseModel):
    """Request model for approval endpoint."""
    thread_id: str
    command_id: str
    approved: bool


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "browser-use-agent"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the agent and get a response.
    
    Args:
        request: Chat request with message and optional thread_id
        
    Returns:
        ChatResponse: Agent's response with state
    """
    try:
        # Get or create thread_id
        thread_id = request.thread_id or str(uuid.uuid4())
        
        # Get or create session
        if thread_id not in sessions:
            sessions[thread_id] = create_agent_state(thread_id)
        
        state = sessions[thread_id]
        
        # Add user message to state
        from langchain_core.messages import HumanMessage
        state["messages"].append(HumanMessage(content=request.message))
        
        # Run agent
        config = {"configurable": {"thread_id": thread_id}}
        result = None
        
        for event in graph.stream(state, config):
            result = event
            # Update session state
            if isinstance(event, dict):
                for key, value in event.items():
                    if key in state:
                        state[key] = value
        
        # Extract response
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        response_text = last_message.content if last_message else "No response"
        
        # Check if approval is required
        approval_queue = state.get("approval_queue", [])
        has_approval = len(approval_queue) > 0
        
        # Get browser session info
        browser_session = state.get("browser_session")
        
        return ChatResponse(
            thread_id=thread_id,
            response=response_text,
            browser_session=browser_session,
            todos=state.get("todos", []),
            files=state.get("files", {}),
            approval_required=has_approval,
            approval_queue=approval_queue,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/approve")
async def approve_command(request: ApprovalRequest):
    """
    Approve or reject a pending browser command.
    
    Args:
        request: Approval request with thread_id, command_id, and approval decision
        
    Returns:
        dict: Result of approval
    """
    try:
        if request.thread_id not in sessions:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        state = sessions[request.thread_id]
        approval_queue = state.get("approval_queue", [])
        
        # Find and remove the command from queue
        command = None
        for i, cmd in enumerate(approval_queue):
            if cmd.get("id") == request.command_id:
                command = approval_queue.pop(i)
                break
        
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")
        
        if request.approved:
            # Continue execution with approval
            config = {"configurable": {"thread_id": request.thread_id}}
            
            # Resume from interrupt
            result = graph.invoke(None, config, interrupt=False)
            
            return {
                "status": "approved",
                "command_id": request.command_id,
                "result": "Command executed"
            }
        else:
            return {
                "status": "rejected",
                "command_id": request.command_id,
                "result": "Command cancelled"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/threads/{thread_id}/stream")
async def get_stream_url(thread_id: str):
    """
    Get the browser stream WebSocket URL for a thread.
    
    Args:
        thread_id: Thread identifier
        
    Returns:
        dict: Stream URL
    """
    if stream_manager.is_active(thread_id):
        stream_url = stream_manager.get_stream_url(thread_id)
        return {"stream_url": stream_url, "active": True}
    else:
        return {"stream_url": None, "active": False}


@app.delete("/threads/{thread_id}")
async def close_thread(thread_id: str):
    """
    Close a thread and cleanup resources.
    
    Args:
        thread_id: Thread identifier
        
    Returns:
        dict: Closure status
    """
    if thread_id in sessions:
        # Close browser session
        from browser_skills import browser_close
        try:
            browser_close.invoke({"thread_id": thread_id})
        except:
            pass
        
        # Remove from sessions
        del sessions[thread_id]
        
        # Release stream port
        stream_manager.release_port(thread_id)
        
        return {"status": "closed", "thread_id": thread_id}
    else:
        raise HTTPException(status_code=404, detail="Thread not found")


@app.get("/threads")
async def list_threads():
    """
    List all active threads.
    
    Returns:
        dict: List of thread IDs and their status
    """
    threads = []
    for thread_id, state in sessions.items():
        threads.append({
            "thread_id": thread_id,
            "message_count": len(state.get("messages", [])),
            "has_browser": state.get("browser_session") is not None,
            "todos_count": len(state.get("todos", [])),
        })
    
    return {"threads": threads, "count": len(threads)}


if __name__ == "__main__":
    import uvicorn
    
    print("Starting Browser-Use Agent Server...")
    print("API will be available at: http://localhost:8000")
    print("API docs available at: http://localhost:8000/docs")
    print("\nNote: Make sure agent-browser is installed globally:")
    print("  npm install -g agent-browser")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
