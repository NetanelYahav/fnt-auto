
from abc import abstractmethod
import logging
import typing as t
from fnt_auto.models.inventory.device import DeviceCreateReq
from fnt_auto.models.inventory.junction_box import JunctionBoxFistCreateReq
from fnt_auto.async_api import FntAsyncAPI
from fnt_auto.resources import utils
from fnt_auto.import_tools.base import ItemsImporter

logger = logging.getLogger(__name__)

class DevicesImporter(ItemsImporter):        

    def __init__(self, fnt_api: FntAsyncAPI) -> None:
        super().__init__(fnt_api.inventory.device)
        self.fnt_api = fnt_api

    async def initialize(self):
        self.fnt_items_exist = utils.to_dict(await self.fnt_api.inventory.device.get_all(), key='id')

    async def _collect_items(self) -> list[DeviceCreateReq]:
        return await self.collect_items()
    
    @abstractmethod
    async def collect_items(self) -> list[DeviceCreateReq]:
        pass

    def _identify_key(self, new_item: DeviceCreateReq) -> t.Optional[str]:
        return new_item.id
    

class JunctionBoxesFistImporter(ItemsImporter):        

    def __init__(self, fnt_api: FntAsyncAPI) -> None:
        super().__init__(fnt_api.inventory.junction_box_fist)
        self.fnt_api = fnt_api

    async def initialize(self):
        self.fnt_items_exist = utils.to_dict(await self.fnt_api.inventory.junction_box_fist.get_all(), key='id')

    async def _collect_items(self) -> list[JunctionBoxFistCreateReq]:
        return await self.collect_items()
    
    @abstractmethod
    async def collect_items(self) -> list[JunctionBoxFistCreateReq]:
        pass

    def _identify_key(self, new_item: JunctionBoxFistCreateReq) -> t.Optional[str]:
        return new_item.id
