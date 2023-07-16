from enum import Enum

from fnt_auto.models import base


class DirectionOpt(str, Enum):
    AB = 'AB'
    BA = 'BA'

class TransmissionTechnologyOpt(str, Enum):
    CIRCUIT_SWITCHED = 'CIRCUIT_SWITCHED'
    PACKET_DATA = 'PACKET_DATA'

class ServiceCategoryOpt(str, Enum):
    CONCATENATED_PATH = 'CONCATENATED_PATH'
    BEARER = 'BEARER'
    PATH = 'PATH'
    MULTIPOINT = 'MULTIPOINT'
    POINT_TO_POINT = 'POINT_TO_POINT'


class TelcoMasterData(RWModel):
    elid: str
    service_category: str = Field(alias='serviceCategory')
    transmission_technology: TransmissionTechnologyOpt = Field(alias='transmissionTechnology')
    service_category: ServiceCategoryOpt = Field(alias='serviceCategory')
