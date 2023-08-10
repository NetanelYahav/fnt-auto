from abc import ABC, abstractmethod
import logging
import typing as t
from pydantic import ValidationError
from pprint import pformat
from collections import defaultdict
from fnt_auto.models.base import RestRequest, ItemCreateRes
from fnt_auto.async_api.base import ApiProtocol, ItemRead
from fnt_auto.models.importer import ImportSummary, ItemStatus, ImportStatusType

logger = logging.getLogger(__package__)


class ItemsImporter(ABC):

    def __init__(self, fnt_item_api: ApiProtocol):
        self.fnt_item_api = fnt_item_api
        self.fnt_items_exist: dict[str, ItemRead] = {}
        self.parse_summary: defaultdict[str, int] = defaultdict(int)
        self.import_summary: ImportSummary = ImportSummary()

    @abstractmethod
    async def initialize(self):
        pass

    @abstractmethod
    async def _collect_items(self) -> list[RestRequest]:
        pass

    def identify_key(self, new_item:RestRequest) -> str:
        key = self._identify_key(new_item)
        if key is None:
            raise Exception("Result of new Item identifier formula must not be empty")
        return key
    
    @abstractmethod
    def _identify_key(self, new_item:RestRequest) -> t.Optional[str]:
        pass

    def already_exist(self, item: RestRequest) -> bool:
        return self.identify_key(item) in self.fnt_items_exist
    
    async def _import_items(self, new_items: list[RestRequest]) -> None:
        total = len(new_items)
        logger.info(f"{type(self).__name__}: About to import Items into FNT:")
        logger.info("---------------------------------------------------------")
        for i, item in enumerate(new_items):
            status:t.Optional[ImportStatusType] = None
            item_exist: t.Optional[ItemRead] = None

            item_id = self.identify_key(item)
            logger.info(f"\t{type(self).__name__}: Proccessing Item {i+1}/{total} - {item_id}:")         
 
            if self.already_exist(item):
                logger.info(f"\t\tItem [{item_id}] already exist.")
                
                status = ImportStatusType.EXIST
                item_exist = self.fnt_items_exist[item_id]
                if self.cleanup and hasattr(item_exist, 'elid'):
                    item_elid = getattr(item_exist, 'elid')
                    res = await self.fnt_item_api.delete(item_elid)
                    if res.success:
                        status = ImportStatusType.DELETED
                    else:
                        status = ImportStatusType.FAILED_DELETE
                
                self.import_summary.items.append(ItemStatus(item_req=item, item=item_exist, status=status))
                continue
            
            if self.cleanup:
                continue

            try:
                dcr = await self.fnt_item_api.create(item)
                if dcr.new_item_elid:
                    logger.info(f"\t\tCreated item ELID: [{dcr.new_item_elid}]")
                    item_exist = await self.fnt_item_api.get_by_elid(dcr.new_item_elid)
            except (ValidationError, ValueError) as err:
                status = ImportStatusType.MISSING_ATTRIBUTE
                logger.exception(err)
            except Exception as err:
                status = ImportStatusType.FAILED_CREATE
                logger.exception(err)
            else:
                if dcr.rest_response.success:
                    status = ImportStatusType.CREATED
                elif dcr.already_exist:
                    status = ImportStatusType.EXIST
                else:
                    status = ImportStatusType.FAILED_CREATE

            self.import_summary.items.append(ItemStatus(item_req=item, item=item_exist, status=status))
    
    async def make_import(self, cleanup: bool = False) -> ImportSummary:
        self.cleanup = cleanup
        logger.info(f"{type(self).__name__}: Starting the parsing proccess")
        items = await self._collect_items()
        logger.info(f"{type(self).__name__}: Finish parsing proccess")
        await self._import_items(items)
        logger.info("==============================================================================================")
        logger.info(f"Parse status: {pformat(self.parse_summary)}")
        logger.info(f"Import status: {pformat(self.import_summary.summary)}")
        logger.info("==============================================================================================")
        return self.import_summary