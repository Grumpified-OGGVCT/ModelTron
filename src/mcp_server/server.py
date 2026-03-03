import asyncio
import sqlite3

import chromadb
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from sentence_transformers import SentenceTransformer

app = Server("stolen_history_vault")

# ---------------------------------------------------------------------------
# Local inference resources (loaded once at startup)
# ---------------------------------------------------------------------------
embedder = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./data/chroma_db")
collection = chroma_client.get_or_create_collection(name="stolen_history")


# ---------------------------------------------------------------------------
# Database helper — always opens in read-only mode
# ---------------------------------------------------------------------------
def get_db():
    return sqlite3.connect('file:./data/vault.db?mode=ro', uri=True)


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="search_archives",
            description=(
                "Search the local historical archives for a concept using "
                "semantic similarity. Returns matching archival text with "
                "author and source metadata."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="view_thread_history",
            description=(
                "Reconstruct a thread to show how it changed over time across "
                "all stored snapshots (live and Wayback). Posts flagged as "
                "deleted are marked [DELETED] in the output."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"]
            }
        )
    ]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_archives":
        query = arguments["query"]
        vector = embedder.encode(query).tolist()

        results = collection.query(query_embeddings=[vector], n_results=5)

        output = "--- RAW ARCHIVAL DATA ---\n"
        for doc, meta in zip(
            results['documents'][0], results['metadatas'][0]
        ):
            output += (
                f"[Author: {meta.get('author', 'N/A')} "
                f"| Source: {meta.get('source', 'N/A')}]\n"
            )
            output += f"{doc}\n-------------------------\n"

        return [TextContent(type="text", text=output)]

    elif name == "view_thread_history":
        url = arguments["url"]
        conn = get_db()
        cur = conn.cursor()

        rows = cur.execute(
            """
            SELECT p.author, p.content_clean, p.source_type, p.snapshot_date,
                   p.is_deleted
            FROM posts p
            JOIN threads t ON p.thread_id = t.id
            WHERE t.url = ?
            ORDER BY p.post_external_id, p.snapshot_date
            """,
            (url,)
        ).fetchall()
        conn.close()

        output = f"--- THREAD RECONSTRUCTION: {url} ---\n"
        for row in rows:
            author, content, source, date, is_deleted = row
            deleted_marker = " [DELETED]" if is_deleted else ""
            output += f"[{source.upper()} | {date}]{deleted_marker} {author}: {content}\n"

        return [TextContent(type="text", text=output)]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    asyncio.run(_run())
