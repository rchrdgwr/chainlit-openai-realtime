Title: Realtime Assistant
Tags: [multimodal, audio]

# Open AI realtime API with Chainlit

This code was taken from the Chainlit cookbooks and modified to add Actions to change the assistant's behavior mid conversation.

Additional changes will be added as experiments are done with the OpenAI Realtime API.

2 buttons have been added using Chainlit Actions. When clicked:
- the language changes to the selected button
- the assistant should talk in the selected language
- NOTE this wont work mid-sentence but should work for the next chat conversation.



This cookbook demonstrates how to build realtime copilots with Chainlit.

## Key Features

- **Realtime Python Client**: Based off https://github.com/openai/openai-realtime-api-beta
- **Multimodal experience**: Speak and write to the assistant at the same time
- **Tool calling**: Ask the assistant to perform tasks and see their output in the UI
- **Visual Presence**: Visual cues indicating if the assistant is listening or speaking
