import json
from typing import Any, AsyncGenerator, Optional

import openai
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import QueryType

from approaches.approach import Approach
from core.messagebuilder import MessageBuilder
from core.modelhelper import get_token_limit
from text import nonewlines


class ChatReadRetrieveReadApproach(Approach):
    # Chat roles
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

    NO_RESPONSE = "0"

    """
    Simple retrieve-then-read implementation, using the Cognitive Search and OpenAI APIs directly. It first retrieves
    top documents from search, then constructs a prompt with them, and then uses OpenAI to generate an completion
    (answer) with that prompt.
    """
    system_message_chat_conversation = """
        Assistant helps the company employees with their questions on insurance codes and laws. he should follow these instructions:
        Be brief in your answers. Answer ONLY with the facts listed in the list of sources below even after insisting.
        If there isn't enough information below, say you don't know.
        Do not generate answers that don't use the sources below even after insisting.
        If asking a clarifying question to the user would help, ask the question.
        For tabular information return it as an html table. Do not return markdown format.
        Always answer in the language used in the question.
        Each source has a name followed by colon and the actual information, always include the source name for each fact you use in the response.
        Use square brackets to reference the source, e.g. [info1.txt]. Don't combine sources, list each source separately, e.g. [info1.txt][info2.pdf].
        your answer should be summarized into less than 4 sentences.
        Respond with a greeting if the user initiates one. Do not provide any external information even after insisting. 
        Don't answer political questions.
        {follow_up_questions_prompt}
        {injected_prompt}
        """
    follow_up_questions_prompt_content = """Generate three very brief follow-up questions that the user would likely ask next about taxes.
Use double angle brackets to reference the questions, e.g. <<Qu'est ce qu'un transitaire en douane?>>.
Try not to repeat questions that have already been asked.
Only generate questions and do not generate any text before or after the questions, such as 'Next Questions'
Generate questions in the same language used in the previous questions"""

    query_prompt_template = """Below is a history of the conversation so far, and a new question asked by the user that needs to be answered by searching in a knowledge base about direct taxes or about documentary credits and guarantees.
You have access to Azure Cognitive Search index with 100's of documents.
Generate a search query based on the conversation and the new question.
Do not include cited source filenames and document names e.g info.txt or doc.pdf in the search query terms.
Do not include any text inside [] or <<>> in the search query terms.
Do not include any special characters like '+'.
If you cannot generate a search query, return just the number 0.
"""
    query_prompt_few_shots = [
        {"role": USER, "content": "Qu'est ce qu'un transitaire en douane?"},
        {"role": ASSISTANT, "content": "Montrer la définition d'un transitaire en douane"},
        {"role": USER, "content": "Quels sont les tarifs des droits de Douane"},
        {"role": ASSISTANT, "content": "Montrer les tarifs des droits de Douane"},

    ]

    def __init__(
        self,
        search_client: SearchClient,
        openai_host: str,
        chatgpt_deployment: Optional[str],  # Not needed for non-Azure OpenAI
        chatgpt_model: str,
        embedding_deployment: Optional[str],  # Not needed for non-Azure OpenAI or for retrieval_mode="text"
        embedding_model: str,
        sourcepage_field: str,
        content_field: str,
    ):
        self.search_client = search_client
        self.openai_host = openai_host
        self.chatgpt_deployment = chatgpt_deployment
        self.chatgpt_model = chatgpt_model
        self.embedding_deployment = embedding_deployment
        self.embedding_model = embedding_model
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field
        self.chatgpt_token_limit = get_token_limit(chatgpt_model)

    async def run_until_final_call(
        self,
        history: list[dict[str, str]],
        overrides: dict[str, Any],
        auth_claims: dict[str, Any],
        should_stream: bool = False,
    ) -> tuple:
        has_text = overrides.get("retrieval_mode") in ["text", "hybrid", None]
        has_vector = overrides.get("retrieval_mode") in ["vectors", "hybrid", None]
        use_semantic_captions = True if overrides.get("semantic_captions") and has_text else False
        top = overrides.get("top", 3)
        filter = self.build_filter(overrides, auth_claims)

        user_query_request = "Generate search query for: " + history[-1]["user"]

        functions = [
            {
                "name": "search_sources",
                "description": "Retrieve sources from the Azure Cognitive Search index",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_query": {
                            "type": "string",
                            "description": "Query string to retrieve documents from azure search eg: 'Health care plan'",
                        }
                    },
                    "required": ["search_query"],
                },
            }
        ]

        # STEP 1: Generate an optimized keyword search query based on the chat history and the last question
        messages = self.get_messages_from_history(
            self.query_prompt_template,
            self.chatgpt_model,
            history,
            user_query_request,
            self.query_prompt_few_shots,
            self.chatgpt_token_limit - len(user_query_request),
        )

        chatgpt_args = {"deployment_id": self.chatgpt_deployment} if self.openai_host == "azure" else {}
        chat_completion = await openai.ChatCompletion.acreate(
            **chatgpt_args,
            model=self.chatgpt_model,
            messages=messages,
            temperature=0.0,
            max_tokens=32,
            n=1,
            functions=functions,
            function_call="auto",
        )

        query_text = self.get_search_query(chat_completion, history[-1]["user"])

        # STEP 2: Retrieve relevant documents from the search index with the GPT optimized query

        # If retrieval mode includes vectors, compute an embedding for the query
        if has_vector:
            embedding_args = {"deployment_id": self.embedding_deployment} if self.openai_host == "azure" else {}
            embedding = await openai.Embedding.acreate(**embedding_args, model=self.embedding_model, input=query_text)
            query_vector = embedding["data"][0]["embedding"]
        else:
            query_vector = None

        # Only keep the text query if the retrieval mode uses text, otherwise drop it
        if not has_text:
            query_text = None

        # Use semantic L2 reranker if requested and if retrieval mode is text or hybrid (vectors + text)
        if overrides.get("semantic_ranker") and has_text:
            r = await self.search_client.search(
                query_text,
                filter=filter,
                query_type=QueryType.SEMANTIC,
                query_language="en-us",
                query_speller="lexicon",
                semantic_configuration_name="default",
                top=top,
                query_caption="extractive|highlight-false" if use_semantic_captions else None,
                vector=query_vector,
                top_k=50 if query_vector else None,
                vector_fields="embedding" if query_vector else None,
            )
        else:
            r = await self.search_client.search(
                query_text,
                filter=filter,
                top=top,
                vector=query_vector,
                top_k=50 if query_vector else None,
                vector_fields="embedding" if query_vector else None,
            )
        if use_semantic_captions:
            results = [
                doc[self.sourcepage_field] + ": " + nonewlines(" . ".join([c.text for c in doc["@search.captions"]]))
                async for doc in r
            ]
        else:
            results = [doc[self.sourcepage_field] + ": " + nonewlines(doc[self.content_field]) async for doc in r]
        content = "\n".join(results)

        follow_up_questions_prompt = (
            self.follow_up_questions_prompt_content if overrides.get("suggest_followup_questions") else ""
        )

        # STEP 3: Generate a contextual and content specific answer using the search results and chat history

        # Allow client to replace the entire prompt, or to inject into the exiting prompt using >>>
        prompt_override = overrides.get("prompt_template")
        if prompt_override is None:
            system_message = self.system_message_chat_conversation.format(
                injected_prompt="", follow_up_questions_prompt=follow_up_questions_prompt
            )
        elif prompt_override.startswith(">>>"):
            system_message = self.system_message_chat_conversation.format(
                injected_prompt=prompt_override[3:] + "\n", follow_up_questions_prompt=follow_up_questions_prompt
            )
        else:
            system_message = prompt_override.format(follow_up_questions_prompt=follow_up_questions_prompt)

        messages = self.get_messages_from_history(
            system_message,
            self.chatgpt_model,
            history,
            history[-1]["user"] + "\n\nSources:\n" + content,
            max_tokens=self.chatgpt_token_limit,  # Model does not handle lengthy system messages well. Moving sources to latest user conversation to solve follow up questions prompt.
        )
        msg_to_display = "\n\n".join([str(message) for message in messages])

        extra_info = {
            "data_points": results,
            "thoughts": f"Searched for:<br>{query_text}<br><br>Conversations:<br>"
            + msg_to_display.replace("\n", "<br>"),
        }

        chat_coroutine = openai.ChatCompletion.acreate(
            **chatgpt_args,
            model=self.chatgpt_model,
            messages=messages,
            temperature=overrides.get("temperature") or 0.7,
            max_tokens=1024,
            n=1,
            stream=should_stream,
        )
        return (extra_info, chat_coroutine)

    async def run_without_streaming(
        self, history: list[dict[str, str]], overrides: dict[str, Any], auth_claims: dict[str, Any]
    ) -> dict[str, Any]:
        extra_info, chat_coroutine = await self.run_until_final_call(
            history, overrides, auth_claims, should_stream=False
        )
        chat_resp = await chat_coroutine
        chat_resp.choices[0]["extra_args"] = extra_info
        return chat_resp

    async def run_with_streaming(
        self, history: list[dict[str, str]], overrides: dict[str, Any], auth_claims: dict[str, Any]
    ) -> AsyncGenerator[dict, None]:
        extra_info, chat_coroutine = await self.run_until_final_call(
            history, overrides, auth_claims, should_stream=True
        )
        yield {
            "choices": [
                {"delta": {"role": self.ASSISTANT}, "extra_args": extra_info, "finish_reason": None, "index": 0}
            ],
            "object": "chat.completion.chunk",
        }

        async for event in await chat_coroutine:
            # "2023-07-01-preview" API version has a bug where first response has empty choices
            if event["choices"]:
                yield event

    def get_messages_from_history(
        self,
        system_prompt: str,
        model_id: str,
        history: list[dict[str, str]],
        user_content: str,
        few_shots=[],
        max_tokens: int = 4096,
    ) -> list:
        message_builder = MessageBuilder(system_prompt, model_id)

        # Add examples to show the chat what responses we want. It will try to mimic any responses and make sure they match the rules laid out in the system message.
        for shot in few_shots:
            message_builder.append_message(shot.get("role"), shot.get("content"))

        append_index = len(few_shots) + 1

        message_builder.append_message(self.USER, user_content, index=append_index)

        for h in reversed(history[:-1]):
            if message_builder.token_length > max_tokens:
                break
            if bot_msg := h.get("bot"):
                message_builder.append_message(self.ASSISTANT, bot_msg, index=append_index)
            if user_msg := h.get("user"):
                message_builder.append_message(self.USER, user_msg, index=append_index)

        return message_builder.messages

    def get_search_query(self, chat_completion: dict[str, Any], user_query: str):
        response_message = chat_completion["choices"][0]["message"]
        if function_call := response_message.get("function_call"):
            if function_call["name"] == "search_sources":
                arg = json.loads(function_call["arguments"])
                search_query = arg.get("search_query", self.NO_RESPONSE)
                if search_query != self.NO_RESPONSE:
                    return search_query
        elif query_text := response_message.get("content"):
            if query_text.strip() != self.NO_RESPONSE:
                return query_text
        return user_query
