from typing import Optional, Any
from fnt_auto.models import RWModel

class Login(RWModel):
    user: str
    password: str
    man_id: str = '1001'
    user_group_name: str = 'admin_1001|G'

class RestResponse(RWModel):
    message: Optional[str] = None
    status_code: int
    data: Optional[dict[str,Any]] = None