from pickle import NONE
from openai import AzureOpenAI
from datetime import datetime
import os
import json
import traceback
from bson import ObjectId
from pymongo import MongoClient
import re
from config import *

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(JSONEncoder, self).default(obj)


class QueryBase:
    def __init__(self, db='prod'):
        self.client = None
        self.schema = {}

    def update_mind_client(self, env=None):
        client = mongo_client
        return client

    def get_field_type(self, value):
        if isinstance(value, str):
            return 'string'
        elif isinstance(value, int):
            return 'int'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, bool):
            return 'bool'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        elif isinstance(value, datetime):
            return 'datetme'
        elif value is None:
            return 'null'
        else:
            return 'unknown'

    def get_document_schema(self, collection, required_fields=None):
        if not required_fields:
            document = collection.find_one(sort=[('_id', -1)])

        else:
            pipeline = [
                {"$sample": {"size": 1}},
                {"$project": {field: 1 for field in required_fields}}
            ]
            sample_docs = list(collection.aggregate(pipeline))
            if sample_docs:
                document = sample_docs[0]
        schema = {}

        for key, value in document.items():
            schema[key] = self.get_field_type(value)
        return schema, document

    def _extract_json(self, text):
        stack = []
        json_start = -1
        for i, char in enumerate(text):
            if char == '{':
                if not stack:
                    json_start = i
                stack.append(char)
            elif char == '}':
                stack.pop()
                if not stack:
                    json_string = text[json_start:i + 1]
                    try:
                        return json.loads(json_string)
                    except Exception as e:
                        return e

    @property
    def _base_template(self):
        temp = "You are a MongoDb expert. Create a syntactically correct raw aggregation query for the user question:\n"
        return temp

    def open_api_endpoint(self, template):
        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version,
        )
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": template}
            ]
        )

        output_str = response.choices[0].message.content
        output_json = self._extract_json(output_str)
        # if 'pipeline' not in output_json:
        #     raise ValueError("Invalid format: 'pipeline' key not found")
        return output_json

    def prompt_query(self, db, collection, query, env="prod"):
        self.update_mind_client(env=env)
        collection = self.client[db][collection]
        schema, document = self.get_document_schema(collection)
        system_temp = f"""
        This is the document schema : "{schema}"
        The following is an the example of one mongodb document: {document}
        Return the raw aggregration pipeline in JSON.
        output should be like  {{"pipeline": "json_object"}}
        Unless the user specifies in the question a specific number of examples to obtain, limit your query to at most 50 results using the $limit stage in an aggregation pipeline.
        Always use the field names as they appear in the collection. Be careful not to query for fields that do not exist.
        When dealing with dates, and if the question involves "today", use MongoDB's $currentDate,
        ###{query}###
        """
        final_temp = self._base_template + system_temp
        try:
            output_json = self.open_api_endpoint(final_temp)
            # if 'pipeline' not in output_json:
            #     raise ValueError("Invalid format: 'pipeline' key not found")
            if output_json.get('pipeline'):
                output_json['pipeline'].append({'$project': {'_id': 0}})
            result = list(collection.aggregate(output_json['pipeline'] if output_json.get('pipeline') else
                                               [output_json]))
            return result
        except Exception as e:
            print(traceback.format_exc())
            return e

    def custom_prompt_query(self, db, collection, custom_prompt, env=None, minutes_ago=None, foreign_collection=None):
        try:
            self.update_mind_client(env=env)
            collection = self.client[db][collection]
            schema, document = self.get_document_schema(collection)
            schema_str = json.dumps(schema, indent=1, cls=JSONEncoder)
            document_str = json.dumps(document, indent=1, cls=JSONEncoder)
            if foreign_collection:
                foreign_collection = self.client[db][foreign_collection]
                schema_foreign, document_foreign = self.get_document_schema(foreign_collection)
                schema_foreign_str = json.dumps(schema_foreign, indent=1, cls=JSONEncoder)
                document_foreign_str = json.dumps(document_foreign, indent=1, cls=JSONEncoder)
            else:
                schema_foreign_str = ''
                document_foreign_str = ''
            document_str = json.dumps(document, indent=1, cls=JSONEncoder)
            custom_prompt = custom_prompt.format(schema=schema_str, document=document_str, \
                                                 schema_foreign=schema_foreign_str,
                                                 document_foreign=document_foreign_str)
            final_temp = self._base_template + custom_prompt
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return e
        try:
            output_json = self.open_api_endpoint(final_temp)
            print("output_json", output_json)
            if minutes_ago:
                if output_json.get('pipeline') and isinstance(output_json.get('pipeline'), list) and len(
                        output_json.get('pipeline')) > 0:
                    for idx, item in enumerate(output_json['pipeline']):
                        if item.get('$match'):
                            for key, value in item['$match'].items():
                                if isinstance(value, dict):
                                    for sub_key, sub_value in value.items():
                                        if 'minutes_ago' in sub_value:
                                            output_json['pipeline'][idx]['$match'][key][sub_key] = minutes_ago
                                elif 'minutes_ago' in value:
                                    output_json['pipeline'][idx]['$match'][key] = minutes_ago
            result = list(collection.aggregate(output_json['pipeline']
                                               if output_json.get('pipeline')
                                               else [output_json]))
            return result
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return e












