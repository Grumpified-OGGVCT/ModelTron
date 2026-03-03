import sys
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Mock heavy ML / MCP dependencies BEFORE any test file imports server.py.
# This prevents model downloads (~100 MB) during unit tests.
# ---------------------------------------------------------------------------

# 1. sentence_transformers — encode() returns a fixed-length float list
_st = MagicMock()
_st.SentenceTransformer.return_value.encode.return_value = [0.1] * 384
sys.modules['sentence_transformers'] = _st

# 2. chromadb — query() returns empty result sets by default
_collection = MagicMock()
_collection.query.return_value = {'documents': [[]], 'metadatas': [[]]}
_chroma = MagicMock()
_chroma.PersistentClient.return_value.get_or_create_collection.return_value = _collection
sys.modules['chromadb'] = _chroma

# 3. mcp — make list_tools/call_tool decorators transparent (identity functions)
#    so the actual async functions in server.py remain callable in tests.
class _MockServer:
    def __init__(self, name):
        pass
    def list_tools(self):
        return lambda fn: fn
    def call_tool(self):
        return lambda fn: fn
    def create_initialization_options(self):
        return {}

_mcp_server_mod = MagicMock()
_mcp_server_mod.Server = _MockServer
sys.modules['mcp'] = MagicMock()
sys.modules['mcp.server'] = _mcp_server_mod
sys.modules['mcp.server.stdio'] = MagicMock()

# TextContent must be a real class so test assertions can inspect .text
class _TextContent:
    def __init__(self, *, type, text):
        self.type = type
        self.text = text

_mcp_types = MagicMock()
_mcp_types.TextContent = _TextContent
_mcp_types.Tool = MagicMock()
sys.modules['mcp.types'] = _mcp_types
