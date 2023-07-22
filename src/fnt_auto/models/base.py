import logging
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from httpx._status_codes import codes
from pydantic import validator
from fnt_auto.models import RWModel
from fnt_auto.models.api import RestRequest, RestResponse

logger = logging.getLogger(__name__)


class CustumAttribute(RWModel):
    pass

class ItemActionRes(RWModel):
    rest_request: RestRequest
    rest_response: RestResponse


class ItemCreateRes(ItemActionRes):
    new_item_elid: Optional[str] = None

    @validator('rest_response')
    def validate_rest_response(cls, response:RestResponse, values:dict) -> RestResponse:
        if response.success and response.data:
            if isinstance(response.data, dict):
                values['new_item_elid'] = response.data.get('elid')
        
        logger.info(f"Created item ELID: [{values.get('new_item_elid')}]")
        return response
    
    @property
    def already_exist(self) -> bool:
        if self.rest_response.success:
            return False

        if self.rest_response.message:
            if 'already in use' in self.rest_response.message:
                return True
        return False

class Link(RWModel):
    linked_elid: str