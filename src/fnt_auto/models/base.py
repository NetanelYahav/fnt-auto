import logging
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from httpx._status_codes import codes

from fnt_auto.models import RWModel
from fnt_auto.models.api import RestResponse

logger = logging.getLogger(__name__)

class ItemStatusOpt(Enum):
    SUCCESS = auto()
    ALREADY_EXIST = auto()
    FAILED = auto()
    INIT = auto()


class CustumAttribute(RWModel):
    pass

class ItemAction(RWModel):
    _rest_response: Optional[RestResponse] = None
    _status: ItemStatusOpt = ItemStatusOpt.INIT

    @property
    def status(self) -> ItemStatusOpt:
        return self._status

    @status.setter
    def status(self, value:ItemStatusOpt):
        self._status = value

    @property
    def rest_response(self) -> Optional[RestResponse]:
        return self._rest_response

    @rest_response.setter
    def rest_response(self, value:RestResponse):
        self._rest_response = value

    def to_rest_request(self) -> Dict[str, Any]:
        # attr_class = type(self)
        # self_attr = attr_class(**{**self.model_dump(exclude_defaults=True), **self.model_dump(exclude_unset=True), **self.model_dump(exclude_none=True)})
        # if curr_db_attr is not None:
        #     curr_attr = attr_class(**{k.lower(): v for k, v in curr_db_attr.items()})
        #     if curr_attr == self_attr:
        #         return {}

        # update_attr = {}
        # for field_name, value in self_attr.model_dump(exclude_unset=True).items():
        #     extra = (attr_class.model_fields[field_name].field_info.extra)
        #     if extra.get('rest_name') is None:
        #         continue
        #     fn = extra.get('rest_name', field_name)

        #     val_as_obj = getattr(self_attr, field_name)
        #     if issubclass(type(val_as_obj), List) and value:
        #         value = []
        #         for val in val_as_obj:
        #             if issubclass(type(val), RWModel):
        #                 value.append(val.prepare_request())
        #     elif issubclass(type(val_as_obj), RWModel):
        #         value = val.prepare_request()

        #     if fn.startswith('createLink'):
        #         value = {'linkedElid': value}
        #     update_attr[fn] = value
        # return update_attr

        return self.model_dump(by_alias=True, exclude_defaults=True)

class ItemCreate(ItemAction):
    _new_item_elid: Optional[str] = None

    @property
    def new_item_elid(self) -> Optional[str]:
        return self._new_item_elid
    
    @property
    def rest_response(self) -> Optional[RestResponse]:
        return self._rest_response

    @rest_response.setter
    def rest_response(self, value:RestResponse):
        self._rest_response = value
        if value.status_code == codes.OK and value.data:
            self._new_item_elid = value.data.get('elid')
            self.status = ItemStatusOpt.SUCCESS
        elif value.status_code == codes.BAD_REQUEST:
            if value.message and 'already exists' in value.message:
                self.status = ItemStatusOpt.ALREADY_EXIST

class Link(RWModel):
    linked_elid: str