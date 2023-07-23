from fnt_auto.models import RWModel
from fnt_auto.models.location.zone import ZoneQuery

from fnt_auto.async_api.base import AsyncBaseAPI
from fnt_auto.models.location.zone import Zone

class ZoneAPI(AsyncBaseAPI):

    async def get_by_query(self, zone: ZoneQuery) -> list[Zone]:
        response = await self.rest_request('zone', 'query', zone)
        return self.parse_rest_response(Zone, response)