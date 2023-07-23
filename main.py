import asyncio
import json
import logging
from pathlib import Path

from fnt_auto.async_api.async_client import FntAsyncClient
from fnt_auto.async_api import FntAsyncAPI
from fnt_auto.models import geo
from pydantic import ValidationError
from fnt_auto.resources import utils
from fnt_auto.import_tools.base import ItemsImporter
from fnt_auto.import_tools.location import CampusesImporter, BuildingsImporter
from fnt_auto.import_tools.inventory import DevicesImporter
from fnt_auto.import_tools.tray_mgmt import NodesImporter
from fnt_auto.models.location.campus import CampusCreateReq
from fnt_auto.models.location.building import BuildingCreateReq
from fnt_auto.models.inventory.device import DeviceCreateInZoneReq, DeviceCreateReq
from fnt_auto.models.tray_mgmt.node import NodeCreateReq, NodeCreateAdvanceReq
from fnt_auto.models.location.zone import ZoneQuery, ZoneType

logger = logging.getLogger(__name__)

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)-120s\t | %(filename)s:%(funcName)s:%(lineno)d',
    level=logging.INFO,
    datefmt='%F %T',
)


fnt_client = FntAsyncClient(base_url='http://iecinventory', username='command', password='KusAma772&')
fnt_client._session_id='pE-vg8MwdiUF68SCMg9K7g'

fnt_api = FntAsyncAPI(fnt_client=fnt_client)

from pathlib import Path
path = Path.cwd()

class PartnerCampusesImporter(CampusesImporter):
    
    async def collect_items(self) -> list[CampusCreateReq]:
        summary = {
            'Success': 0,
            'Failed': 0,
            'Skip': 0,
            'Duplication': 0
        }
        with path.joinpath('test_data/buildings.json').open('r', encoding='utf-8') as f:
            buildings_feat = geo.FeatureCollection(features=json.load(f)['features'])
        
        campuses: dict[tuple[str,str], CampusCreateReq] = {}
        for building_feat in buildings_feat:
            prop = building_feat.properties
            if prop.get('rozeta_coordinates') is None:
                summary['Skip'] += 1
                continue
        
            if (city := prop.get('city_en')) is None:
                summary['Skip'] += 1
                continue
            
            if city in campuses:
                summary['Duplication'] += 1
                continue

            try:
                city_he = prop.get('city')
                campus = CampusCreateReq(
                    name = city,
                    description= city_he
                )
            except ValidationError:
                logger.error(f"\tFailed to parse Campus [{city}]")
                summary['Failed'] += 1
                continue
            
            summary['Success'] += 1

            campuses[city] = campus
        
        self.parse_summary = summary
        return list(campuses.values())

class PartnerBuildingsImporter(BuildingsImporter):
    
    async def initialize(self):
        await super().initialize()
        self.fnt_campuses = utils.convert_to_dict(await self.fnt_api.location.campus.get_all(), keys=['name'])
    
    async def collect_items(self) -> list[BuildingCreateReq]:
        summary = {
            'Success': 0,
            'Failed': 0,
            'Skip': 0,
            'Duplication': 0
        }
        with path.joinpath('test_data/buildings.json').open('r', encoding='utf-8') as f:
            buildings_feat = geo.FeatureCollection(features=json.load(f)['features'])
        
        buildings: dict[tuple[str,str], BuildingCreateReq] = {}
        for building_feat in buildings_feat:
            prop = building_feat.properties
            if prop.get('rozeta_coordinates') is None:
                summary['Skip'] += 1
                continue
        
            if (city := prop.get('city_en')) is None:
                summary['Skip'] += 1
                continue
            
            if city not in self.fnt_campuses:
                continue
            
            coordinates = prop.get('rozeta_coordinates')
            if coordinates is None:
                logger.error("Missing Cordinate")
                continue
            
            building_key = (city, building_feat.properties['id'])
            if building_key in buildings:
                summary['Duplication'] += 1
                continue
            try:
                building = BuildingCreateReq(
                    name = building_feat.properties['id'],
                    description = building_feat.properties.get('visible_id'),
                    c_x = round(coordinates[0], 2),
                    c_y = round(coordinates[1], 2),
                    c_floors_num = prop['floors'],
                    c_business_num = prop['businesses'],
                    c_residential_num = prop['apartments'],
                    remark = str(prop['unique_id']),
                    campus_elid= self.fnt_campuses[city].elid
                )
            except ValidationError:
                logger.error(f"Failed to parse building [{building_key}]")
                summary['Failed'] += 1
                continue
            
            summary['Success'] += 1

            buildings[building_key] = building
        self.parse_summary = summary
        return list(buildings.values())

class PartnerSplittersImporter(DevicesImporter):
    
    async def initialize(self):
        await super().initialize()
        self.fnt_buildings = utils.convert_to_dict(await self.fnt_api.location.building.get_all(), keys=['campus','name'])
        self.fnt_devices_types = utils.to_dict(await fnt_api.inventory.device.get_all_types(), key='type') 
    
    async def collect_items(self) -> list[DeviceCreateReq]:
        splitter_type = 'PFO-4LC-FTTH'
        summary = {
            'Success': 0,
            'Failed': 0,
            'Skip': 0,
            'Duplication': 0
        }
        with path.joinpath('test_data/buildings.json').open('r', encoding='utf-8') as f:
            buildings_feat = geo.FeatureCollection(features=json.load(f)['features'])
        
        if (master_data:=self.fnt_devices_types.get(splitter_type)) is None:
            return []
    
        buildings: dict[str, DeviceCreateReq] = {}
        for building_feat in buildings_feat:
            prop = building_feat.properties
            if prop.get('rozeta_coordinates') is None:
                continue
        
            if (city := prop.get('city_en')) is None:
                continue
            
            building_key = f"{city} | {building_feat.properties['id']}"

            if building_key in buildings:
                summary['Duplication'] += 1
                continue

            if building_key not in self.fnt_buildings:
                summary['skip'] += 1
                continue
            
            try:
                spliiter = DeviceCreateInZoneReq(
                    id = f"{building_key} | {splitter_type}",
                    zone_elid = self.fnt_buildings[building_key].elid,
                    type_elid = master_data.elid
                )
            except ValidationError:
                logger.error(f"Failed to parse splitter [{building_key}]")
                summary['Failed'] += 1
                continue
            
            summary['Success'] += 1

            buildings[building_key] = spliiter
        self.parse_summary = summary
        return list(buildings.values())


class PartnerNodesImporter(NodesImporter):
    
    async def initialize(self):
        await super().initialize()
        self.fnt_campuses = utils.to_dict(await self.fnt_api.location.campus.get_all(), key='name')
        self.fnt_nodes_types = utils.to_dict(await self.fnt_api.tray_mgmt.node.get_all_types(), key='type')
    
    async def collect_items(self) -> list[NodeCreateReq]:
        zone_elid = self.fnt_campuses['PartnerNodes'].elid

        summary = {
            'Success': 0,
            'Failed': 0,
            'Skip': 0,
            'Duplication': 0
        }

        FNT_TYPES = {'klozer 48': 'FIST-GB2-12', 'edge-cable': 'cable-edge-jb'}

        types_mapping = {
            'Pole': 'Pole',
            'MH_Reg': 'MH_Reg',
            'klozer 48': 'klozer 48',
            'B_TB': 'B_TB',
            'TS_UNDER': 'TS_UNDER',
            'TS_OVER': 'TS_OVER',
            'klozer FDT': 'klozer FDT',
        }

        with path.joinpath('test_data/nodes.json').open('r', encoding='utf-8') as f:
            bezeq_data = geo.FeatureCollection(features=json.load(f)['features'])

        nodes_feat = bezeq_data.filter(lambda feature: feature.properties.get('_class', '') == 'node')
        
        nodes: dict[str, NodeCreateReq] = {}

        for node in nodes_feat:
            node_type = node.properties['_type']
            if node_type not in types_mapping:
                types_mapping[node_type] = node_type
            
            node_id = node.properties['_id']
            
            if node_id in nodes:
                summary['Duplication'] += 1

            try:    
                new_node = NodeCreateReq(
                    zone_elid = zone_elid,
                    type_elid = self.fnt_nodes_types[node_type].elid,
                    # zone = ZoneQuery(campus_name='PartnerNodes', entity_name=ZoneType.CAMPUS),
                    id = node_id,
                    visible_id = node_id,
                    coord_x = node.properties['_x'],
                    coord_y = node.properties['_y'],
                    c_node_owner = node.properties['owner'],
                    c_import_origin = node.properties['origin']  
                )
            except (ValidationError, KeyError):
                summary['Failed'] += 1
                continue
            
            summary['Success'] += 1
            nodes[node_id] = new_node
        
        self.parse_summary = summary
        return list(nodes.values())
    

class PartnerTraySectionsImporter(TraySectionsImporter):
    
    async def initialize(self):
        await super().initialize()
        self.fnt_campuses = utils.to_dict(await self.fnt_api.location.campus.get_all(), key='name')
        self.fnt_nodes_types = utils.to_dict(await self.fnt_api.tray_mgmt.node.get_all_types(), key='type')
    
    async def collect_items(self) -> list[NodeCreateReq]:
        zone_elid = self.fnt_campuses['PartnerNodes'].elid

        summary = {
            'Success': 0,
            'Failed': 0,
            'Skip': 0,
            'Duplication': 0
        }

        FNT_TYPES = {'klozer 48': 'FIST-GB2-12', 'edge-cable': 'cable-edge-jb'}

        types_mapping = {
            'Pole': 'Pole',
            'MH_Reg': 'MH_Reg',
            'klozer 48': 'klozer 48',
            'B_TB': 'B_TB',
            'TS_UNDER': 'TS_UNDER',
            'TS_OVER': 'TS_OVER',
            'klozer FDT': 'klozer FDT',
        }

        with path.joinpath('test_data/nodes.json').open('r', encoding='utf-8') as f:
            bezeq_data = geo.FeatureCollection(features=json.load(f)['features'])

        nodes_feat = bezeq_data.filter(lambda feature: feature.properties.get('_class', '') == 'node')
        
        nodes: dict[str, NodeCreateReq] = {}

        for node in nodes_feat:
            node_type = node.properties['_type']
            if node_type not in types_mapping:
                types_mapping[node_type] = node_type
            
            node_id = node.properties['_id']
            
            if node_id in nodes:
                summary['Duplication'] += 1

            try:    
                new_node = NodeCreateReq(
                    zone_elid = zone_elid,
                    type_elid = self.fnt_nodes_types[node_type].elid,
                    # zone = ZoneQuery(campus_name='PartnerNodes', entity_name=ZoneType.CAMPUS),
                    id = node_id,
                    visible_id = node_id,
                    coord_x = node.properties['_x'],
                    coord_y = node.properties['_y'],
                    c_node_owner = node.properties['owner'],
                    c_import_origin = node.properties['origin']  
                )
            except (ValidationError, KeyError):
                summary['Failed'] += 1
                continue
            
            summary['Success'] += 1
            nodes[node_id] = new_node
        
        self.parse_summary = summary
        return list(nodes.values())
    


# def load_nodes(path: Path) -> None:
#     zone_elid = get_zone_by_name('nodes', 'campus')
#     if zone_elid is None:
#         zone_elid = create_campus('nodes', 'campus')

#     # FIXME make name of the file smarter
#     with path.joinpath('nodes.json').open('r', encoding='utf-8') as f:
#         bezeq_data = FeatureCollection(features=json.load(f)['features'])

#     node_cache = load_nodes_cache()

#     nodes = bezeq_data.filter(lambda feature: feature.properties.get('_class', '') == 'node')
#     for node in nodes:
#         node_type = node.properties['_type']
#         if node_type not in types_mapping:
#             types_mapping[node_type] = node_type
#         node_id = node.properties['_id']
#         if node_id in node_cache:
#             continue
#         node_elid = create_node(node, zone_elid)
#         junction_box = node.properties.get('junction_box')
#         node_cache[node.properties['_id']] = node_elid
#         if junction_box is None:
#             continue
#         type_name = FNT_TYPES.get(junction_box)
#         if type_name is None:
#             logger.error(f'Failed to find type for {junction_box}')
#             continue
#         place_junction_box_fist_in_node(node_elid, node.properties['_id'], type_name)

# def create_node(node: 'Feature', zone_elid: str) -> str:
#     type_elid = get_node_type_by_name(node.properties['_type'])
#     if type_elid is None:
#         msg = f'Failed to find node type for {node.properties["_type"]}'
#         raise Exception(msg)
#     payload = {
#         'createLinkNodeType': {'linkedElid': type_elid},
#         'createLinkZone': {'linkedElid': zone_elid},
#         'coordX': node.properties['_x'],
#         'coordY': node.properties['_y'],
#         'id': node.properties['_id'],
#         'visibleId': node.properties['_id'],
#         'cNodeOwner': node.properties['owner'],
#         'cImportOrigin': node.properties['origin'],
#     }
#     response, err = api.rest_request('node', 'create', payload)
#     if err is not None:
#         logger.error(f'Failed to create node: {err}')
#         raise Exception(err)
#     return response['returnData']['elid']



async def main(): 
    # await fnt_client.login()
    
    import_engines: list[ItemsImporter] = [
        PartnerCampusesImporter(fnt_api),
        PartnerBuildingsImporter(fnt_api),
        PartnerSplittersImporter(fnt_api),
        PartnerNodesImporter(fnt_api),
        # PartnerTraySectionsImporter(fnt_api)
    ]

    for engine in import_engines:
        await engine.initialize()
        await engine.make_import()

    # print(await fnt_api.tray_mgmt.node.get_master_data('POLE'))

    # node_importer = PartnerNodesImporter(fnt_api)
    # await node_importer.initialize()
    # await node_importer.make_import()


if __name__ == '__main__':
    asyncio.run(main())


