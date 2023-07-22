from typing import Optional
from fnt_auto.async_api.base import AsyncBaseAPI
from fnt_auto.models.base import ItemCreateRes
from fnt_auto.models.location.building import BuildingCreateReq, Building

class BuildingAPI(AsyncBaseAPI):

    async def create(self, building: BuildingCreateReq) -> 'ItemCreateRes':
        return ItemCreateRes(
            rest_request = building.model_copy(),
            rest_response = await self.rest_action_request('building', 'create', building)
        )
        
    
    async def get_all(self) -> list[Building]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('building', 'query', req)
        return self.parse_rest_response(Building, response)
        