from fnt_auto.async_api.async_client import FntAsyncClient
from fnt_auto.async_api.inventory.device import DeviceAPI
from fnt_auto.async_api.inventory.junction_box import JunctionBoxAPI, JunctionBoxFistAPI

class InventoryAPI:
    def __init__(self, _fnt_client: FntAsyncClient):
        self.device: DeviceAPI = DeviceAPI(_fnt_client)
        self.junction_box: JunctionBoxAPI = JunctionBoxAPI(_fnt_client)
        self.junction_box_fist: JunctionBoxFistAPI = JunctionBoxFistAPI(_fnt_client)

__all__ = ['InventoryAPI',]