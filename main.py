import json
import logging
from pathlib import Path
from typing import Literal
from pprint import pprint
from fnt_auto.models import geo
from fnt_auto.models.zones.building import BuildingCreate
from pydantic import BaseModel, ValidationError
from fnt_auto._async_api import AsyncFntAPI

logger = logging.getLogger(__name__)

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d | %(levelname)-8s | %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
    level=logging.INFO,
    datefmt='%F %T',
)




fnt_api = AsyncFntAPI(base_url='http://iecinventory', username='command', password='KusAma772&')

async def sync_building():
    bc = BuildingCreate(name="MTB1", campus_elid="2X0Z0C5GPD8GS7")
    await fnt_api.create_building(bc, session_id='vxFgrbwMU3YD2Xh2k55AFg')
    logger.info(bc)
    logger.info(bc.rest_response)
    logger.info(bc.new_item_elid)
    logger.info(bc.status)


async def main():
    await sync_building()

import asyncio
loop = asyncio.get_event_loop()
loop.run_until_complete(sync_building())

