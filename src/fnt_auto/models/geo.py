import logging
import math
import typing
from typing import Any, Dict, List, Literal, Tuple, Union

from pydantic import BaseModel, Field, conlist
from pyproj import CRS, Transformer
from pyproj.enums import TransformDirection
from shapely import geometry as shapely_geometry


if typing.TYPE_CHECKING:
    Coordinates = Union[Tuple[float, float, float], Tuple[float, float]]
else:
    Coordinates = conlist(float, min_length=2, max_length=3)


EPSG2039_PROJ = '+proj=tmerc +lat_0=31.7343936111111 +lon_0=35.2045169444445 +k=1.0000067 +x_0=219529.584 +y_0=626907.39 +ellps=GRS80 +towgs84=-24.002400,-17.103200,-17.844400,-0.33077,-1.852690,1.669690,5.424800 +units=m +no_defs'

transformer = Transformer.from_crs(CRS.from_proj4(EPSG2039_PROJ), 4326, always_xy=True)

logger = logging.getLogger(__package__)


class BaseGeometry(BaseModel):
    type: str  # noqa: A003
    coordinates: Coordinates

    @staticmethod
    def _convert_to_2039(coordinates: 'Coordinates') -> 'Coordinates':
        x = coordinates[0]
        y = coordinates[1]
        if x < 180 and x > -180:
            coordinates = transformer.transform(
                xx=coordinates[0], yy=coordinates[1], direction=TransformDirection.FORWARD
            )
        elif x < 150_000:
            coordinates = (x + 50000, y + 500000)
        return coordinates

    @staticmethod
    def _convert_to_4326(coordinates: 'Coordinates') -> 'Coordinates':
        x = coordinates[0]
        y = coordinates[1]
        if y > 360_000:
            transformer.transform(xx=x, yy=y, direction=TransformDirection.FORWARD)
            return transformer.transform(xx=x, yy=y, direction=TransformDirection.FORWARD)
        if x > 180 and y > 180:
            # Already in 4326
            return transformer.transform(xx=x, yy=y, direction=TransformDirection.FORWARD)
        return coordinates

        return None

    @property
    def geom(self):
        return self.json()

    def __eq__(self, other: 'object') -> bool:
        if not isinstance(other, BaseGeometry) or self.type != other.type:
            return False
        return self.coordinates == other.coordinates


class Point(BaseGeometry):
    type: Literal['Point'] = 'Point'  # noqa: A003
    coordinates: Coordinates

    @property
    def x(self) -> float:
        return self.coordinates[0]

    @property
    def y(self) -> float:
        return self.coordinates[1]

    @property
    def shapely(self) -> 'shapely_geometry.Point':
        return shapely_geometry.Point(*self.coordinates)

    def within(self, other: 'Point', distance: float) -> bool:
        return other.shapely.within(self.shapely.buffer(distance))

    def distance_to(self, other: 'Point') -> float:
        # This is ITM distance calculation
        if self.x > 180 and self.y > 180 and other.x > 180 and other.y > 180:
            return math.sqrt(pow(self.x - other.x, 2) + pow(self.y - other.y, 2))
        return self.shapely.distance(other.shapely)

    def convert_to_2039(self) -> None:
        self.coordinates = self._convert_to_2039(self.coordinates)

    def convert_to_4326(self) -> None:
        self.coordinates = self._convert_to_4326(self.coordinates)


class MultiPoint(BaseGeometry):
    type: Literal['MultiPoint'] = 'MultiPoint'  # noqa: A003
    coordinates: List[Coordinates]

    @property
    def shapely(self) -> 'shapely_geometry.MultiPoint':
        return shapely_geometry.MultiPoint(self.coordinates)

    def convert_to_2039(self) -> None:
        self.coordinates = [self._convert_to_2039(coordinates) for coordinates in self.coordinates]

    def convert_to_4326(self) -> None:
        self.coordinates = [self._convert_to_4326(coordinates) for coordinates in self.coordinates]


class LineString(BaseGeometry):
    type: Literal['LineString'] = 'LineString'  # noqa: A003
    coordinates: List[Coordinates]

    @property
    def shapely(self) -> 'shapely_geometry.LineString':
        return shapely_geometry.LineString(self.coordinates)

    def convert_to_2039(self) -> None:
        self.coordinates = [self._convert_to_2039(coordinates) for coordinates in self.coordinates]

    def convert_to_4326(self) -> None:
        self.coordinates = [self._convert_to_4326(coordinates) for coordinates in self.coordinates]

    @property
    def length(self) -> float:
        return self.shapely.length

    @property
    def points(self) -> List[Point]:
        return [Point(coordinates=coordinates) for coordinates in self.coordinates]


class MultiLineString(BaseGeometry):
    type: Literal['MultiLineString'] = 'MultiLineString'  # noqa: A003
    coordinates: List[List[Coordinates]]

    @property
    def shapely(self) -> 'shapely_geometry.MultiLineString':
        return shapely_geometry.MultiLineString(self.coordinates)

    def convert_to_2039(self) -> None:
        self.coordinates = [[self._convert_to_2039(coordinates) for coordinates in line] for line in self.coordinates]

    def convert_to_4326(self) -> None:
        self.coordinates = [[self._convert_to_4326(coordinates) for coordinates in line] for line in self.coordinates]


class Polygon(BaseGeometry):
    type: Literal['Polygon'] = 'Polygon'  # noqa: A003
    coordinates: List[List[Coordinates]]

    @property
    def shapely(self) -> 'shapely_geometry.Polygon':
        return shapely_geometry.Polygon(self.coordinates)

    def convert_to_2039(self) -> None:
        self.coordinates = [[self._convert_to_2039(coordinates) for coordinates in line] for line in self.coordinates]

    def convert_to_4326(self) -> None:
        self.coordinates = [[self._convert_to_4326(coordinates) for coordinates in line] for line in self.coordinates]


class MultiPolygon(BaseGeometry):
    type: Literal['MultiPolygon'] = 'MultiPolygon'  # noqa: A003
    coordinates: List[List[List[Coordinates]]]

    @property
    def shapely(self) -> 'shapely_geometry.MultiPolygon':
        return shapely_geometry.MultiPolygon(self.coordinates)

    def convert_to_2039(self) -> None:
        self.coordinates = [
            [[self._convert_to_2039(coordinates) for coordinates in line] for line in polygon]
            for polygon in self.coordinates
        ]

    def convert_to_4326(self) -> None:
        self.coordinates = [
            [[self._convert_to_4326(coordinates) for coordinates in line] for line in polygon]
            for polygon in self.coordinates
        ]


class GeometryCollection(BaseModel):
    type: Literal['GeometryCollection'] = 'GeometryCollection'  # noqa: A003
    geometries: List[Union[Point, MultiPoint, LineString, MultiLineString, Polygon, MultiPolygon]]

    @property
    def geom(self):
        return self.json()

    @property
    def shapely(self) -> 'shapely_geometry.GeometryCollection':
        return shapely_geometry.GeometryCollection(self.geometries)

    def convert_to_2039(self) -> None:
        self.coordinates = [geometry.convert_to_2039() for geometry in self.geometries]

    def convert_to_4326(self) -> None:
        self.coordinates = [geometry.convert_to_4326() for geometry in self.geometries]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GeometryCollection) or len(self.geometries) != len(other.geometries):
            return False
        return self.geometries == other.geometries


class Feature(BaseModel):
    type: Literal['Feature'] = 'Feature'  # noqa: A003
    geometry: Union[Point, MultiPoint, LineString, MultiLineString, Polygon, MultiPolygon, GeometryCollection]
    properties: dict[str, Any] = Field(default_factory=dict)

    @property
    def geom(self):
        return self.geometry.geom

    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        return self.shapely.bounds

    @property
    def shapely(self) -> 'shapely_geometry.base.BaseGeometry':
        return self.geometry.shapely

    def convert_to_2039(self) -> None:
        self.geometry.convert_to_2039()

    def convert_to_4326(self) -> None:
        self.geometry.convert_to_4326()

    def add_property(self, key: str, value: Any) -> None:
        if key in self.properties and not isinstance(self.properties[key], list):
            msg = f'Property {key} already exists'
            raise KeyError(msg)
        if key in self.properties and isinstance(self.properties[key], list):
            self.properties[key].extend(value) if isinstance(value, list) else self.properties[key].append(value)
        else:
            self.properties[key] = value

    def set_property(self, key: str, value: Any) -> None:
        if key not in self.properties:
            msg = f'Property {key} does not exists'
            raise KeyError(msg)
        self.properties[key] = value

    def remove_property(self, key: str) -> None:
        if key not in self.properties:
            msg = f'Property {key} does not exists'
            raise KeyError(msg)
        del self.properties[key]

    def remove_properties(self, keys: List[str]) -> None:
        for key in keys:
            self.remove_property(key)

    def __eq__(self, other: 'object') -> bool:
        if not isinstance(other, Feature) or self.geometry.type != other.geometry.type:
            return False
        return self.geometry == other.geometry


class FeatureCollection(BaseModel):
    type: Literal['FeatureCollection'] = 'FeatureCollection'  # noqa: A003
    features: 'List[Feature]' = Field(default_factory=list)

    @property
    def geom(self):
        return self.json(ensure_ascii=False)

    @property
    def shapely(self) -> 'shapely_geometry.base.BaseGeometry':
        return shapely_geometry.GeometryCollection([feature.shapely for feature in self.features])

    def convert_to_2039(self) -> None:
        for feature in self.features:
            feature.convert_to_2039()

    def convert_to_4326(self) -> None:
        for feature in self.features:
            feature.convert_to_4326()

    def add_feature(self, feature: Feature) -> None:
        self.features.append(feature)

    def extend(self, other: 'FeatureCollection') -> None:
        self.features.extend(other.features)

    def filter(self, func: typing.Callable[[Feature], bool], remove: bool = False) -> 'FeatureCollection':  # noqa: A003
        logger.debug(f'current features: {len(self.features)}')
        collection = FeatureCollection(features=list(filter(func, self.features)))
        logger.debug(f'filtered features: {len(collection.features)}')
        if remove:
            self.features = list(filter(lambda feature: not func(feature), self.features))
            logger.debug(f'remaining features: {len(self.features)}')
        return collection

    def closest(
        self,
        point: 'Point',
        /,
        *,
        min_distance: typing.Union[float, None] = None,
        max_distance: typing.Union[float, None] = None,
    ) -> 'typing.Union[Feature, None]':
        feature: 'typing.Union[Feature,None]' = None
        lowest_distance = None
        for _feature in self.features:
            distance = _feature.geometry.distance_to(point)
            if min_distance is not None and distance < min_distance:
                continue
            if max_distance is not None and distance > max_distance:
                continue
            if lowest_distance is not None and lowest_distance < distance:
                continue
            lowest_distance = distance
            feature = _feature
        return feature

    def __iter__(self) -> typing.Iterator[Feature]:
        return iter(self.features)

    def __len__(self) -> int:
        return len(self.features)

    def __eq__(self, other: 'object') -> bool:
        if not isinstance(other, FeatureCollection) or len(self.features) != len(other.features):
            return False
        return self.features == other.features
