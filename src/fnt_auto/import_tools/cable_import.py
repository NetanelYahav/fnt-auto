import asyncio
import json
import logging
from collections import namedtuple
from functools import partial, partialmethod
from typing import Any, Optional

from aiopath import AsyncPath
from async_lru import alru_cache
from fnt_auto.async_api import FntAsyncAPI
from fnt_auto.models.geo import Feature, FeatureCollection
# from partner_import.oracle import OracleBaseRepository, oracle_repo


logging.TRACE = 5
logging.addLevelName(logging.TRACE, 'TRACE')
logging.Logger.trace = partialmethod(logging.Logger.log, logging.TRACE)
logging.trace = partial(logging.log, logging.TRACE)


logger = logging.getLogger(__package__)
logging.basicConfig(
    format='%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-8s | %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
    level=logging.DEBUG,
    datefmt='%F %T',
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
CABLE_TYPES = {
    'eli-12': 'FO-12',
    # 'ttk-432': '',
    'ttk-12': 'FO-12',
    'ttk-48': 'FO-48',
    # 'eli-72': '',
    'eli-48': 'FO-48',
    'eli-144': 'FO-144',
    'eli-96': 'FO-96',
    'ttk-576': '',
    'ttk-24': 'FO-24',
    # 'ttk-288': 'FO-288',
    'eli-24': 'FO-24',
    'ttk-144': 'FO-144',
    # 'ttk-864': '',
    'ttk-96': 'FO-96',
    'drop-4': 'FO-4',
}

TraySectionHop = namedtuple('TraySectionHop', ['elid', 'swap', 'sequence'])


async def get_nodes(api: FntAsyncAPI) -> list[dict[str, str]]:
    payload:dict = {'restrictions': {}, 'returnAttributes': []}
    response = await api.fnt_client.rest_request('node', 'query', payload)
    if not response.success:
        msg = f'failed to get nodes: {response.message}'
        raise ValueError(msg)
    return response.data


async def get_buildings(api: FntAsyncAPI) -> list[dict[str, str]]:
    payload = {'restrictions': {}, 'returnAttributes': []}
    response = await api.fnt_client.rest_request('building', 'query', payload)
    if not response.success:
        msg = f'failed to get buildings: {response.message}'
        raise ValueError(msg)
    return response.data


async def get_cable_master(api: FntAsyncAPI) -> list[dict[str, Any]]:
    payload = {'restrictions': {}, 'returnAttributes': []}
    response = await api.fnt_client.rest_request('cableMaster', 'query', payload)
    if not response.success:
        msg = f'failed to get cable master: {response.message}'
        raise ValueError(msg)
    return response.data


async def get_device_master_junction_box(api: 'FntAsyncAPI') -> list[dict[str, Any]]:
    payload = {'restrictions': {}, 'returnAttributes': []}
    response = await api.fnt_client.rest_request('deviceMasterJunctionBox', 'query', payload)
    if not response.success:
        msg = f'failed to get device master junction box: {response.message}'
        raise ValueError(msg)
    return [device | {'fist': False} for device in response.data]


async def get_device_master_junction_box_fist(api: 'FntAsyncAPI') -> list[dict[str, Any]]:
    payload = {'restrictions': {}, 'returnAttributes': []}
    response = await api.fnt_client.rest_request('deviceMasterJunctionBoxFist', 'query', payload)
    if not response.success:
        msg = f'failed to get device master junction box fist: {response.message}'
        raise ValueError(msg)
    return [device | {'fist': True} for device in response.data]


@alru_cache
async def get_junction_box_mapping(api: FntAsyncAPI) -> dict[str, dict[str, Any]]:
    junction_box = await asyncio.gather(get_device_master_junction_box(api), get_device_master_junction_box_fist(api))
    junction_box = junction_box[0] + junction_box[1]
    return {box['type']: box for box in junction_box} | {box['elid']: box for box in junction_box}


@alru_cache
async def get_cable_master_mapping(api: FntAsyncAPI) -> dict[str, str]:
    cable_master = await get_cable_master(api)
    return {cable['type']: cable['elid'] for cable in cable_master}


@alru_cache
async def get_building_mapping(api: FntAsyncAPI) -> dict[str, str]:
    buildings = await get_buildings(api)
    return {building['name']: building['elid'] for building in buildings}


@alru_cache
async def get_node_mapping(api: FntAsyncAPI) -> dict[str, str]:
    nodes = await get_nodes(api)
    return {node['id']: node['elid'] for node in nodes}


async def get_cable(api: FntAsyncAPI, id: str) -> list[dict[str, Any]]:
    payload = {'restrictions': {'id': {'value': id, 'operator': 'like'}}, 'returnAttributes': []}
    response = await api.fnt_client.rest_request('dataCable', 'query', payload)
    if not response.success:
        logger.error(err)
        return None
    logger.debug(f'found {len(response.data)} cables for {payload}')
    return response.data


async def get_devices_in_zone(api: FntAsyncAPI, zone: str) -> list[dict[str, Any]]:
    payload = {
        'restrictions': {'zoneElid': {'value': zone, 'operator': '='}},
        'returnAttributes': [],
    }
    response = await api.fnt_client.rest_request('zone', 'queryContent', payload)
    if not response.success:
        msg = f'failed to get devices in zone {zone}: {response.message}'
        raise ValueError(msg)
    return response.data


async def get_devices_in_node(api: FntAsyncAPI, node: str) -> list[dict[str, Any]]:
    payload: dict[str, dict[str, str] | list[str]] = {
        'relationRestrictions': {},
        'entityRestrictions': {},
        'returnRelationAttributes': [],
        'returnEntityAttributes': [],
    }
    response = await api.fnt_client.rest_elid_request('node', node, 'DevicesAll', payload)
    if not response.success:
        msg = f'failed to get devices in node {node}: {response.message}'
        raise ValueError(msg)
    return [device['entity'] for device in response.data]


async def find_cable_end(api: FntAsyncAPI, id: str, type: str) -> Optional[dict[str, Any]]:
    logger.debug(f'Searching Junction or Device for `{type}` `{id}` ')
    if type == 'building':
        buildings = await get_building_mapping(api)
        building_elid = buildings.get(id)
        if building_elid is None:
            logger.error(f'building {id} not found in building mapping')
            return None
        devices = await get_devices_in_zone(api, building_elid)
        # TODO find the right device
    if type == 'node':
        nodes = await get_node_mapping(api)
        junction = await get_junction_box_mapping(api)
        node_elid = nodes.get(id)
        if node_elid is None:
            logger.error(f'node {id} not found in node mapping')
            return None
        devices = await get_devices_in_node(api, node_elid)
        for device in devices:
            junction_box = junction.get(device['typeElid'])
            if junction_box is None:
                continue
            logger.debug(f'found junction box {junction_box} in node {id}')
            return device | {'master': junction_box}

    return None


async def init_cache(api: FntAsyncAPI) -> None:
    await asyncio.gather(
        get_building_mapping(api),
        get_node_mapping(api),
        get_cable_master_mapping(api),
        get_junction_box_mapping(api),
    )


async def update_data_cable(api: FntAsyncAPI, elid: str, id: str, visible_id: str) -> None:
    payload = {'id': id, 'visibleId': visible_id}
    logger.info(f'updating data cable {elid} -> {payload}')
    response = await api.fnt_client.rest_elid_request('dataCable', elid, 'update', payload)
    if not response.success:
        msg = f'failed to update data cable {id}: {response.message}'
        raise ValueError(msg)
    logger.debug(f'updated data cable {elid}')
    return response.data


async def delete_data_cable(api: FntAsyncAPI, elid: str) -> None:
    payload = {'releaseService': 'true', 'releaseSignalpath': 'true', 'releaseTrmRoute': 'true'}
    response = await api.fnt_client.rest_elid_request('dataCable', elid, 'delete', payload)
    if not response.success:
        msg = f'failed to delete data cable {elid}: {response.message}'
        raise ValueError(msg)
    logger.info(f'deleted data cable {elid}')
    return response.data


async def connect_cable(
    api: FntAsyncAPI,
    cable: 'Feature',
    type_elid: str,
    start: dict[str, str],
    end: dict[str, str],
    section: int = 1,
    intersections: list[dict[str, str]] = [],
) -> bool:
    size = cable.properties['cable_size']
    start_device, end_device = await asyncio.gather(
        *[find_cable_end(api, start['id'], start['type']), find_cable_end(api, end['id'], end['type'])]
    )
    logger.debug(f'found {start_device} <-> {end_device}')
    if start_device is None or end_device is None:
        logger.debug('failed to find start or end device - Skipping')
        return False

    start_device_master = start_device['master']
    end_device_master = end_device['master']
    if 'fist' in start_device_master:
        start_elid = start_device['elid']
        fist_box = start_device_master['fist']
        end_elid = end_device['elid']
        end_is_junction = 'fist' in end_device_master

    elif 'fist' in end_device_master:
        start_elid = end_device['elid']
        fist_box = end_device_master['fist']
        end_elid = start_device['elid']
        end_is_junction = 'fist' in start_device_master
    else:
        msg = f'both ends of cable {cable.properties["handle"]} are not junction boxes'
        raise ValueError(msg)
    if end_is_junction:
        logger.debug('Start is fist box and end is junction box')
    else:
        logger.debug('Start is fist box and end is device')

    payload = {
        'cableLength': 0,
        'useBundleCable': True,
        'geoDirection': 'EAST',
        'startWire': 1,
        'numberOfWires': size,
        'cableTypeElid': type_elid,
    }

    if end_is_junction:
        payload['connectToJunctionBox'] = {'linkedElid': end_elid, 'geoDirection': 'EAST'}
    else:
        payload['connectToDeviceAll'] = {'portIdentifier': f'{end_elid}|NETWORK|B|1'}
    entity = 'junctionBoxFist' if fist_box else 'junctionBox'
    
    response = await api.fnt_client.rest_elid_request(entity, start_elid, 'connect', payload)
    if not response.success:
        msg = f'failed to connect cable {cable.properties["handle"]}: {response.message}'
        raise ValueError(msg)
    # hopefully there is only one cable
    cable_elid = response.data['createdCables'][0]['cableElid']
    cable_route = await find_cable_route(api, start, end, intersections)
    if cable_route:
        route_cable(cable_elid, cable_route)
    # FIXME choose the right cable name
    cable_name = f"{cable.properties['handle']}-{section}"
    await update_data_cable(api, cable_elid, cable_name, cable_name)
    logger.info(f'connected cable {cable_name} ({cable_elid})')
    return True


async def get_tray_section_by_nodes(api: FntAsyncAPI, start_node: str, end_node: str) -> Optional[str]:
    payload = {
        'restrictions': {
            'fromNodeElid': {'value': start_node, 'operator': '='},
            'toNodeElid': {'value': end_node, 'operator': '='},
        },
        'returnAttributes': [],
    }
    response = await api.fnt_client.rest_request('traySection', 'query', payload)
    if not response.success:
        msg = f'failed to get tray section: {response.message}'
        raise ValueError(msg)
    if len(response.data) == 1:
        return response.data[0]['elid']
    if len(response.data) > 1:
        logger.error(f'found more than one tray section for nodes {start_node} and {end_node}')
    return None


async def find_cable_route(
    api: FntAsyncAPI, cable_start: dict[str, str], cable_end: dict[str, str], intersections: list[dict[str, str]]
) -> list[TraySectionHop]:
    nodes = await get_node_mapping(api)
    intersections.append(cable_end)
    tray_section_path: list[TraySectionHop] = []
    current = cable_start
    success = True
    for sequence, optional_end in enumerate(intersections, start=1):
        # We try to connect the cable to the next end in the intersection (if it exists)
        current_node = nodes.get(current['id'])
        optional_end_node = nodes.get(optional_end['id'])
        if current_node is None or optional_end_node is None:
            message = f'failed to find node for {current["id"]}'
            raise ValueError(message)
        tray_section_elid = await get_tray_section_by_nodes(api, current_node, optional_end_node)
        if tray_section_elid is not None:
            tray_section_path.append(TraySectionHop(tray_section_elid, False, sequence))
            current = optional_end
            continue
        # Lets tray swapping the nodes
        tray_section_elid = await get_tray_section_by_nodes(api, optional_end_node, current_node)
        if tray_section_elid is not None:
            tray_section_path.append(TraySectionHop(tray_section_elid, True, sequence))
            current = optional_end
            continue
        success = False
        logger.error(f'failed to find tray section for nodes {current["id"]} and {optional_end["id"]}')

    if not success:
        return []
    return tray_section_path


async def load_cable(api: FntAsyncAPI, cable: 'Feature') -> None:
    cable_master = await get_cable_master_mapping(api)
    # FIXME choose the right cable name
    cable_name = f"{cable.properties['handle']}*"
    if await get_cable(api, cable_name):
        logger.info(f'cable {cable_name} already exists')
        return
    cable_type = f"{cable.properties['type']}-{cable.properties['cable_size']}"

    fnt_type = CABLE_TYPES.get(cable_type)
    if fnt_type is None:
        logger.error(f'cable type {cable_type} not found in cable types')
        return
    cable_type_elid = cable_master.get(fnt_type)
    if cable_type_elid is None:
        logger.error(f'cable type {fnt_type} not found in cable master')
        return
    cable_start = cable.properties.get('start')
    cable_end = cable.properties.get('end')
    if cable_start is None or cable_end is None:
        logger.error(f'cable {cable_name} is missing start or end')
        return
    # TODO if start or end does not have junction box or panel - create it (Junction for node and panel for building)
    intersections = cable.properties['intersections']
    current = cable_start
    section = 1
    logger.info(f'Processing cable: {cable_name} ({cable_type})')
    current_hops: list[dict[str, Any]] = []
    for optional_end in intersections:
        # We try to connect the cable to the next end in the intersection (if it exists)
        created = await connect_cable(api, cable, cable_type_elid, current, optional_end, section, current_hops)
        if created:
            current = optional_end
            section += 1
            current_hops = []
        current_hops.append(optional_end)

    await connect_cable(api, cable, cable_type_elid, current, cable_end, section, current_hops)


async def load_cables(api:FntAsyncAPI, path: AsyncPath) -> None:
    if DEVELOPMENT:
        await delete_cables(import_origin)
    async with path.joinpath('test_data/cables.json').open('r', encoding='utf-8') as file:
        content = await file.read()
        cables = FeatureCollection(features=json.loads(content)['features'])
    await init_cache(api)
    # for cable in cables:
    #     await load_cable(api, cable)
    proccessed = []
    for i in range(0, len(cables), CHUCK_SIZE):
        logger.info(f'processing cables {i} - {i+CHUCK_SIZE}')
        cable_handlers = [cable.properties['handle'] for cable in cables.features[i : i + CHUCK_SIZE]]
        logger.debug(f'processing cables {cable_handlers}')
        for handler in cable_handlers:
            if handler in proccessed:
                logger.info(f'skipping {handler}')
                continue
        await asyncio.gather(*[load_cable(api, cable) for cable in cables.features[i : i + CHUCK_SIZE]])
        proccessed.extend(cable_handlers)
        break
    #

    # logger.info(cable)


async def delete_cable(api: FntAsyncAPI, cable: 'Feature') -> None:
    # FIXME choose the right cable name
    cable_name = f"{cable.properties['handle']}*"
    fnt_cables = await get_cable(api, cable_name)
    for fnt_cable in fnt_cables:
        await delete_data_cable(api, fnt_cable['elid'])


async def delete_cables(path: AsyncPath) -> None:
    api = await setup_fnt()
    async with path.joinpath('cables.json').open('r', encoding='utf-8') as file:
        content = await file.read()
        cables = FeatureCollection(features=json.loads(content)['features'])
    for i in range(0, len(cables), CHUCK_SIZE):
        await asyncio.gather(*[delete_cable(api, cable) for cable in cables.features[i : i + CHUCK_SIZE]])


async def get_list_of_cable_types(path: AsyncPath) -> None:
    async with path.joinpath('cables.json').open('r', encoding='utf-8') as file:
        content = await file.read()
        cables = FeatureCollection(features=json.loads(content)['features'])
    cable_types = set()
    for cable in cables:
        cable_types.add(f"{cable.properties['type']}-{cable.properties['cable_size']}")
    logger.info(cable_types)


def route_cable(cable_elid: str, tray_sections: list[TraySectionHop]):
    logger.debug(f'route cable {cable_elid}')
    for tray_section in tray_sections:
        logger.debug(f'route cable {cable_elid} to tray section {tray_section}')
        sql = "SELECT spasys_element.GENERATEELID(14, 'STCCLI_BLOCKED_SOCKET', 'INFOS') AS NEW_ELID FROM dual"
        new_elid_ret = oracle_repo.fetch(sql)

        new_elid = new_elid_ret[0]['NEW_ELID']
        swap = 'Y' if tray_section.swap else 'N'
        # # TODO: Find the right CREATED_BY
        created_by = 'ALGWFLKQMBSZRH'

        sql = """
                INSERT INTO STLTRM_LINK
                (LINK_ELID, PARENT_ELEMENT, CHILD_ELEMENT, ARG_1, LINK_DESCRIPTION, STATUS_ACTION, SWAP, ARG_2, ARG_3, ARG_4, ARG_5, CREATED_BY, CREATE_DATE, REL_ID, NUM_OBJECTS_TO_PLACE)
                VALUES
                ({new_elid}, {tray_elid}, {cable_elid}, {sequence}, 'STCTRM_TRAY_SECTION_STCCLI_CABLE', 0, {swap}, NULL, NULL, NULL, {sequence}, {created_by}, SYSDATE, NULL, NULL)
            """
        oracle_repo.execute(
            sql,
            new_elid=new_elid,
            tray_elid=tray_section.elid,
            cable_elid=cable_elid,
            sequence=tray_section.sequence,
            swap=swap,
            created_by=created_by,
        )
    logger.info(f'Routed cable {cable_elid}')

    # Success


DEVELOPMENT = False
CHUCK_SIZE = 1

# if __name__ == '__main__':
#     import_origin = AsyncPath.cwd().joinpath('export/ארלוזורוב-ראשי_חדש')
#     OracleBaseRepository()._initilize(
#         host='10.90.39.2', port=1521, service_name='command', username='command', password='command'
#     )
#     # asyncio.run(get_list_of_cable_types(import_origin))
#     asyncio.run(load_cables(import_origin))
#     # asyncio.run(delete_cables(import_origin))
