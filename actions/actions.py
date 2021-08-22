# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from elasticsearch import Elasticsearch
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []


############# ELASTICSEARCH MODULE CLASS ###############
class ElasticModule:
    def __init__(self):
        self.rest_index = 'restaurants'
        self.elastic = Elasticsearch()

    def get_infos(self, slots_content):
        if slots_content["restaurant_name"] != None:
            query_body = {
                "query": {
                    "match": {
                        "restaurant_name": slots_content["restaurant_name"]
                    }
                }
            }
        else:
            filters = []
            for key, content in slots_content.items():
                if key != "restaurant_name" or content != None:
                    filters.append({"term": {key: content}})
            query_body = {
                "query": {
                    "bool": {
                        "filter": filters
                    }
                }
            }
        list_rest = []
        query = self.elastic.search(index=self.rest_index, body=query_body)['hits']['hits']
        
        for p in query:
            list_rest.append(p['_source'])

        return list_rest
    
    def get_rest_names(self):
        query = self.elastic.search(index=self.rest_index)['hits']['hits']
        
        rest_names = []
        for p in query:
            p_name = p['_source']['restaurant_name']
            if p_name not in rest_names:
                rest_names.append(p_name)
        return rest_names

elastic_mod = ElasticModule()

########### ACTION CLASSES ###########
class ActionGetInfos(Action):
    def name(self) -> Text:
        return "action_get_infos"

    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        slots_content = {
            "restaurant_name": tracker.get_slot("restaurant_name"),
            "city" : None,
            "cuisine" : None,
            "date" : None,
            "time" : None    
        }
        list_rest = elastic_mod.get_infos(slots_content=slots_content)
        display_resp = []
        if list_rest == []:
            display_resp = "Unfortunatly, I don't have these infomations in my data :("
        else:
            for rests in list_rest:
                msg = []
                for key, it in rests.items():
                    msg.append(f"{key} --> {it}")
                msg = " : ".join(msg)
                display_resp.append(msg)

            display_resp = "\n".join(display_resp)

        dispatcher.utter_message(response="utter_list_infos", text=display_resp)
        return []

class ActionGetRestNames(Action):
    def name(self) -> Text:
        return "action_get_restaurants"

    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            
        list_rest_names = elastic_mod.get_rest_names()
        list_rest_names = "\n"
        dispatcher.utter_message(response="utter_list_restaurants", text=list_rest_names)

class ActionResetSlots(Action):
    def name(self) -> Text:
        return "action_reset_slots"
    
    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

            slots_to_reset = ["restaurant_name", "city", "cuisine", "date", "time"]
            return [SlotSet(slot, None) for slot in slots_to_reset]
