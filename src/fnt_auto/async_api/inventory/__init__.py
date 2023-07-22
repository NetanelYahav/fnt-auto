from fnt_auto.async_api.async_client import FntAsyncClient
from fnt_auto.async_api.inventory.device import DeviceAPI

class InventoryAPI:
    def __init__(self, _fnt_client: FntAsyncClient):
        self.device: DeviceAPI = DeviceAPI(_fnt_client)

__all__ = ['InventoryAPI',]