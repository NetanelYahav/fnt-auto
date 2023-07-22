import logging
from abc import abstractmethod
from fnt_auto.models.base import RestRequest
from fnt_auto.models.location.campus import CampusCreateReq
from fnt_auto.models.location.building import BuildingCreateReq
from fnt_auto.async_api import FntAsyncAPI
from fnt_auto.resources import utils
from fnt_auto.import_tools.base import ItemsImporter

logger = logging.getLogger(__name__)


class CampusesImporter(ItemsImporter):        

    def __init__(self, fnt_api: FntAsyncAPI) -> None:
        super().__init__(fnt_api.location.campus)
        self.fnt_api = fnt_api

    async def initialize(self):
        self.fnt_items_exist = utils.to_dict(await self.fnt_api.location.campus.get_all(), key='name')

    async def _collect_items(self) -> list[CampusCreateReq]:
        return await self.collect_items()
    
    @abstractmethod
    async def collect_items(self) -> list[CampusCreateReq]:
        pass

    def _identify_key(self, campus: CampusCreateReq) -> str:
        return campus.name
    

class BuildingsImporter(ItemsImporter):        

    def __init__(self, fnt_api: FntAsyncAPI) -> None:
        super().__init__(fnt_api.location.building)
        self.fnt_api = fnt_api

    async def initialize(self):
        self.fnt_campuses_by_elid = utils.to_dict(await self.fnt_api.location.campus.get_all())
        self.fnt_items_exist = utils.convert_to_dict(await self.fnt_api.location.building.get_all(), keys=['campus', 'name'])

    async def _collect_items(self) -> list[BuildingCreateReq]:
        return await self.collect_items()
    
    @abstractmethod
    async def collect_items(self) -> list[BuildingCreateReq]:
        pass

    def _identify_key(self, building: BuildingCreateReq) -> str:
        campus_name = self.fnt_campuses_by_elid[building.campus_elid].name
        return f"{campus_name} | {building.name}"