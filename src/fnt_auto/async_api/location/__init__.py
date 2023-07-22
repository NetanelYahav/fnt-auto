from fnt_auto.async_api.async_client import FntAsyncClient
from fnt_auto.async_api.location.campus import CampusAPI
from fnt_auto.async_api.location.building import BuildingAPI

class LocationAPI:

    def __init__(self, _fnt_client: FntAsyncClient):
        self.campus: CampusAPI = CampusAPI(_fnt_client)
        self.building: BuildingAPI = BuildingAPI(_fnt_client)

__all__ = ['LocationAPI', ]