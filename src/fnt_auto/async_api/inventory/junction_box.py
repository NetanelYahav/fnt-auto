from typing import Optional
from fnt_auto.async_api.base import AsyncBaseAPI
from fnt_auto.models import RWModel
from fnt_auto.models.base import ItemCreateRes
from fnt_auto.models.inventory.device import DeviceMaster
from fnt_auto.models.inventory.junction_box import JunctionBoxCreateReq, JunctionBox, JunctionBoxCreateInZoneReq, JunctionBoxQuery
from fnt_auto.models.inventory.junction_box import JunctionBoxFistCreateReq, JunctionBoxFistCreateInZoneReq, JunctionBoxQuery

class JunctionBoxAPI(AsyncBaseAPI):

    async def create(self, JunctionBox: JunctionBoxCreateReq) -> 'ItemCreateRes':
        operation = 'placeInNode'
        if isinstance(JunctionBox, JunctionBoxCreateInZoneReq):
            operation = 'placeInZone'
        
        return ItemCreateRes(
            rest_request=JunctionBox.model_copy(),
            rest_response = await self.rest_request('junctionBox', operation, JunctionBox)
        )
    
    async def get_all(self) -> list[JunctionBox]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('junctionBox', 'query', req)
        return self.parse_rest_response(JunctionBox, response)
    
    async def get_by_query(self, jb: JunctionBoxQuery) -> list[JunctionBox]:
        response = await self.rest_request('junctionBox', 'queryExtended', jb)
        return self.parse_rest_response(JunctionBox, response)
    
class JunctionBoxFistAPI(AsyncBaseAPI):

    async def create(self, JunctionBox: JunctionBoxFistCreateReq) -> 'ItemCreateRes':
        operation = 'placeInNode'
        if isinstance(JunctionBox, JunctionBoxFistCreateInZoneReq):
            operation = 'placeInZone'
        
        return ItemCreateRes(
            rest_request=JunctionBox.model_copy(),
            rest_response = await self.rest_request('junctionBoxFist', operation, JunctionBox)
        )
    
    async def get_all(self) -> list[JunctionBox]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('junctionBoxFist', 'query', req)
        return self.parse_rest_response(JunctionBox, response)
    
    async def get_by_query(self, jb: JunctionBoxQuery) -> list[JunctionBox]:
        response = await self.rest_request('junctionBoxFist', 'queryExtended', jb)
        return self.parse_rest_response(JunctionBox, response)
    
    async def get_all_types(self) -> list[DeviceMaster]:
        req = {'restrictions': {'function': {'value': 'JUNCTION_BOX', 'operator': '='}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('deviceMaster', 'query', req)
        return self.parse_rest_response(DeviceMaster, response)