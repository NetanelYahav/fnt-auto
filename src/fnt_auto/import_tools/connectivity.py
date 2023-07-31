from abc import abstractmethod
import typing as t
import asyncio
from fnt_auto.models.base import RestRequest

from fnt_auto.models.connectivity.cable import CableCreateReq, Cable, CableOnJunctionBoxCreateReq ,CableJbToDeviceCreateReq
from fnt_auto.models.connectivity.connection import Connection
from fnt_auto.async_api import FntAsyncAPI
from fnt_auto.resources import utils
from fnt_auto.import_tools.base import ItemsImporter

async def get_existing_connection(fnt_api: FntAsyncAPI) -> dict[str, Cable]:
    cables: list[Cable] = []
    connections: list[Connection] = []

    cables, connections = await asyncio.gather(
        *[fnt_api.connectivity.cable.get_all(), fnt_api.connectivity.connection.get_all()]
    )
    
    cable_exist = utils.to_dict(cables)

    fnt_items_exist:dict[str, Cable] = {}
    for conn in connections:
        cable = cable_exist.get(conn.cable_elid)
        if not cable:
            continue

        side_a_key = f"{conn.id_elid} | {conn.socket_side} | {conn.socket_no}"
        side_z_key = f"{conn.to_id_elid} | {conn.to_socket_side} | {conn.to_socket_no}"
        if conn.table_name == 'STCDEV_JUNCTIONBOX':
            side_a_key = f"{conn.id_elid}"
        if conn.to_table_name == 'STCDEV_JUNCTIONBOX':
            side_z_key = f"{conn.to_id_elid}"
        
        fnt_items_exist[f"{side_a_key} | {side_z_key}"] = cable
        fnt_items_exist[f"{side_z_key} | {side_a_key}"] = cable
        fnt_items_exist[cable.id] = cable

    return fnt_items_exist

class CablesImporter(ItemsImporter):        
    def __init__(self, fnt_api: FntAsyncAPI) -> None:
        super().__init__(fnt_api.connectivity.cable)
        self.fnt_api = fnt_api

    async def initialize(self):
        self.fnt_items_exist = await get_existing_connection(self.fnt_api)

    async def _collect_items(self) -> list[CableCreateReq]:
        return await self.collect_items()
    
    @abstractmethod
    async def collect_items(self) -> list[CableCreateReq]:
        pass

    def _identify_key(self, new_item: CableCreateReq) -> t.Optional[str]:
        if new_item.id:
            return new_item.id
        return f"{new_item.device_elid_a} | {new_item.side_a} | {new_item.port_a} | {new_item.device_elid_z} | {new_item.side_z} | {new_item.port_z}"


class CablesOnJunctionBoxImporter(ItemsImporter):        
    def __init__(self, fnt_api: FntAsyncAPI) -> None:
        super().__init__(fnt_api.connectivity.cable_on_jb)
        self.fnt_api = fnt_api

    async def initialize(self):
        self.fnt_items_exist = await get_existing_connection(self.fnt_api)

    async def _collect_items(self) -> list[CableOnJunctionBoxCreateReq]:
        return await self.collect_items()
    
    @abstractmethod
    async def collect_items(self) -> list[CableOnJunctionBoxCreateReq]:
        pass

    def _identify_key(self, new_item: CableOnJunctionBoxCreateReq) -> t.Optional[str]:
        if new_item.cable_id:
            return new_item.cable_id
        if isinstance(new_item, CableJbToDeviceCreateReq):
            return f"{new_item.junction_box_elid} | {new_item.device_elid} | {new_item.side} | {new_item.port}"
        raise NotImplementedError()
