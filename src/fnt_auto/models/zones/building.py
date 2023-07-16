from typing import Optional

from pydantic import Field, computed_field
from typing import Dict, Any

from fnt_auto.models.base import ItemCreate, CustumAttribute, Link, RWModel


class BuildingCustomAttr(CustumAttribute):
    c_x: Optional[float] = None
    c_y: Optional[float] = None
    c_floors_num: Optional[int] = None
    c_business_num: Optional[int] = None
    c_residential_num: Optional[int] = None

class BuildingAttr(BuildingCustomAttr):
    description: Optional[str] = None
    remark: Optional[str] = None

class BuildingCreate(ItemCreate, BuildingAttr):
    name: str
    campus_elid: str = Field(..., exclude=True)
    
    @computed_field
    def create_link_campus(self) -> Link:
        return Link(linked_elid=self.campus_elid)
