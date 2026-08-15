"""The conversational agent: system prompt + LangChain tool-calling loop.

Mirrors the llm_engineering week2 pattern (a `while` loop that keeps handing
tool results back to the model until it returns a plain answer) but expressed
with LangChain message objects and `ChatOpenAI.bind_tools`.
"""
from __future__ import annotations

from datetime import datetime

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.domain.booking_rules import BookingError
from app.domain.rooms import ROOMS
from app.services.booking_service import BookingService
from app.agent.tools import build_tools

MAX_TOOL_ITERATIONS = 6


def _system_prompt(username: str) -> str:
    room_lines = "\n".join(f"  - Room {r.name}: capacity {r.capacity}" for r in ROOMS.values())
    now = datetime.now()
    return f"""You are the booking assistant for the Cubo Itau office. You help \
{username} manage meeting-room reservations and nothing else. Politely decline \
requests unrelated to meeting rooms.

The current date and time is {now:%A %Y-%m-%d %H:%M}. When the user says "today", \
"tomorrow", "3pm" etc., resolve them to concrete ISO-8601 datetimes before calling tools.

Office rules you must respect (the tools also enforce them):
{room_lines}
  - Bookings use 30-minute slots aligned to :00 or :30.
  - A booking covers contiguous slots only, maximum duration 3 hours.
  - Attendees must not exceed the room's capacity.
  - Rooms cannot be double-booked; back-to-back bookings are allowed.
  - Every booking needs a title.

Guidance:
  - Before creating a booking, make sure you have room, title, attendee count, \
start and end. Ask for whatever is missing.
  - To cancel, first use list_my_bookings to find the id if the user didn't give one.
  - Always confirm what you did in clear, friendly language and show times as HH:MM.
  - If a tool reports an error, explain it plainly and suggest a fix (e.g. another room or time).
"""


def run_chat(
    *,
    user_message: str,
    history: list[dict],
    service: BookingService,
    username: str,
) -> str:
    """Run one conversational turn and return the assistant's text reply.

    `history` is a list of {"role": "user"|"assistant", "content": str}.
    """
    if not settings.openai_api_key:
        return (
            "The assistant is not configured yet: no OPENAI_API_KEY is set on the "
            "server. Add it to the environment and try again."
        )

    tools = build_tools(service, username)
    tools_by_name = {t.name: t for t in tools}
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    ).bind_tools(tools)

    messages: list[BaseMessage] = [SystemMessage(content=_system_prompt(username))]
    for turn in history:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))
    messages.append(HumanMessage(content=user_message))

    for _ in range(MAX_TOOL_ITERATIONS):
        ai_msg: AIMessage = llm.invoke(messages)
        messages.append(ai_msg)

        if not ai_msg.tool_calls:
            return ai_msg.content

        for call in ai_msg.tool_calls:
            tool = tools_by_name.get(call["name"])
            try:
                if tool is None:
                    result = f"Unknown tool '{call['name']}'."
                else:
                    result = tool.invoke(call["args"])
            except BookingError as exc:
                result = f"Booking error: {exc}"
            except Exception as exc:  # keep the loop alive on unexpected tool errors
                result = f"Unexpected error running {call['name']}: {exc}"
            messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))

    return "I wasn't able to complete that request after several steps. Could you rephrase it?"
