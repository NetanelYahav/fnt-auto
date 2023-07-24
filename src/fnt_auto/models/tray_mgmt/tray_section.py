from typing import Optional
from pydantic import Field, computed_field, validator
from datetime import datetime

from fnt_auto.models.api import RestRequest
from fnt_auto.models.base import CustumAttribute, Link, RWModel
from fnt_auto.models.location.zone import ZoneQuery

class TraySectionMaster(RWModel):
    elid: str
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    type: str

class TraySectionCustomAttr(CustumAttribute):
    c_tray_owner: Optional[str] = None
    c_remark: Optional[str] = None
    c_import_origin: Optional[str] = None
    c_exec_contractor: Optional[str] = None
    c_last_seen: Optional[str] = None
    c_geo_coords: Optional[str] = None

class TraySectionAttr(RWModel):
    id: Optional[str] = None
    visible_id: Optional[str] = None
    description: Optional[str] = None
    coord_system: Optional[str] = None
    segment_length: Optional[float] = None 


class TraySectionCreateReq(RestRequest, TraySectionAttr, TraySectionCustomAttr):
    type_elid: str = Field(..., exclude=True)
    from_node: str = Field(..., exclude=True)
    to_node: str = Field(..., exclude=True)

    @computed_field
    def create_link_from_node(self) -> Link:
        return Link(linked_elid=self.from_node)

    @computed_field
    def create_link_to_node(self) -> Link:
        return Link(linked_elid=self.to_node)
    
    @computed_field
    def create_link_tray_section_type(self) -> Link:
        return Link(linked_elid=self.type_elid)
    

class TraySectionAdvanceReq(TraySectionCreateReq):
    type_elid: Optional[str] = Field(default=None, exclude=True)
    zone_elid: Optional[str] = Field(default=None, exclude=True)
    type: str = Field(..., exclude=True)
    zone: ZoneQuery = Field(..., exclude=True) 

class TraySection(TraySectionAttr, TraySectionCustomAttr):
    elid: str
    type_elid: str
    status_action: int



# {
#       "fromNodeSideName": null,
#       "cXyz": null,
#       "elid": "NNGW36IGWLVJXC",
#       "cGeoCoords": "[]",
#       "cTsDuct": null,
#       "fromNodeSide": null,
#       "toNodeSide": null,
#       "toNodeElid": "5YRJV9DRRSQNTM",
#       "typeElid": "IZQ73AU60E1T1P",
#       "visibleId": "TS-242111-202110",
#       "cTrayOwner": "Bezeq",
#       "segmentLength": 23.86717655775054,
#       "description": "*",
#       "fromLocation": {
#         "campusElid": "D8LCP3F6ZYV6DF",
#         "floorElid": null,
#         "floor": null,
#         "campus": "Rehovot",
#         "roomElid": null,
#         "building": null,
#         "warehouse": null,
#         "warehouseElid": null,
#         "buildingElid": null,
#         "room": null,
#         "zoneElid": "D8LCP3F6ZYV6DF"
#       },
#       "toNodeSideName": null,
#       "toLocation": {
#         "campusElid": "D8LCP3F6ZYV6DF",
#         "floorElid": null,
#         "floor": null,
#         "campus": "Rehovot",
#         "roomElid": null,
#         "building": null,
#         "warehouse": null,
#         "warehouseElid": null,
#         "buildingElid": null,
#         "room": null,
#         "zoneElid": "D8LCP3F6ZYV6DF"
#       },
#       "fromNodeElid": "6TC9QCUOGMNHL4",
#       "id": "TS-242111-202110",
#       "cImportOrigin": "600_DWG_20200301082723_600P100000000003946.dwg",
#       "cLastSeen": "2022-02-13T15:19:34Z",
#       "statusAction": 0