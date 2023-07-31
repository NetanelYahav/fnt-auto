from fnt_auto.async_api.async_client import FntAsyncClient
from fnt_auto.async_api.connectivity.cable import CableAPI, CableOnJunctionBoxAPI
from fnt_auto.async_api.connectivity.connection import ConnectionAPI

class ConnectivityAPI:
    def __init__(self, _fnt_client: FntAsyncClient):
        self.cable: CableAPI = CableAPI(_fnt_client)
        self.cable_on_jb: CableOnJunctionBoxAPI = CableOnJunctionBoxAPI(_fnt_client)
        self.connection: ConnectionAPI = ConnectionAPI(_fnt_client)

__all__ = ['ConnectivityAPI', ]