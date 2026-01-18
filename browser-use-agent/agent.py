#!/usr/bin/env python
"""CLI entry point for browser automation agent."""

import sys
import argparse
from browser_use_agent import create_browser_agent, run_ralph_mode
from browser_use_agent.state import create_initial_state
from langchain_core.messages import HumanMessage
import uuid


def print_result(result: dict) -> None:
    """Pretty print agent result."""
    print("\n" + "="*60)
    print("RESULT:")
    print("="*60)
    
    # Print final messages
    messages = result.get("messages", [])
    for msg in messages[-3:]:  # Show last 3 messages
        role = getattr(msg, "type", "unknown")
        content = getattr(msg, "content", "")
        content_preview = content[:500] + "..." if len(content) > 500 else content
        print(f"\n[{role.upper()}]: {content_preview}")
    
    # Print todos if any
    todos = result.get("todos", [])
    if todos:
        print(f"\n\nTODOS ({len(todos)} items):")
        for i, todo in enumerate(todos, 1):
            status = todo.get("status", "unknown")
            content = todo.get("content", "")
            print(f"  {i}. [{status}] {content}")
    
    # Print browser session info
    browser_session = result.get("browser_session")
    if browser_session:
        print(f"\n\nBROWSER SESSION:")
        print(f"  Session ID: {browser_session.get('sessionId')}")
        print(f"  Stream URL: {browser_session.get('streamUrl')}")
        print(f"  Active: {browser_session.get('isActive')}")
    
    print("\n" + "="*60 + "\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Browser Automation Agent with Ralph Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard mode
  python agent.py --task "Navigate to example.com and get the title"
  
  # Ralph mode with iterations
  python agent.py --ralph --task "Research browser automation tools" --iterations 3
  
  # Custom thread ID
  python agent.py --thread-id my-session --task "Fill out a form"
        """
    )
    
    parser.add_argument(
        "--task",
        type=str,
        required=True,
        help="Task description for the agent"
    )
    parser.add_argument(
        "--ralph",
        action="store_true",
        help="Enable Ralph Mode (iterative refinement)"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Max iterations for Ralph Mode (default: 5)"
    )
    parser.add_argument(
        "--thread-id",
        type=str,
        help="Thread ID for session (auto-generated if not provided)"
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"Browser Automation Agent")
    print(f"Mode: {'Ralph Mode' if args.ralph else 'Standard'}")
    print(f"Task: {args.task}")
    print(f"{'='*60}\n")
    
    try:
        # Create agent
        graph = create_browser_agent()
        
        if args.ralph:
            # Run in Ralph Mode
            result = run_ralph_mode(
                task=args.task,
                max_iterations=args.iterations,
                thread_id=args.thread_id,
                agent=graph
            )
        else:
            # Standard mode
            thread_id = args.thread_id or str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            initial_state = create_initial_state(thread_id)
            initial_state["messages"] = [HumanMessage(content=args.task)]
            
            print(f"Thread ID: {thread_id}\n")
            result = graph.invoke(initial_state, config)
        
        # Print results
        print_result(result)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
