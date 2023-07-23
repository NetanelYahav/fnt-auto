
from abc import abstractmethod
import logging
import typing as t
from fnt_auto.models.tray_mgmt.node import NodeCreateReq
from fnt_auto.async_api import FntAsyncAPI
from fnt_auto.resources import utils
from fnt_auto.import_tools.base import ItemsImporter

logger = logging.getLogger(__name__)

class NodesImporter(ItemsImporter):        

    def __init__(self, fnt_api: FntAsyncAPI) -> None:
        super().__init__(fnt_api.tray_mgmt.node)
        self.fnt_api = fnt_api

    async def initialize(self):
        self.fnt_items_exist = utils.to_dict(await self.fnt_api.tray_mgmt.node.get_all(), key='id')

    async def _collect_items(self) -> list[NodeCreateReq]:
        return await self.collect_items()
    
    @abstractmethod
    async def collect_items(self) -> list[NodeCreateReq]:
        pass

    def _identify_key(self, new_item: NodeCreateReq) -> t.Optional[str]:
        return new_item.id
