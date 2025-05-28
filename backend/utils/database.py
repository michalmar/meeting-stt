import os
from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential
from typing import Optional, List, Dict
import uuid
from dotenv import load_dotenv
import time
import glob
import json

class CosmosDB:
    def __init__(self):
        load_dotenv("./.env", override=True)
        # Get Cosmos DB account details
        COSMOS_DB_URI = os.getenv("COSMOS_DB_URI", "https://YOURDB.documents.azure.com:443/")
        COSMOS_DB_DATABASE = os.getenv("COSMOS_DB_DATABASE", "YOUR_DATABASE")
        credential = DefaultAzureCredential()
        self.client = CosmosClient(COSMOS_DB_URI, credential=credential)
        self.database = self.client.create_database_if_not_exists(id=COSMOS_DB_DATABASE)
        self.containers = {}
        # Pre-initialize default containers
        self.containers["ag_demo"] = self.database.create_container_if_not_exists(
            id="ag_demo",
            partition_key=PartitionKey(path="/user_id"),
            offer_throughput=400
        )
    
    def get_container(self, container_name: str = "ag_demo"):
        if container_name in self.containers:
            return self.containers[container_name]
        container = self.database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path="/user_id"),
            offer_throughput=400
        )
        self.containers[container_name] = container
        return container
    
    def format_message(self, _log_entry_json):
        return _log_entry_json

    def store_conversation(self, conversation: list):
        _messsages = []
        for message in conversation.messages:
            _m = self.format_message(message)
            _messsages.append(_m.to_json())
        conversation_document_item = {
            "id": str(uuid.uuid4()),
            "user_id": conversation_details.session_user,
            "session_id": conversation_details.session_id,
            "messages": _messsages, 
            "agents": conversation_dict["agents"],
            "run_mode_locally": False,
            "timestamp": conversation_details.time,
        }
        container = self.get_container("ag_demo")
        response = container.create_item(body=conversation_document_item)
        return response

    def fetch_user_conversatons(self, user_id: Optional[str] = None, page: int = 1, page_size: int = 20) -> Dict:
        # container = self.get_container("ag_demo")
        
        # First, get the total count
        if user_id is None:
            count_query = "SELECT VALUE COUNT(1) FROM c"
            count_parameters = []
        else:
            count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.user_id = @userId"
            count_parameters = [{"name": "@userId", "value": user_id}]
            
        # count_results = list(container.query_items(
        #     query=count_query, 
        #     parameters=count_parameters, 
        #     enable_cross_partition_query=True
        # ))
        # total_count = count_results[0] if count_results else 0
        total_count = 0
        
        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        
        # Ensure page is within valid range
        page = max(1, min(page, total_pages))
        
        # Calculate skip for pagination
        skip = (page - 1) * page_size
        
        # Get paginated results
        if user_id is None:
            query = "SELECT c.user_id, c.session_id, c.timestamp FROM c ORDER BY c.timestamp DESC OFFSET @skip LIMIT @limit"
            parameters = [
                {"name": "@skip", "value": skip},
                {"name": "@limit", "value": page_size}
            ]
        else:
            query = "SELECT c.user_id, c.session_id, c.timestamp FROM c WHERE c.user_id = @userId ORDER BY c.timestamp DESC OFFSET @skip LIMIT @limit"
            parameters = [
                {"name": "@userId", "value": user_id},
                {"name": "@skip", "value": skip},
                {"name": "@limit", "value": page_size}
            ]
            
        # items = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        items = [
            {
                "user_id": "dummy_user",
                "session_id": "dummy_session",
                "timestamp": "dummy_timestamp"
            }
        ]
        
        return {
            "conversations": items,
            "total_count": total_count,
            "page": page,
            "total_pages": total_pages
        }

    def fetch_user_conversation(self, user_id: str, session_id: str):
        container = self.get_container("ag_demo")
        query = "SELECT * FROM c WHERE c.user_id = @userId AND c.session_id = @sessionId"
        parameters = [
            {"name": "@userId", "value": user_id},
            {"name": "@sessionId", "value": session_id},
        ]
        items = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        return items

    def delete_user_conversation(self, user_id: str, session_id: str):
        container = self.get_container("ag_demo")
        query = "SELECT * FROM c WHERE c.user_id = @userId AND c.session_id = @sessionId"
        parameters = [
            {"name": "@userId", "value": user_id},
            {"name": "@sessionId", "value": session_id},
        ]
        items = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        if not items:
            return {"error": f"No conversation found with user_id {user_id} and session_id {session_id}."}
        conversation = items[0]
        response = container.delete_item(item=conversation["id"], partition_key=conversation["user_id"])
        return response

    def delete_user_all_conversations(self, user_id: str):
        container = self.get_container("ag_demo")
        query = "SELECT * FROM c WHERE c.user_id = @userId"
        parameters = [{"name": "@userId", "value": user_id}]
        items = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        if not items:
            return {"error": f"No conversation found with user_id {user_id}."}
        for item in items:
            container.delete_item(item=item["id"], partition_key=item["user_id"])
        return True

if __name__ == "__main__":
    db = CosmosDB()
    pass