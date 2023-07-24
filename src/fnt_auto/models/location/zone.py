from typing import Optional
from pydantic import computed_field, Field
from enum import Enum

from fnt_auto.models import RWModel
from fnt_auto.models.api import RestQuery

class ZoneType(str, Enum):
    CAMPUS= 'campus'
    BUILDING = 'building'
    FLOOR = 'floor'
    ROOM = 'room'

class ZoneQuery(RestQuery):
    campus: Optional[str] = Field(default=None)
    building: Optional[str] = Field(default=None)
    floor: Optional[str] = Field(default=None)
    room: Optional[str] = Field(default=None)
    entity: Optional[ZoneType] = Field(default=None)
    

class Zone(RWModel):
    elid: str
    campus: str
    building: Optional[str]
    floor: Optional[str]
    description: Optional[str]
    remark: Optional[str]
    target_sub_entity: ZoneType