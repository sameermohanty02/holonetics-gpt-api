from llama_index.core.agent import ReActAgent
from llama_index.core.chat_engine import SimpleChatEngine
from openai import OpenAI
from llama_index.core.tools.tool_spec.base import BaseToolSpec
from llama_index.llms.azure_openai import AzureOpenAI
from db_search.base_query_ import QueryBase
import os
from summarization.summarize import Summarize
from config import *


def get_llm():
    llm = AzureOpenAI(
        engine="gpt-4",
        model="gpt-4",
        temperature=0.5,
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        api_version=api_version,
    )
    return llm

class MetricDB(BaseToolSpec):
    spec_functions = [
            "get_outage_details",
            "get_node_details"
        ]

    def __init__(self):
        self.base_obj = QueryBase()
        self.query = self.base_obj.prompt_query
        self.custom_query = self.base_obj.custom_prompt_query

    def get_outage_details(self, complete_user_question):
        "to get if there is any outage going on a node "
        try:
            collection = "stats_outage"
            db = "holonetics"
            result = self.query(db, collection, complete_user_question)
            obj = Summarize()
            result_summary = obj.summarize_text(result, "Please summarize this outage")
            if result_summary:
                return result_summary
        except Exception as e:
            print(e)
        return result

    def get_node_details(self, question):
        "to get any information regarding a node like dc, hostname, ip address"
        collection = "nodes"
        db = "holonetics"
        result = self.query(db, collection, question)
        return result




def db_query(input):
    neat = MetricDB()
    neat_agent = ReActAgent.from_tools(neat.to_tool_list(), llm=get_llm(), verbose=True, max_iterations=20)
    response = neat_agent.chat(input)
    return response





