from typing import Optional
from abc import ABC
from pydantic import Field, computed_field
from typing import Dict, Any

from fnt_auto.models.api import RestRequest
from fnt_auto.models.base import CustumAttribute, Link, RWModel, ItemRead
from fnt_auto.models.api import RestQuery

class JunctionBoxCustomAttr(CustumAttribute):
    c_jb_type: Optional[str] = None
    c_work_status: Optional[str] = None


class JunctionBoxAttr(RWModel):
    id: Optional[str] = None
    visible_id: Optional[str] = None
    remark: Optional[str] = None


class JunctionBoxCreateReq(ABC, RestRequest, JunctionBoxAttr, JunctionBoxCustomAttr):
    type_elid: str = Field(..., exclude=True)
    
    def __new__(cls, *args, **kwargs):
        if cls is JunctionBoxCreateReq:
            raise TypeError(f"Cannot instantiate {cls.__name__} directly.")
        return super(JunctionBoxCreateReq, cls).__new__(cls)
    
    @computed_field
    def create_link_device_master_junction_box(self) -> Link:
        return Link(linked_elid=self.type_elid)

class JunctionBoxCreateInZoneReq(JunctionBoxCreateReq):
    zone_elid: str = Field(..., exclude=True)
    
    @computed_field
    def create_link_zone(self) -> Link:
        return Link(linked_elid=self.zone_elid)
    
class JunctionBoxCreateInNodeReq(JunctionBoxCreateReq):
    node_elid: str = Field(..., exclude=True)
    
    @computed_field
    def create_link_node(self) -> Link:
        return Link(linked_elid=self.node_elid)


class JunctionBoxFistCreateReq(ABC, RestRequest, JunctionBoxAttr, JunctionBoxCustomAttr):
    type_elid: str = Field(..., exclude=True)
    
    def __new__(cls, *args, **kwargs):
        if cls is JunctionBoxFistCreateReq:
            raise TypeError(f"Cannot instantiate {cls.__name__} directly.")
        return super(JunctionBoxFistCreateReq, cls).__new__(cls)
    
    @computed_field
    def create_link_device_master_junction_box_fist(self) -> Link:
        return Link(linked_elid=self.type_elid)

class JunctionBoxFistCreateInZoneReq(JunctionBoxFistCreateReq):
    zone_elid: str = Field(..., exclude=True)
    
    @computed_field
    def create_link_zone(self) -> Link:
        return Link(linked_elid=self.zone_elid)
    
class JunctionBoxFistCreateInNodeReq(JunctionBoxFistCreateReq):
    node_elid: str = Field(..., exclude=True)
    
    @computed_field
    def create_link_node(self) -> Link:
        return Link(linked_elid=self.node_elid)
    


class JunctionBox(ItemRead, JunctionBoxAttr, JunctionBoxCustomAttr):
    zone_elid: Optional[str] = None
    id: str
    type: Optional[str] = None


class JunctionBoxQuery(RestQuery):
    campus_elid: Optional[str] = Field(default=None,)
    building_elid: Optional[str] = Field(default=None)
    floor_elid: Optional[str] = Field(default=None)
    room_elid: Optional[str] = Field(default=None)
    zone_elid: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    plan_status: Optional[str] = Field(default=None)
    type_elid: Optional[str] = Field(default=None)