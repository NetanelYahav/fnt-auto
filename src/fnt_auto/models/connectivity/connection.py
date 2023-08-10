from typing import Optional
from pydantic import Field

from fnt_auto.models.base import ItemRead
from fnt_auto.models.api import DBQuery

class Connection(ItemRead):
    elid: str
    category: str
    table_name: str
    id_elid: str
    socket_side: str
    socket_no: Optional[int] = Field(default=None)
    socket_sub_no: Optional[int] = Field(default=None)
    plan_occupied: str
    cable_elid: str
    cable_line_no: Optional[int] = Field(default=None)
    to_table_name: str
    to_id_elid: str
    to_socket_side: str
    to_socket_no: Optional[int] = Field(default=None)
    to_socket_sub_no: Optional[int] = Field(default=None)
    to_plan_occupied: str
    plan_pos_elid: Optional[str]
    status_action: Optional[int] = Field(default=None)


class ConnectionQuery(DBQuery):
    elid: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    id_elid: Optional[str] = Field(default=None)
    socket_side: Optional[str] = Field(default=None)
    socket_no: Optional[int] = Field(default=None)
    socket_sub_no: Optional[int] = Field(default=None)
    plan_occupied: Optional[str] = Field(default=None)
    cable_elid: Optional[str] = Field(default=None)
    cable_line_no: Optional[int] = Field(default=None)
    to_id_elid: Optional[str] = Field(default=None)
    to_socket_side: Optional[str] = Field(default=None)
    to_socket_no: Optional[int] = Field(default=None)
    to_socket_sub_no: Optional[int] = Field(default=None)
    to_plan_occupied: Optional[str] = Field(default=None)
    plan_pos_elid: Optional[str] = Field(default=None)
    status_action: Optional[int] = Field(default=None)