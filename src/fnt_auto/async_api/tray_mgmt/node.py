import typing as t
from pydantic import ValidationError

from fnt_auto.async_api.base import AsyncBaseAPI
from fnt_auto.models.base import ItemCreateRes
from fnt_auto.models.tray_mgmt.node import NodeCreateReq, Node, NodeMaster, NodeCreateAdvanceReq

class NodeAPI(AsyncBaseAPI):

    async def create(self, node: NodeCreateReq) -> 'ItemCreateRes':
        if isinstance(node, NodeCreateAdvanceReq):
            if(master_data:=await self.get_master_data(node.type)) is None:
                raise ValueError("Node type is not exist")
            node.type_elid = master_data.elid
            from fnt_auto.async_api.location import ZoneAPI
            zone_api = ZoneAPI(self._fnt_client)
            if not (zone_data:=await zone_api.get_by_query(node.zone)):
                raise ValueError("Zone is not exist")
            node.zone_elid = zone_data[0].elid
            
        return ItemCreateRes(
            rest_request=node.model_copy(),
            rest_response = await self.rest_request('node', 'create', node)
        )

    async def get_all(self) -> list[Node]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('node', 'query', req)
        return self.parse_rest_response(Node, response)
    
    async def get_all_types(self) -> list[NodeMaster]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('nodeType', 'query', req)
        return self.parse_rest_response(NodeMaster, response)
        
    async def get_master_data(self, type:str) -> t.Optional[NodeMaster]:
        req = {'restrictions': {'type': {'value': type, 'operator': '='}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('nodeType', 'query', req)
        if (nodes:=self.parse_rest_response(NodeMaster, response)):
            return nodes[0]