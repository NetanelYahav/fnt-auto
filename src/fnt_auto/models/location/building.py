from typing import Optional

from pydantic import Field, computed_field
from typing import Dict, Any

from fnt_auto.models.api import RestRequest
from fnt_auto.models.base import CustumAttribute, Link, RWModel, ItemRead


class BuildingCustomAttr(CustumAttribute):
    c_x: Optional[float] = None
    c_y: Optional[float] = None
    c_floors_num: Optional[int] = None
    c_business_num: Optional[int] = None
    c_residential_num: Optional[int] = None
    
    c_address: Optional[str] = None
    c_building_owner: Optional[str] = None
    c_building_status: Optional[str] = None
    c_building_type: Optional[str] = None
    c_local_authority: Optional[str] = None
    c_polygon: Optional[str] = None
    c_pop: Optional[str] = None

class BuildingAttr(RWModel):
    description: Optional[str] = None
    remark: Optional[str] = None


class BuildingCreateReq(RestRequest, BuildingAttr, BuildingCustomAttr):
    name: str
    campus_elid: str = Field(..., exclude=True)
    
    @computed_field
    def create_link_campus(self) -> Link:
        return Link(linked_elid=self.campus_elid)

class Building(ItemRead, BuildingAttr, BuildingCustomAttr):
    name: str
    campus: str