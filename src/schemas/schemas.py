from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional


class PointTuple(BaseModel):
    """Validador para puntos [lat, lng]"""
    model_config = ConfigDict(arbitrary_types_allowed=True)


class Route(BaseModel):
    id_trm_cs: int
    nombre_tramo: str
    color: str
    points: list[list[float]]

    @field_validator('points')
    @classmethod
    def validate_points(cls, v):
        if not v or len(v) < 2:
            raise ValueError('Route must have at least 2 points')
        for point in v:
            if not isinstance(point, list) or len(point) != 2:
                raise ValueError('Each point must be [lat, lng]')
            if not all(isinstance(x, (int, float)) for x in point):
                raise ValueError('Coordinates must be numbers')
        return v

    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be hex format like #RRGGBB')
        return v


class LocationPoint(BaseModel):
    id: int
    name: str
    coor: list[float]
    radio: Optional[int] = None

    @field_validator('coor')
    @classmethod
    def validate_coor(cls, v):
        if not isinstance(v, list) or len(v) != 2:
            raise ValueError('Coordinate must be [lat, lng]')
        if not all(isinstance(x, (int, float)) for x in v):
            raise ValueError('Coordinates must be numbers')
        return v


class DataFile(BaseModel):
    Routes: list[Route]
    Load: list[LocationPoint]
    Dump: list[LocationPoint]

    @field_validator('Routes')
    @classmethod
    def validate_routes_not_empty(cls, v):
        if not v:
            raise ValueError('Must have at least one route')
        return v

    @field_validator('Load')
    @classmethod
    def validate_loads_not_empty(cls, v):
        if not v:
            raise ValueError('Must have at least one load point')
        return v

    @field_validator('Dump')
    @classmethod
    def validate_dumps_not_empty(cls, v):
        if not v:
            raise ValueError('Must have at least one dump point')
        return v
