from typing import Optional
from pydantic import computed_field, Field
from enum import Enum

from fnt_auto.models import RWModel
from fnt_auto.models.api import RestQuery
from fnt_auto.models.base import Restriction

class ZoneType(str, Enum):
    CAMPUS= 'campus'
    BUILDING = 'building'
    FLOOR = 'floor'
    ROOM = 'room'

class ZoneQuery(RestQuery):
    campus_name: str = Field(exclude=True)
    building_name: Optional[str] = Field(default=None, exclude=True)
    floor_name: Optional[str] = Field(default=None, exclude=True)
    room_name: Optional[str] = Field(default=None, exclude=True)
    entity_name: Optional[ZoneType] = Field(default=None, exclude=True)

    @computed_field
    def campus(self) -> Restriction:
        return Restriction(value=self.campus_name)
    
    @computed_field
    def building(self) -> Restriction:
        return Restriction(value=self.building_name)
    
    @computed_field
    def floor(self) -> Restriction:
        return Restriction(value=self.floor_name)
    
    @computed_field
    def room(self) -> Restriction:
        return Restriction(value=self.room_name)
    
    @computed_field
    def target_sub_entity(self) -> Restriction:
        return Restriction(value=self.entity_name)
    

class Zone(RWModel):
    elid: str
    campus: str
    building: Optional[str]
    floor: Optional[str]
    description: Optional[str]
    remark: Optional[str]
    target_sub_entity: ZoneType