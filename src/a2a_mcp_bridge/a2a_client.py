"""Call another agent over A2A and return its final text.

Used both by the Researcher (to delegate to the Analyst) and by the demo client
(to kick off the Researcher). Uses the SDK's streaming client; the final
assistant text is the last non-empty chunk.
"""

from __future__ import annotations

from a2a.client import ClientConfig, ClientFactory
from a2a.helpers import get_stream_response_text, new_text_message
from a2a.types import SendMessageRequest


async def call_agent(url: str, text: str) -> str:
    """Send ``text`` to the A2A agent at ``url`` and return its final answer."""
    factory = ClientFactory(ClientConfig(streaming=True))
    client = await factory.create_from_url(url)
    try:
        request = SendMessageRequest(message=new_text_message(text))
        final = ""
        async for response in client.send_message(request):
            chunk = get_stream_response_text(response)
            if chunk and chunk.strip():
                final = chunk
        return final
    finally:
        await client.close()
