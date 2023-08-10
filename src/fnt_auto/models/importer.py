from enum import Enum
from typing import Optional, TypeVar, Generic
from pydantic import Field

from fnt_auto.models import BaseModel
from fnt_auto.models.base import ItemRead
from fnt_auto.models.api import RestRequest

ITEM = TypeVar('ITEM', bound=ItemRead)

class ImportStatusType(str, Enum):
    CREATED = 'Just Created'
    DELETED = 'Just Deleted'
    UPDATED = 'Just Updated'
    FAILED_CREATE = 'Failed to Create'
    FAILED_DELETE = 'Failed to Delete'
    EXIST = 'Already Exist'
    MISSING_ATTRIBUTE = 'Missing Attribute'

class ItemStatus(BaseModel):
    item_req: RestRequest
    item: Optional[ItemRead] = None
    status: ImportStatusType
    

class ImportSummary(BaseModel):
    items: list[ItemStatus] = Field(default_factory=list)
    
    @property
    def items_created(self) -> list[ItemRead]:
        ret_items: list[ItemRead] = []
        for item_status in self.items:
            if item_status.status != ImportStatusType.CREATED:
                continue
            if item_status.item:
                ret_items.append(item_status.item)
        return ret_items
    
    @property
    def items_exist(self) -> list[ItemRead]:
        ret_items: list[ItemRead] = []
        for item_status in self.items:
            if item_status.status != ImportStatusType.EXIST:
                continue
            if item_status.item:
                ret_items.append(item_status.item)
        return ret_items
    
    @property
    def items_imported(self) -> list[ItemRead]:
        ret_items: list[ItemRead] = []
        for item_status in self.items:
            if item_status.status in (ImportStatusType.EXIST, ImportStatusType.CREATED) and item_status.item:
                ret_items.append(item_status.item)
        return ret_items
    
    @property
    def failed_create(self) -> list[RestRequest]:
        ret_items: list[RestRequest] = []
        for item_status in self.items:
            if item_status.status != ImportStatusType.FAILED_CREATE:
                continue
            ret_items.append(item_status.item_req)
        return ret_items
    
    @property
    def attribute_missing(self) -> list[RestRequest]:
        ret_items: list[RestRequest] = []
        for item_status in self.items:
            if item_status.status != ImportStatusType.MISSING_ATTRIBUTE:
                continue
            ret_items.append(item_status.item_req)
        return ret_items
    
    @property
    def items_deleted(self) -> list[RestRequest]:
        ret_items: list[RestRequest] = []
        for item_status in self.items:
            if item_status.status != ImportStatusType.DELETED:
                continue
            ret_items.append(item_status.item_req)
        return ret_items
    
    
    @property
    def failed_delete(self) -> list[RestRequest]:
        ret_items: list[RestRequest] = []
        for item_status in self.items:
            if item_status.status != ImportStatusType.FAILED_DELETE:
                continue
            ret_items.append(item_status.item_req)
        return ret_items
    
    @property
    def summary(self) -> dict[str, int]:
        total_created = len(self.items_created)
        total_exist = len(self.items_exist)
        return {
            'Total': len(self.items),
            'Good': total_exist + total_created,
            'JustImported': total_created,
            'FailedCreate': len(self.failed_create),
            'AttributeMissing': len(self.attribute_missing),
            'JustDeleted': len(self.items_deleted),
            'FailedDelete': len(self.failed_delete)
        }