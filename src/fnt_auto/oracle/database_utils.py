from __future__ import annotations

import logging
import typing
from itertools import count
from string import Formatter

from pydantic import BaseModel


if typing.TYPE_CHECKING:
    ...


logger = logging.getLogger(__package__)


def _log_query(query: str, query_params: typing.Sequence[typing.Any] | typing.Any) -> None:
    logger.debug(f'[Database] - query: {query}, values: {query_params}')


def _extract_params(query_params: dict[str, typing.Any] | BaseModel, keys: list[str]) -> dict[str, typing.Any]:
    params: dict[str, typing.Any] = {}
    if isinstance(query_params, BaseModel):
        query_params = query_params.dict()
    elif not isinstance(query_params, dict):
        logger.error(f'Unsupported params {type(query_params)}')
        return params
    for key, value in query_params.items():
        if key in keys:
            params[key] = value
    return params


@typing.overload
def _pyformat_to_psql(
    query: str,
    query_params: list[BaseModel] | list[dict[str, typing.Any]],
) -> tuple[str, typing.Iterator[tuple[typing.Any]]]:
    ...


@typing.overload
def _pyformat_to_psql(
    query: str, query_params: BaseModel | dict[str, typing.Any] | None
) -> tuple[str, typing.ValuesView[typing.Any]]:
    ...


def _pyformat_to_psql(
    query: str,
    query_params: (list[BaseModel] | list[dict[str, typing.Any]] | BaseModel | dict[str, typing.Any] | None) = None,
) -> tuple[str, typing.ValuesView[typing.Any] | typing.Iterator[tuple[typing.Any, ...]] | None]:
    params: (typing.ValuesView[typing.Any] | typing.Iterator[tuple[typing.Any, ...]] | dict[str, typing.Any]) = {}
    keys = [i[1] for i in Formatter().parse(query) if i[1] is not None]
    if query_params is None and len(keys) != 0:
        params = typing.cast(dict[str, typing.Any], params)
        logger.error(f'Missing query params: {keys}')
        return query, params.values()
    if query_params is None and len(keys) == 0:
        return query, None
    if isinstance(query_params, (BaseModel, dict)):
        params = _extract_params(query_params, keys)
        _keys = params.keys()
    elif isinstance(query_params, list) and len(query_params) > 0:
        _params = _extract_params(query_params[0], keys)
        _keys = _params.keys()
        params = (tuple(_extract_params(query_param, keys).values()) for query_param in query_params)
    else:
        logger.error(f'Unsupported Type {type(query_params)}')
    value_location = {}
    for key in _keys:
        value_location[key] = f':{key}'
    if isinstance(params, dict):
        return (query.format(**value_location), params)
    return (query.format(**value_location), params)


__all__ = ('_pyformat_to_psql', '_log_query')
