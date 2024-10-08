import os
import asyncio
from openai import AsyncOpenAI

import chainlit as cl
from uuid import uuid4
from chainlit.logger import logger

from realtime import RealtimeClient
from realtime.tools import tools

client = AsyncOpenAI()    

@cl.action_callback("english")
async def on_action(action):
    cl.user_session.set("language", "english")
    await cl.Message(content="Responses from the Chatbot will be in English").send()

@cl.action_callback("icelandic")
async def on_action(action):
    cl.user_session.set("language", "icelandic")
    await cl.Message(content="Responses from the Chatbot will be in Icelandic").send()

@cl.action_callback("ask_question")
async def on_action(action):
    cl.user_session.set("question", "How much wood would a woodchuck chuck if a woodchuck could chuck wood?")
    await cl.Message(content="Asking my assistant a question").send()

async def setup_openai_realtime():
    """Instantiate and configure the OpenAI Realtime Client"""
    openai_realtime = RealtimeClient(api_key=os.getenv("OPENAI_API_KEY"))
    cl.user_session.set("track_id", str(uuid4()))
    async def handle_conversation_updated(event):
        item = event.get("item")
        delta = event.get("delta")
        """Currently used to stream audio back to the client."""
        if delta:
            # Only one of the following will be populated for any given event
            if 'audio' in delta:
                audio = delta['audio']  # Int16Array, audio added
                await cl.context.emitter.send_audio_chunk(cl.OutputAudioChunk(mimeType="pcm16", data=audio, track=cl.user_session.get("track_id")))
            if 'transcript' in delta:
                transcript = delta['transcript']  # string, transcript added
                pass
            if 'arguments' in delta:
                arguments = delta['arguments']  # string, function arguments added
                pass
            
    async def handle_item_completed(item):
        """Used to populate the chat context with transcription once an item is completed."""
        # print(item) # TODO
        pass
    
    async def handle_conversation_interrupt(event):
        """Used to cancel the client previous audio playback."""
        cl.user_session.set("track_id", str(uuid4()))
        await cl.context.emitter.send_audio_interrupt()
        
    async def handle_error(event):
        logger.error(event)

    await openai_realtime.update_session(instructions="You are Australian and a little talkative")
    # await openai_realtime.update_session(voice="alloy")

    openai_realtime.on('conversation.updated', handle_conversation_updated)
    openai_realtime.on('conversation.item.completed', handle_item_completed)
    openai_realtime.on('conversation.interrupted', handle_conversation_interrupt)
    openai_realtime.on('error', handle_error)

    cl.user_session.set("openai_realtime", openai_realtime)
    coros = [openai_realtime.add_tool(tool_def, tool_handler) for tool_def, tool_handler in tools]
    await asyncio.gather(*coros)


@cl.on_chat_start
async def start():
    actions = [
        cl.Action(name="english", value="english", description="English"),
        cl.Action(name="icelandic", value="icelandic", description="Icelandic"),
        cl.Action(name="ask_question", value="ask_question", description="Ask my assistant a question")
    ]

    await cl.Message(content="Languages", actions=actions).send()

    await cl.Message(
        content="Welcome to the Sidekick. Press `P` to talk!"
    ).send()
    await setup_openai_realtime()

@cl.on_message
async def on_message(message: cl.Message):
    print("on_message()")
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime and openai_realtime.is_connected():
        # TODO: Try image processing with message.elements
        await openai_realtime.send_user_message_content([{ "type": 'input_text', "text": message.content }])
    else:
        await cl.Message(content="Please activate voice mode before sending messages!").send()

@cl.on_audio_start
async def on_audio_start():
    try:
        openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
        await openai_realtime.connect()
        logger.info("Connected to OpenAI realtime")
        # TODO: might want to recreate items to restore context
        # openai_realtime.create_conversation_item(item)
        
    except Exception as e:
        await cl.ErrorMessage(content=f"Failed to connect to OpenAI realtime: {e}").send()
        return 
    print("done on_audio_start")
    return True

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    language = cl.user_session.get("language", "english")  
    question = cl.user_session.get("question", "How much wood would a woodchuck chuck if a woodchuck could chuck wood?")
    if openai_realtime and openai_realtime.is_connected() and language:
        await openai_realtime.update_session(instructions=f"You will answer in {language}")
    if openai_realtime and openai_realtime.is_connected() and question:
        await openai_realtime.update_session(instructions=f"You will answer the question: {question}")
    if openai_realtime and openai_realtime.is_connected():
        await openai_realtime.append_input_audio(chunk.data)
    else:
        logger.info("RealtimeClient is not connected")

@cl.on_audio_end
@cl.on_chat_end
@cl.on_stop
async def on_end():
    openai_realtime: RealtimeClient = cl.user_session.get("openai_realtime")
    if openai_realtime and openai_realtime.is_connected():
        await openai_realtime.disconnect()