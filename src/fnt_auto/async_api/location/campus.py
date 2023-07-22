from fnt_auto.async_api.base import AsyncBaseAPI
from fnt_auto.models.base import ItemCreateRes
from fnt_auto.models.location.campus import CampusCreateReq, Campus

class CampusAPI(AsyncBaseAPI):

    async def create(self, campus: CampusCreateReq) -> 'ItemCreateRes':
        return ItemCreateRes(
            rest_request = campus.model_copy(),
            rest_response = await self.rest_action_request('campus', 'create', campus)
        )
    
    async def get_all(self) -> list[Campus]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('campus', 'query', req)
        return self.parse_rest_response(Campus, response)