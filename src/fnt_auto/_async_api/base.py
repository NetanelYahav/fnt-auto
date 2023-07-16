import typing
import logging
import typing

from httpx import AsyncClient
from httpx import AsyncClient
from fnt_auto.models.api import Login, RestResponse


if typing.TYPE_CHECKING:
    from fnt_auto._async_api.base import ResponseType


logger = logging.getLogger(__package__)

class AsyncBaseAPI:
    _client: AsyncClient
    _session_id: str

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self._client = AsyncClient(base_url=base_url.rstrip('/'))
        self._username = username
        self._password = password

    async def login(
        self, username: typing.Union[str, None] = None, password: typing.Union[str, None] = None
    ) -> typing.Union[str, None]:
        response = await self._client.post(
            '/axis/api/rest/businessGateway/login',
            json=Login(user=username or self._username, password=password or self._password).model_dump(by_alias=True),
        )
        if response.is_success:
            self._session_id = response.json()['sessionId']
            return self._session_id
        logger.error(response.json())
        return None

    async def logout(self, session_id: typing.Union[str, None] = None) -> None:
        response = await self._client.post(
            '/axis/api/rest/businessGateway/logout', params={'sessionId': session_id or self._session_id}
        )
        if response.is_success:
            return response.json()
        logger.error(response.json())
        return response.json()

    async def rest_request(
        self, entity: str, operation: str, data: typing.Any, session_id: typing.Union[str, None] = None
    ) -> 'RestResponse':
        logger.info(f"About to {operation} {entity}:")
        logger.info(f"\tRequest content: {data}")
        response = await self._client.post(
            f'/axis/api/rest/entity/{entity}/{operation}', params={'sessionId': session_id or self._session_id}, json=data
        )
        ret = RestResponse(status_code=response.status_code)
        if response.is_success:
            ret.data = response.json().get('returnData')
            logger.info(f"\tResponse content: {ret.data}")
        else:
            ret.message = response.json().get('status',{}).get('message')
            logger.error(f"\tFailed to {operation} {entity}: {ret.message}")
        return ret

    async def rest_elid_request(
        self, entity: str, elid: str, operation: str, data: typing.Any, session_id: typing.Union[str, None] = None
    ) -> 'ResponseType':
        response = await self._client.post(
            f'/entity/{entity}/{elid}/{operation}', params={'sessionId': session_id or self._session_id}, json=data
        )
        if response.is_success:
            return response.json(), None
        logger.error(response.text)
        return None, response.text

    async def soap_request(
        self, operation: str, xml: str, session_id: typing.Union[str, None] = None
    ) -> typing.Union[typing.Tuple[typing.Literal[True], None], typing.Tuple[None, str]]:
        url = f'/axis/services/{operation}'
        payload = xml.format(sid=session_id or self._session_id)
        response = await self._client.post(
            url, content=payload, headers={'Content-Type': 'text/xml', 'SOAPAction': url}
        )
        if b'exception_msgtxt' in response.content:
            logger.error(response.content)
            return None, response.content.decode('utf-8')
        return True, None


ErrorReponse = typing.Tuple[None, str]
SuccessReponse = typing.Tuple[typing.Dict[str, typing.Any], None]

ResponseType = typing.Union[ErrorReponse, SuccessReponse]
