from fnt_auto.models.base import RWModel


class PathRoute(RWModel):
    ser_elid: str = Field(rest_name='linkedElid')
    direction: DirectionOpt = Field(rest_name='direction')
    start_device: t.Optional[str] = Field(rest_name='multipointStartDeviceElid')
    end_device: t.Optional[str] = Field(rest_name='multipointEndDeviceElid')
    sequence_no: t.Optional[int] = Field(rest_name='sequenceNo')

class PathAttr(RWModel):
    id: t.Optional[str] = Field(rest_name='id')
    visible_id: t.Optional[str] = Field(rest_name='cServiceName')
    output_port_a: t.Optional[str] = Field(rest_name='createLinkLogicalPortOutputStart')
    output_port_z: t.Optional[str] = Field(rest_name='createLinkLogicalPortOutputEnd')

class PathCreate(ItemCreate, PathAttr):
    _route_over_multipoint: bool = Field(default=False)
    _master_data: t.Optional[TelcoMasterData]
    _start_port: t.Optional[str]
    type: str
    _type_elid: t.Optional[str] = Field(rest_name='createLinkServiceTypeDefinition')
    overbooking: bool = Field(rest_name='overbooking', default=True)
    route: t.List[PathRoute] = Field(rest_name='addRoute')


    @validator('type')
    def type_validator(cls, type:str, values:t.Dict[str, t.Any]):
        print(values)
        if type is not None:
            values['_master_data'] = TelcoMasterData(**globals.get_type_master_data(type))
            print(values['_master_data'])
            values['type_elid'] = values['_master_data'].elid
            if values['type_elid'] is None:
                msg = f'type [{type}] not found FNT.'
                raise ValueError(msg)
        return type

    @validator('route')
    def route_validator(cls, route:t.List[PathRoute], values:t.Dict[str, t.Any]) -> t.List[PathRoute]:
        if route:
            route_info, err = fntapi.get_services_infos([hop.ser_elid for hop in route])
            if err:
                logger.error(err)
                raise ApiError(err)
            for i, hop in enumerate(route):
                if hop.ser_elid not in route_info:
                    msg = f'\tRouted Service [{hop.ser_elid}] not found in FNT'
                    raise RouteMissing(msg)
                if hop.sequence_no is None:
                    hop.sequence_no = i+1
                if i == 0 and values.get('_start_port') == route_info[hop.ser_elid][0]['lp_z']:
                    hop.direction = 'BA'
                if route_info[hop.ser_elid][0]['serviceCategory'] == ServiceCategoryOpt.MULTIPOINT:
                    values['_route_over_multipoint'] = True
        return route

    def prepare_request(self) -> t.Dict[str, t.Any]:
        return super().prepare_request()

    @property
    def route_over_multipoint(self) -> bool:
        return self._route_over_multipoint

    @property
    def rest_entity(self) -> t.Optional[str]:
        if self._master_data.service_category == ServiceCategoryOpt.PATH:
            return 'serviceTelcoPath'
        return None

    @property
    def rest_operation(self) -> t.Optional[str]:
        if self._master_data.transmission_technology == TransmissionTechnologyOpt.PACKET_DATA:
            return 'createPacketData'
        elif self._master_data.transmission_technology == TransmissionTechnologyOpt.CIRCUIT_SWITCHED:
            return 'create'
        return None
