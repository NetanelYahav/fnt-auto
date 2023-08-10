from pydantic import Field
from typing import Optional, Union, Any
from fnt_auto.models import RWModel

class RestLogin(RWModel):
    base_url: str
    username: str
    password: str
    
class DBLogin(RWModel):
    username: str
    password: str
    host: str
    port: int
    service_name:str


class Login(RWModel):
    user: str
    password: str
    man_id: str = '1001'
    user_group_name: str = 'admin_1001|G'


class RestResponse(RWModel):
    message: Optional[str] = None
    status_code: int
    data: Optional[Union[dict[str,Any], list[dict[str,Any]]]] = None
    success: bool

class RestRequest(RWModel):
    def to_rest_request(self) -> dict[str, Any]:
        # attr_class = type(self)
        # self_attr = attr_class(**{**self.model_dump(exclude_defaults=True), **self.model_dump(exclude_unset=True), **self.model_dump(exclude_none=True)})
        # if curr_db_attr is not None:
        #     curr_attr = attr_class(**{k.lower(): v for k, v in curr_db_attr.items()})
        #     if curr_attr == self_attr:
        #         return {}

        # update_attr = {}
        # for field_name, value in self_attr.model_dump(exclude_unset=True).items():
        #     extra = (attr_class.model_fields[field_name].field_info.extra)
        #     if extra.get('rest_name') is None:
        #         continue
        #     fn = extra.get('rest_name', field_name)

        #     val_as_obj = getattr(self_attr, field_name)
        #     if issubclass(type(val_as_obj), List) and value:
        #         value = []
        #         for val in val_as_obj:
        #             if issubclass(type(val), RWModel):
        #                 value.append(val.prepare_request())
        #     elif issubclass(type(val_as_obj), RWModel):
        #         value = val.prepare_request()

        #     if fn.startswith('createLink'):
        #         value = {'linkedElid': value}
        #     update_attr[fn] = value
        # return update_attr
        
        rest_req = {
            **self.model_dump(by_alias=True, exclude_defaults=True), 
            **self.model_dump(by_alias=True, exclude_unset=True), 
            **self.model_dump(by_alias=True, exclude_none=True)
        }

        return rest_req 

class RestQuery(RestRequest):
    elid: Optional[str] = Field(default=None)
    def to_rest_request(self) -> dict[str, Any]:
        ret = {'restrictions': {}, "returnAttributes": []}
        for field_name, value in self.rw_model_dump().items():
            operator = '='
            if value is not None and type(value) == str and '*' in value:
                operator = 'like'
            ret['restrictions'][field_name] = {'value': value, 'operator': operator}

        return ret
    
class DBQuery(RWModel):
    def to_sql_constraint(self) -> str:
        where_clause:str = ""
        for i, field_name in enumerate(self.rw_model_dump()):
            if i == 0:
                where_clause = f"""\nWHERE (COALESCE(t."{field_name}", NULL) is NULL OR t."{field_name}" = :{field_name})\n"""
            else:
                where_clause = where_clause + f"""AND (COALESCE(t."{field_name}", NULL) is NULL OR t."{field_name}" = :{field_name})\n"""
        return where_clause