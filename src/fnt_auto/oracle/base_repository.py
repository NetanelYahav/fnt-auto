from __future__ import annotations

import functools
import logging
import typing

import oracledb
from oracledb.defaults import defaults

from fnt_auto.oracle import database_utils


if typing.TYPE_CHECKING:
    from oracledb.pool import ConnectionPool
    from pydantic import BaseModel

TOracleBaseRepository = typing.TypeVar('TOracleBaseRepository', bound='OracleBaseRepository')

logger = logging.getLogger(__name__)


def _row_factory(columns: list[str], *args: tuple[typing.Any, ...]) -> dict[str, typing.Any]:
    return dict(zip(columns, args))


class OracleBaseRepository:
    __pool: ConnectionPool

    def __init__(self) -> None:
        ...

    def _disconnect(self) -> None:
        logger.info('Closing connection to database')
        type(self).__pool.close()
        logger.info('Connection closed')

    def _initilize(self, username: str, password: str, host: str, port: int, service_name: str, min_connection: int = 2, max_connection: int = 5,) -> None:
        type(self).__pool = oracledb.create_pool(
            dsn=oracledb.makedsn(
                host=typing.cast(str, host),
                port=typing.cast(int, port),
                sid=typing.cast(str, service_name),
            ),
            user=username,
            password=password,
            min=min_connection,
            max=max_connection,
        )

        logger.info('[database]: Connection established')

    def fetch(
        self,
        query: str,
        query_params: typing.Any = None,
        /,
        prefetchrows: int | None = 1000,
        arraysize: int | None = 1000,
        **kwargs: typing.Any,
    ) -> list[dict[str, typing.Any]]:
        database_utils._log_query(query, query_params or kwargs)
        params = query_params or kwargs or None
        with self.__pool.acquire() as connection, connection.cursor() as cursor:
            cursor.prefetchrows = prefetchrows or defaults.prefetchrows
            cursor.arraysize = arraysize or defaults.arraysize
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            cursor.rowfactory = functools.partial(_row_factory, columns)
            return cursor.fetchall()

    def fetch_row(
        self,
        query: str,
        query_params: typing.Any = None,
        /,
        **kwargs: typing.Any,
    ) -> dict[str, typing.Any] | None:
        database_utils._log_query(query, query_params or kwargs)
        params = query_params or kwargs or None
        with self.__pool.acquire() as connection, connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            cursor.rowfactory = lambda *args: dict(zip(columns, args))
            return cursor.fetchone()

    def fetch_value(
        self,
        query: str,
        query_params: typing.Any = None,
        /,
        **kwargs: typing.Any,
    ) -> typing.Any:
        database_utils._log_query(query, query_params or kwargs)
        params = query_params or kwargs or None
        with self.__pool.acquire() as connection, connection.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else None

    def execute(
        self,
        query: str,
        query_params: typing.Any = None,
        /,
        **kwargs: typing.Any,
    ) -> str:
        params = query_params or kwargs or None
        query, params = database_utils._pyformat_to_psql(query, query_params=params)
        database_utils._log_query(query, query_params or kwargs)
        with self.__pool.acquire() as connection, connection.cursor() as cursor:
            connection.autocommit = True
            cursor.execute(query, params)
            return cursor.rowcount

    def execute_many(
        self,
        query: str,
        query_params: (typing.Sequence[dict[str, typing.Any]] | typing.Sequence[BaseModel]),
    ) -> None:
        if len(query_params) == 0:
            msg = f'Not a list {type(query_params)}'
            raise Exception(msg)
        if isinstance(query_params, list):
            database_utils._log_query(query, query_params)
            query, params = database_utils._pyformat_to_psql(query, query_params=query_params)
        else:
            msg = f'Not a list {type(query_params)}'
            raise Exception(msg)
        with self.__pool.acquire() as connection, connection.cursor() as cursor:
            cursor.executemany(query, params)


# oracle_repo = OracleBaseRepository()
# __all__ = ('OracleBaseRepository', 'oracle_repo')
