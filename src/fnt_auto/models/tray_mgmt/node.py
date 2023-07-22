from typing import Optional
from pydantic import Field, computed_field
from datetime import datetime

from fnt_auto.models.api import RestRequest
from fnt_auto.models.base import CustumAttribute, Link, RWModel

class NodeMaster(RWModel):
    elid: str
    description: str
    manufacturer: str
    type: str

class NodeCustomAttr(CustumAttribute):
    c_node_owner: Optional[str] = None
    c_remark: Optional[str] = None
    c_node_addr: Optional[str] = None
    c_node_addr2: Optional[str] = None
    c_import_origin: Optional[str] = None
    c_exec_contractor: Optional[datetime] = None
    c_last_seen: Optional[datetime] = None

class NodeAttr(RWModel):
    id: Optional[str] = None
    visible_id: Optional[str] = None
    description: Optional[str] = None
    coord_x: Optional[float] = None
    coord_y: Optional[float] = None
    coord_z: Optional[float] = None
    coord_system: Optional[str] = None
    function: Optional[str] = None




class NodeCreateReq(RestRequest, NodeAttr, NodeCustomAttr):
    type_elid: str = Field(..., exclude=True)
    zone_elid: str = Field(..., exclude=True)

    @computed_field
    def create_link_node_type(self) -> Link:
        return Link(linked_elid=self.type_elid)
    
    @computed_field
    def create_link_zone(self) -> Link:
        return Link(linked_elid=self.zone_elid)
    

class Node(NodeAttr, NodeCustomAttr, NodeMaster):
    elid: str
    zone_elid: str
    campus_elid: str
    floor_elid: Optional[str]
    room_elid: Optional[str]
    status_action: int
