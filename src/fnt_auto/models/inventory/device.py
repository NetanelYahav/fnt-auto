from typing import Optional
from abc import ABC
from pydantic import Field, computed_field
from typing import Dict, Any

from fnt_auto.models.api import RestRequest
from fnt_auto.models.base import CustumAttribute, Link, RWModel


class DeviceCustomAttr(CustumAttribute):
    pass

class DeviceMaster(RWModel):
    elid: str
    explanation: str
    manufacturer: str
    type: str
    function: str


class DeviceAttr(RWModel):
    id: Optional[str] = None
    visible_id: Optional[str] = None
    remark: Optional[str] = None


class DeviceCreateReq(ABC, RestRequest, DeviceAttr, DeviceCustomAttr):
    type_elid: str = Field(..., exclude=True)
    
    def __new__(cls, *args, **kwargs):
        if cls is DeviceCreateReq:
            raise TypeError(f"Cannot instantiate {cls.__name__} directly.")
        return super(DeviceCreateReq, cls).__new__(cls)
    
    @computed_field
    def create_link_device_master(self) -> Link:
        return Link(linked_elid=self.type_elid)

class DeviceCreateInZoneReq(DeviceCreateReq):
    zone_elid: str = Field(..., exclude=True)
    
    @computed_field
    def create_link_zone(self) -> Link:
        return Link(linked_elid=self.zone_elid)
    
class DeviceCreateInCabinetReq(DeviceCreateReq):
    cabinet_elid: str = Field(..., exclude=True)
    
    @computed_field
    def create_link_switch_cabinet(self) -> Link:
        return Link(linked_elid=self.cabinet_elid)


class Device(DeviceAttr, DeviceCustomAttr):
    elid: str
    id: str
