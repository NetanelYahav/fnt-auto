from typing import Optional

from fnt_auto.models.api import RestRequest
from fnt_auto.models.base import CustumAttribute, RWModel, ItemRead

class CampusCustomAttr(CustumAttribute):
    pass

class CampusAttr(RWModel):
    description: Optional[str] = None
    remark: Optional[str] = None
    continent: Optional[str] = None
    country: Optional[str] = None
    location: Optional[str] = None

class CampusCreateReq(RestRequest, CampusAttr, CampusCustomAttr):
    name: str
    
class Campus(ItemRead, CampusAttr, CampusCustomAttr):
    name: str
