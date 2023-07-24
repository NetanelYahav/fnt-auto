from typing import Optional
from fnt_auto.async_api.base import AsyncBaseAPI
from fnt_auto.models import RWModel
from fnt_auto.models.base import ItemCreateRes
from fnt_auto.models.inventory.device import DeviceCreateReq, Device, DeviceCreateInZoneReq, DeviceMaster, DeviceQuery, DeviceMasterQuery

class DeviceAPI(AsyncBaseAPI):

    async def create(self, device: DeviceCreateReq) -> 'ItemCreateRes':
        operation = 'placeInCabinet'
        if isinstance(device, DeviceCreateInZoneReq):
            operation = 'placeInZone'
        
        return ItemCreateRes(
            rest_request=device.model_copy(),
            rest_response = await self.rest_request('deviceAll', operation, device)
        )
    
    async def get_all(self) -> list[Device]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('deviceAll', 'query', req)
        return self.parse_rest_response(Device, response)
    
    async def get_all_types(self) -> list[DeviceMaster]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('deviceMaster', 'query', req)
        return self.parse_rest_response(DeviceMaster, response)
    
    async def get_types_by_query(self, device: DeviceMasterQuery) -> list[DeviceMaster]:
        response = await self.rest_request('deviceMasterDevice', 'query', device)
        return self.parse_rest_response(DeviceMaster, response)
    
    async def get_by_query(self, device: DeviceQuery) -> list[Device]:
        response = await self.rest_request('deviceAll', 'queryExtended', device)
        return self.parse_rest_response(Device, response)