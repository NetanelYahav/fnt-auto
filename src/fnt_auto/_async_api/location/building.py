from typing import Optional
from fnt_auto._async_api.base import AsyncBaseAPI
from fnt_auto.models.zones.building import BuildingCreate
from fnt_auto.models.api import RestResponse


class BuildingAPI(AsyncBaseAPI):

    async def create_building(self, building: BuildingCreate, session_id:Optional[str]=None) -> 'RestResponse': 
        building.rest_response = await self.rest_request('building', 'create', building.to_rest_request(), session_id=session_id)
        return building.rest_response # type: ignore
        