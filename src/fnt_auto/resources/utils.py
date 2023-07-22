import typing
from pydantic import BaseModel

from fnt_auto.models.api import RestResponse

T = typing.TypeVar('T', bound=BaseModel)

def to_dict(items: list[T], key:str='elid') -> dict[str, T]:
    ret: dict[str, T] = {}
    for item in items:
        if not issubclass(type(item), BaseModel):
            continue
        ret[getattr(item, key)] = item
    return ret

def convert_to_dict(items: list[T], keys:list[str]=['elid'], delimiter:str = ' | ') -> dict[str, T]:
    ret: dict[str, T] = {}
    for item in items:
        if not issubclass(type(item), BaseModel):
            continue
        key = delimiter.join([getattr(item, key) for key in keys])
        if key.endswith(delimiter):
             key = key[:-len(delimiter)]
        ret[key] = item
    return ret

