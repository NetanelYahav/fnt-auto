from abc import ABC, abstractmethod
import logging
import typing as t
from pydantic import ValidationError
from pprint import pformat
from collections import defaultdict
from fnt_auto.models.base import RestRequest
from fnt_auto.async_api.base import AsyncBaseAPI

logger = logging.getLogger(__name__)

class ItemsImporter(ABC):

    def __init__(self, fnt_item_api: AsyncBaseAPI):
        self.fnt_item_api = fnt_item_api
        self.fnt_items_exist = {}
        self.parse_summary = defaultdict(int)

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
    
    async def _import_items(self, new_items: list[RestRequest]) -> dict[str, int]:
        summary = {
            'Total': 0,
            'Good': 0,
            'JustImported': 0,
            'FailedCreate': 0,
            'AttributeMissing': 0
        }

        total = len(new_items)
        summary['Total'] = total
        logger.info(f"{type(self).__name__}: About to import Items into FNT:")
        logger.info("---------------------------------------------------------")
        for i, item in enumerate(new_items):
            item_id = self.identify_key(item)
            logger.info(f"\t{type(self).__name__}: Proccessing Item {i+1}/{total} - {item_id}:")         
 
            if self.already_exist(item):
                logger.info(f"      Item [{item_id}] already exist.")
                summary['Good'] += 1
                continue
            try:
                dcr = await self.fnt_item_api.create(item)
            except (ValidationError, ValueError):
                summary['AttributeMissing'] += 1
                continue
            except Exception:
                summary['FailedCreate'] += 1

            
            if dcr.rest_response.success:
                summary['Good'] += 1
                summary['JustImported'] += 1
            elif dcr.already_exist:
                summary['Good'] += 1
            else:
                summary['FailedCreate'] += 1
        return summary
    
    async def make_import(self):
        logger.info(f"{type(self).__name__}: Starting the parsing proccess")
        items = await self._collect_items()
        logger.info(f"{type(self).__name__}: Finish parsing proccess")
        import_summary = await self._import_items(items)
        logger.info("==============================================================================================")
        logger.info(f"Parse status: {pformat(self.parse_summary)}")
        logger.info(f"Import status: {pformat(import_summary)}")
        logger.info("==============================================================================================")