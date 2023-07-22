import logging
import typing as t
from httpx import AsyncClient
from pprint import pformat

from fnt_auto.models.api import Login
from fnt_auto.resources.exceptions import FntHttpError
from fnt_auto.models.api import RestResponse

logger = logging.getLogger(__package__)

class FntAsyncClient(AsyncClient):
    _session_id: str

    def __init__(self, base_url: str, username: str, password: str) -> None:
        super().__init__(base_url=base_url.rstrip('/'), timeout=30)
        self._username = username
        self._password = password

    async def login(self, username: t.Union[str, None] = None, password: t.Union[str, None] = None) -> t.Union[str, None]:
        response = await self.post(
            '/axis/api/rest/businessGateway/login',
            json=Login(user=username or self._username, password=password or self._password).model_dump(by_alias=True),
        )
        if response.is_success:
            self._session_id = response.json()['sessionId']
            logger.info(f"Login to FNT was successful - Sid: {self._session_id}")
            return self._session_id
        logger.error(response.json())
        return None

    async def logout(self, session_id: t.Union[str, None] = None) -> None:
        response = await self.post(
            '/axis/api/rest/businessGateway/logout', params={'sessionId': session_id or self._session_id}
        )
        if response.is_success:
            return response.json()
        logger.error(response.json())
        return response.json()
    
    async def rest_request(
        self, entity: str, operation: str, data:dict[str, t.Any]) -> 'RestResponse':
        logger.info(f"About to {operation} {entity}:")
        logger.info(f"\tRequest content: {data}")
        response = await self.post(f'/axis/api/rest/entity/{entity}/{operation}', params={'sessionId': self._session_id}, json=data)
        
        if response.status_code >= 500:
            message = "There was unexpected FNT Rest error."
            raise FntHttpError(message, response.status_code)
        
        ret = RestResponse(status_code=response.status_code, success=response.is_success)

        if response.is_success:
            ret.data = response.json().get('returnData')
            logger.debug(f"\tResponse content: {pformat(ret.data)}")
        else:
            ret.message = response.json().get('status',{}).get('message')
            print(response.json())
            logger.warning(f"\tFailed to {operation} {entity}: {ret.message}")
        return ret

        # async def rest_elid_request(self, entity: str, elid: str, operation: str, data: typing.Any, session_id: typing.Union[str, None] = None) -> 'ResponseType':
    #     response = await self._fnt_client.post(
    #         f'/entity/{entity}/{elid}/{operation}', params={'sessionId': session_id or self._session_id}, json=data
    #     )
    #     if response.is_success:
    #         return response.json(), None
    #     logger.error(response.text)
    #     return None, response.text

    # async def soap_request(
    #     self, operation: str, xml: str, session_id: typing.Union[str, None] = None
    # ) -> typing.Union[typing.Tuple[typing.Literal[True], None], typing.Tuple[None, str]]:
    #     url = f'/axis/services/{operation}'
    #     payload = xml.format(sid=session_id or self._session_id)
    #     response = await self._fnt_client.post(
    #         url, content=payload, headers={'Content-Type': 'text/xml', 'SOAPAction': url}
    #     )
    #     if b'exception_msgtxt' in response.content:
    #         logger.error(response.content)
    #         return None, response.content.decode('utf-8')
    #     return True, None