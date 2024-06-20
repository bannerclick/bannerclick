import json
import logging
import os
import sqlite3
from pathlib import Path
from sqlite3 import (
    Connection,
    Cursor,
    IntegrityError,
    InterfaceError,
    OperationalError,
    ProgrammingError,
)
from typing import Any, Dict, List, Tuple

from openwpm.types import VisitId

from .storage_providers import StructuredStorageProvider, TableName
from datetime import datetime
import traceback

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")


def extract_domain(url: str) -> str:
    try:
        '''
        test string :
            https://google.com
            https://www.google.com
            www.google.com
            ://google.com
            /google.com
            //google.com
            http://www.google.com
            http://google.com
            google.com
        '''
        # Define a regular expression pattern to match various URL formats
        pattern = r'^((https:\/\/|http:\/\/|:\/\/|\/|\/\/)?(www\.)?)?(\S*?)(?=\/|$)'

        # Use the regular expression to extract the domain
        match = re.match(pattern, url)
        if match:
            domain = match.group(4)
            return domain
        else:
            return None
    except Exception as e:
        print('An exception occurred:', str(e))
        print('inside extract domain')
        print(url)


class BCSQLiteStorageProvider(StructuredStorageProvider):
    db: Connection
    cur: Cursor

    def __init__(self, db_path: Path) -> None:
        super().__init__()
        self.db_path = db_path
        self._sql_counter = 0
        self._sql_commit_time = 0
        self.logger = logging.getLogger("openwpm")
        # self.visits = dict()
        self.shared_dict = dict()

    def set_IPC_shared_dict(self, IPC_shared_dict):
        self.shared_dict = IPC_shared_dict
        self.logger.error('shared dict set, IPC started')

    async def init(self) -> None:
        self.db = sqlite3.connect(str(self.db_path))
        self.cur = self.db.cursor()
        self._create_tables()

    def _create_tables(self) -> None:
        """Create tables (if this is a new database)"""
        with open(SCHEMA_FILE, "r") as f:
            self.db.executescript(f.read())
        self.db.commit()

    async def flush_cache(self) -> None:
        self.db.commit()

    def add_stateful_cookies(self, table: TableName, visit_id: VisitId, record: Dict[str, Any]):
        '''
        tuple to distinguish cookies: 
            (name, host, path)

        table sent_cookies
            id
            name
            value
            host
            visit_id: sender
            event_ordinal
            url
            top_level_url
            time_stamp
            request_id
            resource_type
            setter: through joining with javascript_cookies table

        to be explored:
            triggering_origin TEXT,
            loading_origin TEXT,
            loading_href TEXT,

        '''
        if table == 'http_responses':
            return
        if 'headers' not in record:
            return
        if 'visit_id' not in record:
            return
        if 'url' not in record:
            return

        visit_id = record['visit_id']
        event_ordinal = record.get('event_ordinal', None)
        url = record.get('url', None)
        top_level_url = record.get('top_level_url', None)
        time_stamp = record.get('time_stamp', None)
        request_id = record.get('request_id', None)
        resource_type = record.get('resource_type', None)
        headers = json.loads(record['headers'])
        # Convert keys to lower case for case-insensitive access
        headers_lower = {k.lower(): v for k, v in headers}

        # Safely get the value of 'cookie', if it exists
        cookies = headers_lower.get('cookie', None)
        # Safely get the value of 'host', if it exists
        host = headers_lower.get('host', None)

        if not cookies:
            return

        cookies = cookies.split(';')
        for cookie in cookies:
            cookie = cookie.strip()
            equal_idx = cookie.find('=')
            key = cookie[:equal_idx]
            value = cookie[equal_idx + 1:]

            statement = r"INSERT INTO sent_cookies (name, value, host, visit_id, event_ordinal, url, top_level_url, time_stamp, request_id, resource_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            self.cur.execute(statement, (key, value, host, visit_id,
                             event_ordinal, url, top_level_url, time_stamp, request_id, resource_type,))

    async def store_record(
        self, table: TableName, visit_id: VisitId, record: Dict[str, Any]
    ) -> None:
        """Submit a record to be stored
        The storing might not happen immediately
        """

        if (table == 'http_requests'
            or table == 'http_responses'
            ) :
            self.add_stateful_cookies(
                table=table, visit_id=visit_id, record=record)
        else:
            assert self.cur is not None
            statement, args = self._generate_insert(table=table, data=record)
            # TODO: DATA INSERTED THROUGH THIS SQL QUERIES IN HERE
            for i in range(len(args)):
                if isinstance(args[i], bytes):
                    args[i] = str(args[i], errors="ignore")
                elif callable(args[i]):
                    args[i] = str(args[i])
                elif type(args[i]) == dict:
                    args[i] = json.dumps(args[i])
            try:
                self.cur.execute(statement, args)
                self._sql_counter += 1

                # if site_visits table is updated, save the changes immediately
                if (table == 'site_visits' and
                        'site_url' in record and
                        'visit_id' in record
                        ):
                    self.db.commit()
                    self.logger.error('database commited')
            except (
                OperationalError,
                ProgrammingError,
                IntegrityError,
                InterfaceError,
            ) as e:
                self.logger.error(
                    "Unsupported record:\n%s\n%s\n%s\n%s\n"
                    % (type(e), e, statement, repr(args))
                )

    @staticmethod
    def _generate_insert(
        table: TableName, data: Dict[str, Any]
    ) -> Tuple[str, List[Any]]:
        """Generate a SQL query from `record`"""
        statement = "INSERT INTO %s (" % table
        value_str = "VALUES ("
        values = list()
        first = True
        for field, value in data.items():
            statement += "" if first else ", "
            statement += field
            value_str += "?" if first else ",?"
            values.append(value)
            first = False
        statement = statement + ") " + value_str + ")"
        return statement, values

    def execute_statement(self, statement: str) -> None:
        self.cur.execute(statement)
        self.db.commit()

    async def finalize_visit_id(
        self, visit_id: VisitId, interrupted: bool = False
    ) -> None:
        try:
            if interrupted:
                self.logger.warning(
                    "Visit with visit_id %d got interrupted", visit_id)
                self.cur.execute(
                    "INSERT INTO incomplete_visits VALUES (?)", (visit_id,))
            self.db.commit()
        except Exception as e:
            self.logger.error(
                'during visit id finalization in provider exception occured')
            traceback_str = traceback.format_exc()
            self.logger.error(traceback_str)
            self.logger.error(f'An exception occurred: {str(e)} - {type(e)}')
            self.logger.error(f'{visit_id} failed to finalize')

    async def shutdown(self) -> None:
        self.db.commit()
        self.db.close()
