import typing as t
from pydantic import ValidationError

from fnt_auto.async_api.base import AsyncBaseAPI
from fnt_auto.models.base import ItemCreateRes
from fnt_auto.models.tray_mgmt.tray_mgmt import TraySectionCreateReq, TraySection, TraySectionMaster

class TraySectionAPI(AsyncBaseAPI):

    async def create(self, tray_section: TraySectionCreateReq) -> 'ItemCreateRes':          
        return ItemCreateRes(
            rest_request=tray_section.model_copy(),
            rest_response = await self.rest_request('traySection', 'create', tray_section)
        )

    async def get_all(self) -> list[TraySection]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('traySection', 'query', req)
        return self.parse_rest_response(TraySection, response)
    
    async def get_all_types(self) -> list[TraySectionMaster]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('traySectionType', 'query', req)
        return self.parse_rest_response(TraySectionMaster, response)
        
    async def get_master_data(self, type:str) -> t.Optional[TraySectionMaster]:
        req = {'restrictions': {'type': {'value': type, 'operator': '='}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('traySectionType', 'query', req)
        if (nodes:=self.parse_rest_response(TraySectionMaster, response)):
            return nodes[0]