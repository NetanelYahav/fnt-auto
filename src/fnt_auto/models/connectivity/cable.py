import logging
from typing import Optional
from pydantic import Field, computed_field, validator
from datetime import datetime
from enum import Enum
from abc import ABC

from fnt_auto.models.api import RestRequest, DBQuery
from fnt_auto.models.base import CustumAttribute, Link, RWModel, PortIdentifierLink, ItemRead
from fnt_auto.models.api import RestQuery

logger = logging.getLogger(__package__)

class GeoDirectionType(str, Enum):
    EAST = 'EAST'
    WEST = 'WEST'
    SOUTH = 'SOUTH'
    NORTH = 'NORTH'

class SideOption(str, Enum):
    A = 'A'
    B = 'B'

class CableMaster(RWModel):
    elid: str
    type: str
    connector1: str
    connector2: str
    medium: str
#       "lineType": "COMMON",
#       "manufacturer": "FNT GmbH",
#       "manufacturerArticleNumber": null,
#       "explanation": "Dubay GENERAL FIX OPTIC CABLE",
#       "diameter": null,
#       "prefix": "CBL-",
#       "category": "NETWORK",
#       "weight": null,
#       "isStandard": true,
#       "deliverLength": null,
#       "type": "FIX-CABLE-FO",
#     }
#   ]
# }


class CableCustomAttr(CustumAttribute):
    pass

class CableAttr(RWModel):
    visible_id: Optional[str] = None
    length: Optional[float] = None
    id: Optional[str] = None
    remark: Optional[str] = None

class CableCreateReq(RestRequest, CableAttr, CableCustomAttr):
    device_elid_a: str = Field(exclude=True)
    side_a: SideOption = Field(exclude=True)
    port_a: int = Field(exclude=True)
    type_elid: str = Field(exclude=True)
    device_elid_z: str = Field(exclude=True)
    side_z: SideOption = Field(exclude=True)
    port_z: int = Field(exclude=True)

    @property
    def port_identifier_a(self) -> str:
        return f"{self.device_elid_a}|NETWORK|{self.side_a}|{self.port_a}"
    
    @property
    def port_identifier_z(self) -> str:
        return f"{self.device_elid_z}|NETWORK|{self.side_z}|{self.port_z}"
    
    @computed_field
    def create_link_start_device(self) -> PortIdentifierLink:
        return PortIdentifierLink(port_identifier=self.port_identifier_a)

    @computed_field
    def create_link_end_device(self) -> PortIdentifierLink:
        return PortIdentifierLink(port_identifier=self.port_identifier_z)
    
    @computed_field
    def create_link_cable_master_data_cable(self) -> Link:
        return Link(linked_elid=self.type_elid)
    
class CableQuery(RestQuery):
    id: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)


class Cable(ItemRead, CableAttr, CableCustomAttr):
    type_elid: str
    id: str


class CableOnJunctionBoxCreateReq(ABC, RestRequest, CableCustomAttr):
    cable_visible_id: Optional[str] = None
    cable_length: Optional[float] = None
    cable_id: Optional[str] = None
    junction_box_elid: str = Field(exclude=True)
    geo_direction: GeoDirectionType
    cable_type_elid: str
    start_wire: int
    number_of_wires:int
    use_bundle_cable: bool = False

    def __new__(cls, *args, **kwargs):
        if cls is CableOnJunctionBoxCreateReq:
            raise TypeError(f"Cannot instantiate {cls.__name__} directly.")
        return super(CableOnJunctionBoxCreateReq, cls).__new__(cls)


class CableJbToDeviceCreateReq(CableOnJunctionBoxCreateReq):
    device_elid: str = Field(exclude=True)
    side: SideOption = Field(exclude=True)
    port: int = Field(exclude=True)
    
    @property
    def port_identifier_device(self) -> str:
        return f"{self.device_elid}|NETWORK|{self.side}|{self.port}"

    @computed_field
    def connect_to_device_all(self) -> PortIdentifierLink:
        return PortIdentifierLink(port_identifier=self.port_identifier_device)

class JunctionBoxLink(Link):
    geo_direction: GeoDirectionType

class CableJbToJbCreateReq(CableOnJunctionBoxCreateReq):
    to_junction_box_elid: str = Field(exclude=True)
    to_geo_direction: GeoDirectionType = Field(exclude=True)

    @computed_field
    def connect_to_junction_box(self) -> JunctionBoxLink:
        return JunctionBoxLink(linked_elid=self.to_junction_box_elid, geo_direction=self.to_geo_direction)
    
class CableRouteHop(RWModel):
    cable_elid: str
    swap: bool
    trs_elid: str


class CableRouteQuery(DBQuery):
    cable_elid: Optional[str] = Field(default=None)
    trs_elid: Optional[str] = Field(default=None)
    swap: Optional[bool] = Field(default=None)