import typing
import logging
import typing

from httpx import AsyncClient, Client
from httpx import AsyncClient
from fnt_auto.models.api import Login


if typing.TYPE_CHECKING:
    from fnt_auto._async_api.base import ResponseType


logger = logging.getLogger(__package__)

__all__: list[str] = []


class SyncBaseAPI:
    _client: Client
    _session_id: str


ErrorReponse = typing.Tuple[None, str]
SuccessReponse = typing.Tuple[typing.Dict[str, typing.Any], None]

ResponseType = typing.Union[ErrorReponse, SuccessReponse]
