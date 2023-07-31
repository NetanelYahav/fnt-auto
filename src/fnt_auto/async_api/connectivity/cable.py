from fnt_auto.async_api.base import AsyncBaseAPI
from fnt_auto.models.base import ItemCreateRes, RestResponse
from fnt_auto.models.connectivity.cable import CableCreateReq, CableMaster, Cable, CableQuery, CableOnJunctionBoxCreateReq

class CableAPI(AsyncBaseAPI):

    async def create(self, cable: CableCreateReq) -> 'ItemCreateRes':          
        return ItemCreateRes(
            rest_request=cable.model_copy(),
            rest_response = await self.rest_request('dataCable', 'connect', cable)
        )

    async def get_all(self) -> list[Cable]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('dataCable', 'query', req)
        return self.parse_rest_response(Cable, response)
    
    
    async def get_by_query(self, device: CableQuery) -> list[Cable]:
        response = await self.rest_request('dataCable', 'query', device)
        return self.parse_rest_response(Cable, response)
    

    async def get_all_types(self) -> list[CableMaster]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('cableMaster', 'query', req)
        return self.parse_rest_response(CableMaster, response)
    
    async def delete(self, elid: str) -> 'RestResponse':
        data = {"releaseService": "true", "releaseSignalpath": "true", "releaseTrmRoute": "true"}
        return await self._fnt_client.rest_elid_request('dataCable', elid, 'delete', data)
    

class CableOnJunctionBoxAPI(AsyncBaseAPI):
    async def create(self, cable: CableOnJunctionBoxCreateReq) -> 'ItemCreateRes':          
        item_create_res = ItemCreateRes(
            rest_request=cable.model_copy(),
            rest_response = await self.rest_elid_request('junctionBoxFist', cable.junction_box_elid, 'connect', cable)
        )
        
        if isinstance(item_create_res.rest_response.data, dict):
            created_cables = item_create_res.rest_response.data.get('createdCables')
            if created_cables:
                item_create_res.new_item_elid = created_cables[0].get('cableElid')
        return item_create_res

    async def delete(self, elid: str) -> 'RestResponse':
        data = {"releaseService": "true", "releaseSignalpath": "true", "releaseTrmRoute": "true"}
        return await self._fnt_client.rest_elid_request('dataCable', elid, 'delete', data)