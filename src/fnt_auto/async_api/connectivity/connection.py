from fnt_auto.async_api.base import AsyncBaseAPI
from fnt_auto.models import RWModel
from fnt_auto.models.connectivity.connection import Connection, ConnectionQuery

sql = """
    SELECT * FROM(
        SELECT sc.INFOS AS "elid", sc.CATEGORY AS "category", 
            sc.ID_ELID AS "idElid", sc.SOCKET_SIDE AS "socketSide", sc.SOCKET_NO AS "socketNo", sc.SOCKET_SUB_NO AS "socketSubNo", sc.PLAN_OCCUPIED AS "planOccupied", 
            sc.CABLE_ELID AS "cableElid", sc.CABLE_LINE_NO AS "cableLineNo", 
            sc.TO_ID_ELID AS "toIdElid", sc.TO_SOCKET_SIDE AS "toSocketSide", sc.TO_SOCKET_NO AS "toSocketNo", sc.TO_SOCKET_SUB_NO AS "toSocketSubNo", sc.TO_PLAN_OCCUPIED AS "toPlanOccupied", 
            sc.PLAN_POS_ELID AS "planPosElid", sc.STATUS_ACTION AS "statusAction",
            mad.TABLE_NAME AS "tableName", mad2.TABLE_NAME AS "toTableName"
        FROM COMMAND.STCCLI_CONNECTION sc INNER JOIN META_ALL_DEVICE mad ON mad.INTERNAL_ID = sc.ID_ELID 
							INNER JOIN META_ALL_DEVICE mad2 ON mad2.INTERNAL_ID = sc.TO_ID_ELID 
    )t
"""

class ConnectionAPI(AsyncBaseAPI):

    async def get_all(self) -> list[Connection]:
        res = self._fnt_client.fetch(sql)
        return [Connection(**conn) for conn in res]
    
    async def get_by_query(self, query: ConnectionQuery) -> list[Connection]:
        res = self._fnt_client.fetch(sql + query.to_sql_constraint(), **query.rw_model_dump())
        return [Connection(**conn) for conn in res]