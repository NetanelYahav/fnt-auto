from fnt_auto.async_api.async_client import FntAsyncClient
from fnt_auto.oracle.base_repository import OracleBaseRepository

from fnt_auto.async_api.location import LocationAPI
from fnt_auto.async_api.inventory import InventoryAPI
from fnt_auto.async_api.tray_mgmt import TrayMgmtAPI
from fnt_auto.async_api.connectivity import ConnectivityAPI

class FntAsyncAPI:
    # _fnt_client = FntAsyncClient
    # _fnt_db = OracleBaseRepository
    
    def __init__(self, fnt_client: FntAsyncClient):
        self._fnt_client = fnt_client
        self.location: LocationAPI = LocationAPI(fnt_client)
        self.inventory: InventoryAPI = InventoryAPI(fnt_client)
        self.tray_mgmt: TrayMgmtAPI = TrayMgmtAPI(fnt_client)
        self.connectivity: ConnectivityAPI = ConnectivityAPI(fnt_client)

    @property
    def fnt_client(self) -> FntAsyncClient:
        return self._fnt_client


__all__ = ['FntAsyncAPI',]