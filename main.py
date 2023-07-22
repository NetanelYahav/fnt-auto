import asyncio
import json
import logging
from pathlib import Path

from fnt_auto.async_api.async_client import FntAsyncClient
from fnt_auto.async_api import FntAsyncAPI
from fnt_auto.models import geo
from fnt_auto.models.location.campus import CampusCreateReq
from fnt_auto.models.location.building import BuildingCreateReq
from pydantic import ValidationError
from fnt_auto.resources import utils
from fnt_auto.import_tools.base import ItemsImporter
from fnt_auto.import_tools.location import CampusesImporter, BuildingsImporter
from fnt_auto.import_tools.inventory import DevicesImporter
from fnt_auto.import_tools.tray_mgmt import NodesImporter
from fnt_auto.models.inventory.device import DeviceCreateInZoneReq, DeviceCreateReq

logger = logging.getLogger(__name__)

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)-120s\t | %(filename)s:%(funcName)s:%(lineno)d',
    level=logging.INFO,
    datefmt='%F %T',
)


fnt_client = FntAsyncClient(base_url='http://iecinventory', username='command', password='KusAma772&')
fnt_client._session_id='qNKhzKUfEINJUFzcFfxHWQ'

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

class PartnerGovesImporter(NodesImporter):
    pass



async def main(): 
    # await fnt_client.login()
    
    import_engines: list[ItemsImporter] = [
        PartnerCampusesImporter(fnt_api),
        PartnerBuildingsImporter(fnt_api),
        PartnerSplittersImporter(fnt_api)
    ]

    for engine in import_engines:
        await engine.initialize()
        await engine.make_import()


if __name__ == '__main__':
    asyncio.run(main())


