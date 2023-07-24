import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime

from fnt_auto.async_api.async_client import FntAsyncClient
from fnt_auto.async_api import FntAsyncAPI
from fnt_auto.models import geo
from pydantic import ValidationError
from fnt_auto.resources import utils
from fnt_auto.import_tools.base import ItemsImporter
from fnt_auto.import_tools.location import CampusesImporter, BuildingsImporter
from fnt_auto.import_tools.inventory import DevicesImporter
from fnt_auto.import_tools.tray_mgmt import NodesImporter, TraySectionsImporter
from fnt_auto.import_tools.inventory import JunctionBoxesFistImporter
from fnt_auto.models.location.campus import CampusCreateReq
from fnt_auto.models.location.building import BuildingCreateReq
from fnt_auto.models.inventory.device import DeviceCreateInZoneReq, DeviceCreateReq, DeviceQuery, DeviceMasterQuery
from fnt_auto.models.tray_mgmt.node import NodeCreateReq, NodeCreateAdvanceReq
from fnt_auto.models.tray_mgmt.tray_section import TraySectionCreateReq
from fnt_auto.models.location.zone import ZoneQuery, ZoneType
from fnt_auto.models.inventory.junction_box import JunctionBoxFistCreateInNodeReq, JunctionBoxFistCreateReq


logger = logging.getLogger(__name__)

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)-120s\t | %(filename)s:%(funcName)s:%(lineno)d',
    level=logging.INFO,
    datefmt='%F %T',
)


fnt_client = FntAsyncClient(base_url='http://iecinventory', username='command', password='KusAma772&')
fnt_client._session_id='svNWpYvyoi6AlE3XqrtBww'

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
        # self.fnt_buildings = utils.convert_to_dict(await self.fnt_api.location.building.get_all(), keys=['campus', 'name'])
    
    async def collect_items(self) -> list[BuildingCreateReq]:
        summary = {
            'Success': 0,
            'Failed': 0,
            'Skip': 0,
            'Duplication': 0
        }
        with path.joinpath('test_data/buildings.json').open('r', encoding='utf-8') as f:
            buildings_feat = geo.FeatureCollection(features=json.load(f)['features'])
        
        buildings: dict[str, BuildingCreateReq] = {}
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
            
            unique_id = f"{building_feat.properties['unique_id']}"
            if (entry:=building_feat.properties['entry']) is not None:
                unique_id = f"{unique_id}_{entry}"
                
            if unique_id in buildings:
                summary['Duplication'] += 1
                continue
        
            try:
                building = BuildingCreateReq(
                    name = unique_id,
                    description = building_feat.properties.get('visible_id'),
                    c_x = round(coordinates[0], 2),
                    c_y = round(coordinates[1], 2),
                    c_floors_num = prop['floors'],
                    c_business_num = prop['businesses'],
                    c_residential_num = prop['apartments'],
                    remark = building_feat.properties['id'],
                    campus_elid= self.fnt_campuses[city].elid
                )
            except ValidationError:
                logger.error(f"Failed to parse building [{unique_id}]")
                summary['Failed'] += 1
                continue
            
            # key = f"{city} | {building.name}"
            # if key in self.fnt_buildings:
            #     print(building.name, '->', building_feat.properties['unique_id'], building_feat.properties['entry'])
            #     # print(self.fnt_buildings[key].elid)
            #     id = f"{building_feat.properties['unique_id']}"
            #     if (entry:=building_feat.properties['entry']) is not None:
            #         id = f"{id}_{entry}"
                
            #     data = {'name': id}   
            #     res = await fnt_client.rest_elid_request('building', self.fnt_buildings[key].elid, 'rename', data)
            #     print(res)
            #     data = {'remark': building_feat.properties['id']}
            #     res = await fnt_client.rest_elid_request('building', self.fnt_buildings[key].elid, 'update', data)
            #     print(res)
            #     print("------------------------------------")
            summary['Success'] += 1

            buildings[building.name] = building
        self.parse_summary = summary
        return list(buildings.values())

class PartnerDevicesImporter(DevicesImporter):
    
    async def initialize(self):
        await super().initialize()
        self.fnt_buildings = utils.to_dict(await self.fnt_api.location.building.get_all(), key='name')
        self.fnt_devices_types = utils.to_dict(await fnt_api.inventory.device.get_all_types(), key='type')
        self.fnt_splitters_types = utils.to_dict(await fnt_api.inventory.device.get_types_by_query(DeviceMasterQuery(type='SPLITTER*', is_card=False)), key='type')
        # self.fnt_spliiters_by_zone = utils.to_dict_list(await fnt_api.inventory.device.get_by_query(DeviceQuery(type='SPLITTER*')), key='zone_elid')
        with path.joinpath('test_data/buildings.json').open('r', encoding='utf-8') as f:
            self.buildings_feat = geo.FeatureCollection(features=json.load(f)['features'])
    
    async def collect_items(self) -> list[DeviceCreateReq]:
        self.parse_summary = {
            'Success': 0,
            'Failed': 0,
            'Skip': 0,
            'Duplication': 0
        }

        new_devices = await self.collect_panel4_in_building() + await self.collect_splitters_in_buildings()
        
        return new_devices
    
    async def collect_splitters_in_buildings(self):
        buildings: dict[str, DeviceCreateReq] = {}
        for building_feat in self.buildings_feat:
            prop = building_feat.properties
            if prop.get('rozeta_coordinates') is None:
                continue
        
            if (city := prop.get('city_en')) is None:
                continue
            
            unique_id = f"{building_feat.properties['unique_id']}"
            if (entry:=building_feat.properties['entry']) is not None:
                unique_id = f"{unique_id}_{entry}"
                
            if unique_id in buildings:
                self.parse_summary['Duplication'] += 1
                continue

            splitters = building_feat.properties.get('splitter', [])
            if not splitters:
                continue
            
            for i, splitter in enumerate(splitters, start=1):
                splitter_type = f"SPLITTER_{'x'.join(splitter.split('/'))}"
                if splitter_type not in self.fnt_devices_types:
                    logger.error(f'Failed to find splitter device master for {splitter_type}')
                    self.parse_summary['Failed'] += 1
                    continue
               
                try:
                    splitter_type_elid = self.fnt_splitters_types[splitter_type].elid
                    zone_elid = self.fnt_buildings[unique_id].elid
                
                    splitter_postfix = f"SPL{splitter_type.split('_')[1].split('x')[1]}-{i}"
                    splitter_id = f"{unique_id}-{splitter_postfix}"

                    splitter = DeviceCreateInZoneReq(
                        id = splitter_id,
                        visible_id = splitter_id,
                        zone_elid = zone_elid,
                        type_elid = splitter_type_elid
                    )
                except (ValidationError, KeyError) as err:
                    self.parse_summary['Failed'] += 1
                    logger.exception(err)
                    continue
                
                self.parse_summary['Success'] += 1
                buildings[unique_id] = splitter
        
        return list(buildings.values())

    async def collect_panel4_in_building(self):
        panel_type = 'PFO-4LC-FTTH'
        if (master_data:=self.fnt_devices_types.get(panel_type)) is None:
            return []
    
        buildings: dict[str, DeviceCreateReq] = {}
        for building_feat in self.buildings_feat:
            prop = building_feat.properties
            if prop.get('rozeta_coordinates') is None:
                continue
        
            if (city := prop.get('city_en')) is None:
                continue
            
            unique_id = f"{building_feat.properties['unique_id']}"
            if (entry:=building_feat.properties['entry']) is not None:
                unique_id = f"{unique_id}_{entry}"
                
            if unique_id in buildings:
                self.parse_summary['Duplication'] += 1
                continue
            
            try:
                panel = DeviceCreateInZoneReq(
                    id = f"{unique_id}-PP",
                    zone_elid = self.fnt_buildings[unique_id].elid,
                    type_elid = master_data.elid
                )
            except (ValidationError, KeyError) as err:
                self.parse_summary['Failed'] += 1
                logger.exception(err)
                continue
            
            self.parse_summary['Success'] += 1

            buildings[unique_id] = panel
        
        return list(buildings.values())

class PartnerNodesImporter(NodesImporter):
    
    async def initialize(self):
        await super().initialize()
        self.fnt_campuses = utils.to_dict(await self.fnt_api.location.campus.get_all(), key='name')
        self.fnt_buildings = utils.to_dict(await self.fnt_api.location.building.get_all(), key='name')
        self.fnt_nodes_types = utils.to_dict(await self.fnt_api.tray_mgmt.node.get_all_types(), key='type')
    
    async def collect_items(self) -> list[NodeCreateReq]:
        self.parse_summary = {
            'Success': 0,
            'Failed': 0,
            'Skip': 0,
            'Duplication': 0
        }
        
        new_nodes = await self.collect_nodes_in_buildings() + await self.collect_regular_nodes()
        return new_nodes
    
    async def collect_nodes_in_buildings(self) -> list[NodeCreateReq]:
            node_type = 'EP_BLDG'
            with path.joinpath('test_data/buildings.json').open('r', encoding='utf-8') as f:
                buildings_feat = geo.FeatureCollection(features=json.load(f)['features'])

            if (master_data:=self.fnt_nodes_types.get(node_type)) is None:
                return []
        
            buildings: dict[str, NodeCreateReq] = {}
            for building_feat in buildings_feat:
                prop = building_feat.properties
                if prop.get('rozeta_coordinates') is None:
                    continue
            
                if (city := prop.get('city_en')) is None:
                    continue
                
                unique_id = f"{building_feat.properties['unique_id']}"
                if (entry:=building_feat.properties['entry']) is not None:
                    unique_id = f"{unique_id}_{entry}"
                    
                if unique_id in buildings:
                    self.parse_summary['Duplication'] += 1
                    continue

                node_id = f"BEP-{unique_id}"

                try:
                    building = self.fnt_buildings[unique_id]
                    new_node = NodeCreateReq(
                        zone_elid = building.elid,
                        type_elid = master_data.elid,
                        id = node_id,
                        visible_id = node_id,
                        coord_x = building.c_x,
                        coord_y = building.c_y,
                        #FIXME Add owner to building.json
                        c_node_owner = building_feat.properties.get('owner', 'Partner'),
                        #FIXME Add origin to building.json
                        c_import_origin = building_feat.properties.get('origin', "tests/test_data/ארלוזורוב-ראשי_חדש.dxf")  
                    )
                except (ValidationError, KeyError) as err:
                    self.parse_summary['Failed'] += 1
                    logger.exception(err)
                    continue
                
                self.parse_summary['Success'] += 1

                buildings[unique_id] = new_node
            return list(buildings.values())
        
    async def collect_regular_nodes(self) -> list[NodeCreateReq]:
            zone_elid = self.fnt_campuses['PartnerNodes'].elid
            FNT_TYPES = {'klozer 48': 'FIST-GB2-12', 'edge-cable': 'cable-edge-jb'}

            types_mapping = {
                'Pole': 'POLE',
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
                else:
                    node_type = types_mapping[node_type]
                
                node_id = node.properties['_id']
                
                if node_id in nodes:
                    self.parse_summary['Duplication'] += 1
                    continue

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
                except (ValidationError, KeyError) as err:
                    self.parse_summary['Failed'] += 1
                    logger.exception(err)
                    continue
                
                self.parse_summary['Success'] += 1
                nodes[node_id] = new_node
        
            return list(nodes.values())
    
class PartnerTraySectionsImporter(TraySectionsImporter):
    
    async def initialize(self):
        await super().initialize()
        self.fnt_tray_sections_types = utils.to_dict(await self.fnt_api.tray_mgmt.tray_section.get_all_types(), key='type')
        self.fnt_nodes = utils.to_dict(await self.fnt_api.tray_mgmt.node.get_all(), key='id')
        
        with path.joinpath('test_data/tray_sections.json').open('r', encoding='utf-8') as f:
            self.bezeq_data = geo.FeatureCollection(features=json.load(f)['features'])
        # with path.joinpath('test_data/building_tray_sections.json').open('r', encoding='utf-8') as f:
            # self.bezeq_data.extend(geo.FeatureCollection(features=json.load(f)['features']))
    
    async def collect_items(self) -> list[TraySectionCreateReq]:
        self.parse_summary = {
            'Success': 0,
            'Failed': 0,
            'Skip': 0,
            'Duplication': 0
        }

        trs_feat = self.bezeq_data.filter(lambda feature: feature.properties.get('layer', '') == 'traySection')
        
        tray_sections: dict[str, TraySectionCreateReq] = {}

        for trs in trs_feat:
            node_a = trs.properties['_from_node']
            node_b = trs.properties['_to_node']
            trs_id = trs.properties.get('_id', trs.properties.get('id'))
            
            if trs_id in tray_sections:
                self.parse_summary['Duplication'] += 1
                continue

            try:   
                node_a_elid = self.fnt_nodes[node_a].elid
                node_b_elid = self.fnt_nodes[node_b].elid
                new_trs = TraySectionCreateReq(
                    type_elid = self.fnt_tray_sections_types[trs.properties['_type']].elid,
                    from_node = node_a_elid,
                    to_node = node_b_elid,
                    c_geo_coords = json.dumps(trs.properties.get('geom', [])),
                    id = trs.properties['_id'],
                    visible_id = trs.properties['_id'],
                    c_tray_owner = trs.properties['owner'],
                    c_import_origin = trs.properties['origin'],
                    c_last_seen = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    segment_length = trs.properties['segment_length']
                )
    
            except (ValidationError, KeyError) as err:
                self.parse_summary['Failed'] += 1
                logger.exception(err)
                continue
            
            self.parse_summary['Success'] += 1
            tray_sections[trs_id] = new_trs
        
        return list(tray_sections.values())
    
class PartnerJunctionBoxesFistImporter(JunctionBoxesFistImporter):
    
    async def initialize(self):
        await super().initialize()
        self.fnt_campuses = utils.to_dict(await self.fnt_api.location.campus.get_all(), key='name')
        self.fnt_buildings = utils.to_dict(await self.fnt_api.location.building.get_all(), key='name')
        self.fnt_jb_types = utils.to_dict(await fnt_api.inventory.junction_box_fist.get_all_types(), key='type')
        self.fnt_nodes = utils.to_dict(await self.fnt_api.tray_mgmt.node.get_all(), key='id')

        with path.joinpath('test_data/nodes.json').open('r', encoding='utf-8') as f:
            self.bezeq_data = geo.FeatureCollection(features=json.load(f)['features'])
    
    async def collect_items(self) -> list[JunctionBoxFistCreateReq]:
        self.parse_summary = {
            'Success': 0,
            'Failed': 0,
            'Skip': 0,
            'Duplication': 0
        }
        
        # new_nodes = await self.collect_jb_in_buildings() + await self.collect_jb_in_nodes()
        return await self.collect_jb_in_nodes()
    
    async def collect_jb_in_buildings(self) -> list[JunctionBoxFistCreateReq]:
            node_type = 'EP_BLDG'
            with path.joinpath('test_data/buildings.json').open('r', encoding='utf-8') as f:
                buildings_feat = geo.FeatureCollection(features=json.load(f)['features'])

            if (master_data:=self.fnt_nodes_types.get(node_type)) is None:
                return []
        
            buildings: dict[str, NodeCreateReq] = {}
            for building_feat in buildings_feat:
                prop = building_feat.properties
                if prop.get('rozeta_coordinates') is None:
                    continue
            
                if (city := prop.get('city_en')) is None:
                    continue
                
                unique_id = f"{building_feat.properties['unique_id']}"
                if (entry:=building_feat.properties['entry']) is not None:
                    unique_id = f"{unique_id}_{entry}"
                    
                if unique_id in buildings:
                    self.parse_summary['Duplication'] += 1
                    continue

                node_id = f"BEP-{unique_id}"

                try:
                    building = self.fnt_buildings[unique_id]
                    new_node = NodeCreateReq(
                        zone_elid = building.elid,
                        type_elid = master_data.elid,
                        id = node_id,
                        visible_id = node_id,
                        coord_x = building.c_x,
                        coord_y = building.c_y,
                        #FIXME Add owner to building.json
                        c_node_owner = building_feat.properties.get('owner', 'Partner'),
                        #FIXME Add origin to building.json
                        c_import_origin = building_feat.properties.get('origin', "tests/test_data/ארלוזורוב-ראשי_חדש.dxf")  
                    )
                except (ValidationError, KeyError) as err:
                    self.parse_summary['Failed'] += 1
                    logger.exception(err)
                    continue
                
                self.parse_summary['Success'] += 1

                buildings[unique_id] = new_node
            return list(buildings.values())
        
    async def collect_jb_in_nodes(self) -> list[JunctionBoxFistCreateReq]:
            # FNT_TYPES = {'klozer 48': 'FIST-GB2-12', 'edge-cable': 'cable-edge-jb'}
            types_mapping = {
                'klozer 48': 'FIST_JBOX'
            }

            nodes_feat = self.bezeq_data.filter(lambda feature: feature.properties.get('_class', '') == 'node')
            
            nodes: dict[str, JunctionBoxFistCreateInNodeReq] = {}

            for node in nodes_feat:
                junction_box = node.properties.get('junction_box')
                if junction_box is None:
                    continue
                
                node_id = node.properties['_id']
                
                if node_id in nodes:
                    self.parse_summary['Duplication'] += 1
                    continue

                try:    
                    new_jb = JunctionBoxFistCreateInNodeReq(
                        node_elid = self.fnt_nodes[node_id].elid,
                        type_elid = self.fnt_jb_types[types_mapping[junction_box]].elid,
                        id = f"CE-{node_id}"
                    )

                except (ValidationError, KeyError) as err:
                    self.parse_summary['Failed'] += 1
                    logger.exception(err)
                    continue
                
                self.parse_summary['Success'] += 1
                nodes[node_id] = new_jb
        
            return list(nodes.values())
    
async def main(): 
    # await fnt_client.login()
    import_engines: list[ItemsImporter] = [
        # PartnerCampusesImporter(fnt_api),
        # PartnerBuildingsImporter(fnt_api),
        # PartnerDevicesImporter(fnt_api),
        # PartnerNodesImporter(fnt_api),
        # PartnerTraySectionsImporter(fnt_api),
        PartnerJunctionBoxesFistImporter(fnt_api)
    ]

    for engine in import_engines:
        await engine.initialize()
        # await engine._collect_items()
        # print(engine.parse_summary)
        await engine.make_import()


    # fnt_spliiters = utils.to_dict_list(await fnt_api.inventory.device.get_by_query(DeviceQuery(type='SPLITTER*')), key='zone_elid')

    # from pprint import pprint
    # pprint(fnt_spliiters)

    # trss = await fnt_api.tray_mgmt.tray_section.get_all()

    # for trs in trss:
    #     print(trs)

    # data = {
    #         "restrictions": {
    #             "id": {
    #             "value": "BEP-Giv*",
    #             "operator": "like"
    #             }
    #         },
    #         "returnAttributes": []
    # }
    # response = await fnt_client.rest_request('node', 'query', data)
    # for device in response.data:
    #     print(device['elid'], device['id'])
    #     res = await fnt_client.rest_elid_request('node',device['elid'], 'delete', {"handleCis": "DELETE_CIS"})
    #     # print(res)
    #     print("------------------------------------")

    # from fnt_auto.models.tray_mgmt.tray_section import TraySectionCreateReq
    # req = TraySectionCreateReq(
    #     id= 'ttt',
    #     from_node='3XVOWREL67T0JS',
    #     to_node='VN2MYZZ1IDAR40',
    #     type_elid='4Z6CE1UPJBEP7M'
    # )
    # ret = await fnt_api.tray_mgmt.tray_section.create(req)

    pass


if __name__ == '__main__':
    asyncio.run(main())


