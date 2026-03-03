import asyncio
import ollama

# Configuration
MISTRAL_MODEL = "mistral-large-3:675b-cloud"  # Cloud-tagged Mistral Large 3 via Ollama

# Model options — maximised for the 256 K-context cloud model.
# num_ctx       : full 256 K context window (262 144 tokens)
# num_predict   : -1 = no output-token cap; model decides when to stop
# temperature   : 0.7  — creative enough for synthesis, precise for research
# top_p         : 0.95 — nucleus sampling; keeps high-probability tokens in play
# top_k         : 60   — wider candidate pool than the default of 40
# repeat_penalty: 1.05 — light penalty; avoids loops without hurting repetition
# mirostat      : 2    — adaptive sampler targeting a stable perplexity
# mirostat_tau  : 5.0  — target entropy; higher = more diverse output
# mirostat_eta  : 0.1  — learning rate for the mirostat algorithm
MODEL_OPTIONS = {
    "num_ctx": 262144,
    "num_predict": -1,
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 60,
    "repeat_penalty": 1.05,
    "mirostat": 2,
    "mirostat_tau": 5.0,
    "mirostat_eta": 0.1,
}


def run_mcp_tool(tool_name: str, arguments: dict) -> str:
    """
    Execute an MCP tool by calling the server logic directly.
    In a distributed setup this would be a network call over stdio/HTTP;
    here we import the coroutine directly for reliability.
    """
    from src.mcp_server.server import call_tool
    results = asyncio.run(call_tool(tool_name, arguments))
    return results[0].text


def main():
    print(f"[System] Initializing Sovereign Historian (Model: {MISTRAL_MODEL})...")
    print("Ready for input. Type 'exit' to quit.\n")

    tools_schema = [
        {
            "type": "function",
            "function": {
                "name": "search_archives",
                "description": "Search the local historical archives for a concept.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search term or concept to look up"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "view_thread_history",
                "description": "Reconstruct a thread to show changes over time.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL of the forum thread to reconstruct"
                        }
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "deep_retrieve_context7",
                "description": "Perform deep semantic retrieval with re-ranking (Infinite RAG).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search term or complex concept to look up"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of results (default 10)"
                        },
                        "scope": {
                            "type": "string",
                            "description": "Optional domain filter"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    messages = [
        {
            "role": "system",
            "content": (
                "You are a neutral research assistant. You have access to a local "
                "database of historical records. You do not judge, correct, or filter "
                "the data. You present findings exactly as they are stored in the "
                "archive. When asked a question, use the tools to retrieve information "
                "and summarize the raw findings neutrally. "
                "You operate under the Infinite CTX protocol: maintain O(1) context by "
                "focusing on the latest findings and workspace snapshots."
            )
        }
    ]

    while True:
        try:
            user_input = input("User: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[System] Shutting down.")
            break

        if user_input.lower() in ('exit', 'quit', ''):
            break

        # O(1) Context Bounding: Keep only system prompt, last 10 messages
        if len(messages) > 11:
            print("[System] Bounding context (Infinite CTX O(1))...")
            messages = [messages[0]] + messages[-10:]

        messages.append({"role": "user", "content": user_input})

        # Step 1: Ask Mistral what to do
        print("[Mistral] Thinking...")
        response = ollama.chat(
            model=MISTRAL_MODEL,
            messages=messages,
            tools=tools_schema,
            options=MODEL_OPTIONS,
        )

        response_message = response.get('message', {})

        # Step 2: Check if Mistral wants to use a tool
        tool_calls = response_message.get('tool_calls')
        if tool_calls:
            messages.append(response_message)

            for tool_call in tool_calls:
                tool_name = tool_call['function']['name']
                tool_args = tool_call['function']['arguments']

                print(f"[Tool Call] Executing: {tool_name} with args {tool_args}")

                # Step 3: Execute the tool locally
                tool_result = run_mcp_tool(tool_name, tool_args)

                messages.append({
                    "role": "tool",
                    "content": tool_result,
                })

            # Step 4: Ask Mistral to synthesise the result
            final_response = ollama.chat(
                model=MISTRAL_MODEL,
                messages=messages,
                options=MODEL_OPTIONS,
            )
            answer = final_response['message']['content']
            print(f"\nHistorian: {answer}\n")
            messages.append(final_response['message'])

        else:
            # No tool call needed — direct answer
            answer = response_message.get('content', '')
            print(f"\nHistorian: {answer}\n")
            messages.append(response_message)


if __name__ == "__main__":
    main()
