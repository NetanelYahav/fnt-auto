from fnt_auto.async_api.async_client import FntAsyncClient
from fnt_auto.async_api.tray_mgmt.node import NodeAPI
from fnt_auto.async_api.tray_mgmt.tray_section import TraySectionAPI

class TrayMgmtAPI:
    def __init__(self, _fnt_client: FntAsyncClient):
        self.node: NodeAPI = NodeAPI(_fnt_client)
        self.tray_section: TraySectionAPI = TraySectionAPI(_fnt_client)

__all__ = ['TrayMgmtAPI',]