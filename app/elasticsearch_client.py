from elasticsearch import Elasticsearch
from config import settings
import asyncio
from functools import wraps


def run_in_threadpool(func):
    """Decorator to run sync functions in thread pool"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    return wrapper


class ElasticsearchClient:
    def __init__(self):
        self.client = Elasticsearch(
            [f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"]
        )

    async def health_check(self):
        try:
            health = await self._get_cluster_health()
            return {
                "status": health["status"],
                "cluster_name": health["cluster_name"],
                "number_of_nodes": health["number_of_nodes"],
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @run_in_threadpool
    def _get_cluster_health(self):
        return self.client.cluster.health()

    async def index_exists(self, index_name: str = None):
        index_name = index_name or settings.ELASTICSEARCH_INDEX
        try:
            exists = await self._check_index_exists(index_name)
            return exists
        except Exception as e:
            return False

    @run_in_threadpool
    def _check_index_exists(self, index_name: str):
        return self.client.indices.exists(index=index_name).body

    async def search_recipes(self, query_body: dict, index_name: str = None):
        """Execute search query against recipes index"""
        index_name = index_name or settings.ELASTICSEARCH_INDEX
        try:
            result = await self._execute_search(index_name, query_body)
            return result
        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")

    @run_in_threadpool
    def _execute_search(self, index_name: str, query_body: dict):
        return self.client.search(index=index_name, body=query_body)

    async def bulk_index_recipes(self, recipes: list, index_name: str = None):
        """Bulk index a list of recipes"""
        index_name = index_name or settings.ELASTICSEARCH_INDEX

        # Prepare bulk actions
        actions = []
        for recipe in recipes:
            action = {"_index": index_name, "_source": recipe}
            actions.append(action)

        try:
            result = await self._execute_bulk(actions)
            return result
        except Exception as e:
            raise Exception(f"Bulk indexing failed: {str(e)}")

    @run_in_threadpool
    def _execute_bulk(self, actions: list):
        from elasticsearch.helpers import bulk

        return bulk(self.client, actions)

    async def create_index_with_mapping(
        self, mapping_data: dict, index_name: str = None
    ):
        """Create index with proper mapping"""
        index_name = index_name or settings.ELASTICSEARCH_INDEX
        try:
            result = await self._create_index(index_name, mapping_data)
            return result
        except Exception as e:
            raise Exception(f"Index creation failed: {str(e)}")

    @run_in_threadpool
    def _create_index(self, index_name: str, mapping_data: dict):
        return self.client.indices.create(index=index_name, body=mapping_data)


es_client = ElasticsearchClient()
