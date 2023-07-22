from fnt_auto.async_api.base import AsyncBaseAPI
from fnt_auto.models.base import ItemCreateRes
from fnt_auto.models.tray_mgmt.node import NodeCreateReq, Node, NodeMaster

class NodeAPI(AsyncBaseAPI):

    async def create(self, node: NodeCreateReq) -> 'ItemCreateRes':
        return ItemCreateRes(
            rest_request=node.model_copy(),
            rest_response = await self.rest_action_request('node', '', node)
        )
    
    async def get_all(self) -> list[Node]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('node', 'query', req)
        return self.parse_rest_response(Node, response)
    
    async def get_all_types(self) -> list[NodeMaster]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('nodeType', 'query', req)
        return self.parse_rest_response(NodeMaster, response)