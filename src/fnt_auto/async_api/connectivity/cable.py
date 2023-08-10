import logging
import typing as t
from fnt_auto.async_api.base import AsyncBaseAPI
from fnt_auto.models.base import ItemCreateRes, ItemRead, RestResponse
from fnt_auto.models.connectivity.cable import CableCreateReq, CableMaster, Cable, CableQuery, CableOnJunctionBoxCreateReq, CableRouteHop, CableRouteQuery

logger = logging.getLogger(__package__)

class CableAPI(AsyncBaseAPI):

    async def create(self, cable: CableCreateReq) -> 'ItemCreateRes':          
        return ItemCreateRes(
            rest_request=cable.model_copy(),
            rest_response = await self.rest_request('dataCable', 'connect', cable)
        )

    async def get_all(self) -> list[Cable]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('dataCable', 'query', req)
        return self.parse_rest_response(Cable, response)
    
    
    async def get_by_query(self, cable: CableQuery) -> list[Cable]:
        response = await self.rest_request('dataCable', 'query', cable)
        return self.parse_rest_response(Cable, response)
    
    async def get_by_elid(self, elid:str) -> t.Optional[Cable]:
        cables = await self.get_by_query(CableQuery(elid=elid))
        return cables[0] if cables else None

    async def get_all_types(self) -> list[CableMaster]:
        req = {'restrictions': {'elid': {'value': '*', 'operator': 'like'}}, 'returnAttributes': []}
        response = await self._fnt_client.rest_request('cableMaster', 'query', req)
        return self.parse_rest_response(CableMaster, response)
    
    async def delete(self, elid: str) -> 'RestResponse':
        data = {"releaseService": True, "releaseSignalpath": True, "releaseTrmRoute": True}
        return await self._fnt_client.rest_elid_request('dataCable', elid, 'delete', data)
    
    async def route_cable(self, cable_route: list[CableRouteHop]) -> bool:
        rows_total = 0
        for sequence, hop in enumerate(cable_route, start=1):
            logger.debug(f'route cable {hop.cable_elid} to tray section {hop.trs_elid}')
            sql = "SELECT spasys_element.GENERATEELID(14, 'STCCLI_BLOCKED_SOCKET', 'INFOS') AS NEW_ELID FROM dual"
            new_elid_ret = self._fnt_client.fetch(sql)

            new_elid = new_elid_ret[0]['NEW_ELID']
            swap = 'Y' if hop.swap else 'N'
            # # TODO: Find the right CREATED_BY
            created_by = 'ALGWFLKQMBSZRH'

            sql = """
                    INSERT INTO STLTRM_LINK
                    (LINK_ELID, PARENT_ELEMENT, CHILD_ELEMENT, ARG_1, LINK_DESCRIPTION, STATUS_ACTION, SWAP, ARG_2, ARG_3, ARG_4, ARG_5, CREATED_BY, CREATE_DATE, REL_ID, NUM_OBJECTS_TO_PLACE)
                    VALUES
                    ({new_elid}, {tray_elid}, {cable_elid}, {sequence}, 'STCTRM_TRAY_SECTION_STCCLI_CABLE', 0, {swap}, NULL, NULL, NULL, {sequence}, {created_by}, SYSDATE, NULL, NULL)
                """
            ret = self._fnt_client.execute(
                sql,
                new_elid=new_elid,
                tray_elid=hop.trs_elid,
                cable_elid=hop.cable_elid,
                sequence=sequence,
                swap=swap,
                created_by=created_by,
            )
            rows_total += int(ret)
        logger.debug(f'Finish Routed cable {cable_route[0].cable_elid}')
        return rows_total == len(cable_route)

    async def get_cable_route_by_query(self, query: CableRouteQuery) -> list[CableRouteHop]:
        sql = """
            SELECT * FROM(
                SELECT CHILD_ELEMENT AS "cableElid", PARENT_ELEMENT AS "trsElid", SWAP AS "swap"
                FROM STLTRM_LINK sl
                WHERE sl.LINK_DESCRIPTION = 'STCTRM_TRAY_SECTION_STCCLI_CABLE'
                ORDER BY sl.CHILD_ELEMENT, sl.ARG_1
            )t
        """
        res = self._fnt_client.fetch(sql + query.to_sql_constraint(), **query.rw_model_dump())
        return [CableRouteHop(**hop) for hop in res]
    

class CableOnJunctionBoxAPI(AsyncBaseAPI):
    async def create(self, cable: CableOnJunctionBoxCreateReq) -> 'ItemCreateRes':          
        item_create_res = ItemCreateRes(
            rest_request=cable.model_copy(),
            rest_response = await self.rest_elid_request('junctionBoxFist', cable.junction_box_elid, 'connect', cable)
        )
        
        if isinstance(item_create_res.rest_response.data, dict):
            created_cables = item_create_res.rest_response.data.get('createdCables')
            if created_cables:
                item_create_res.new_item_elid = created_cables[0].get('cableElid')
        return item_create_res

    async def delete(self, elid: str) -> 'RestResponse':
        data = {"releaseService": "true", "releaseSignalpath": "true", "releaseTrmRoute": "true"}
        return await self._fnt_client.rest_elid_request('dataCable', elid, 'delete', data)
    
    async def get_by_elid(self, elid: str) -> t.Optional[Cable]:
        cable_api = CableAPI(self._fnt_client)
        return await cable_api.get_by_elid(elid)
    