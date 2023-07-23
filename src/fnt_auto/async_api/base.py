import typing
import logging
import typing
from abc import ABC

from fnt_auto.async_api.async_client import FntAsyncClient
from fnt_auto.models.api import RestRequest ,RestResponse
from fnt_auto.models import RWModel
from fnt_auto.models.base import ItemActionRes, ItemCreateRes

logger = logging.getLogger(__package__)

T = typing.TypeVar('T', bound=RWModel)

class AsyncBaseAPI(ABC):
    _fnt_client: FntAsyncClient

    def __init__(self, fnt_client: FntAsyncClient) -> None:
        self._fnt_client = fnt_client
 
    async def rest_request(self, entity: str, operation: str, rest_req: RestRequest) -> 'RestResponse':
        return await self._fnt_client.rest_request(entity, operation, rest_req.to_rest_request())

    @classmethod
    def parse_rest_response(cls, model_cls:type[T], response: RestResponse) -> list[T]:
        items: list[T] = []
        if response.data is None:
            return []
        
        if isinstance(response.data, list):
            for item in response.data:
                items.append(model_cls(**item))
        else:
            for item in response.data.values():
                items.append(model_cls(**item))
        return items
    
    async def create(self, device: RestRequest) -> 'ItemCreateRes':
        raise NotImplementedError("Method Create not implemeted")
    
    async def get_all(self) -> list[RWModel]:
        raise NotImplementedError("Method get_all not implemeted")
    
    async def get_all_types(self) -> list[RWModel]:
        raise NotImplementedError("Method get_all_types not implemeted")
    
    async def get_by_query(self, query: RWModel) -> list[RWModel]:
        raise NotImplementedError("Method get_by_query not implemeted")
