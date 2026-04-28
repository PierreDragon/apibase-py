import requests


class ApibaseError(Exception):
    pass


class _BaseClient:
    def __init__(self, base_url: str, token: str):
        self.base = base_url.rstrip('/')
        self._headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }

    def _parse(self, response: requests.Response) -> list | dict:
        try:
            data = response.json()
        except Exception:
            raise ApibaseError(f'HTTP {response.status_code}: non-JSON response')
        if data.get('status') != 'success':
            raise ApibaseError(data.get('message', 'Unknown error'))
        return data.get('data', data)


class ApibaseClient(_BaseClient):
    """
    Direct client — accesses your own base.
    Requires a token with scope=full.

    URL pattern: {base}/api/{method}/T{id}/L...
    """

    def get(self, table_id: int, primary: int = None, filters: list = None) -> list | dict:
        path = f'T{table_id}/L'
        params = {'format': 'assoc'}

        if primary is not None:
            path = f'T{table_id}/L{primary}'
        elif filters:
            for f in filters:
                path += f'/C{f["col"]}/O{f["op"]}'
            params['V'] = filters[0]['value']

        r = requests.get(f'{self.base}/api/get/{path}', headers=self._headers, params=params)
        return self._parse(r)

    def post(self, table_id: int, record: dict) -> dict:
        r = requests.post(
            f'{self.base}/api/post/T{table_id}',
            json={'record': record},
            headers=self._headers,
        )
        return self._parse(r)

    def put(self, table_id: int, primary: int | str, record: dict) -> dict:
        r = requests.put(
            f'{self.base}/api/put/T{table_id}/L{primary}',
            json={'record': record},
            headers=self._headers,
        )
        return self._parse(r)

    def delete(self, table_id: int, primary: int | str) -> dict:
        r = requests.delete(
            f'{self.base}/api/delete/T{table_id}/L{primary}',
            headers=self._headers,
        )
        return self._parse(r)


class HiveClient(_BaseClient):
    """
    Hive client — accesses another user's base via a shared basekey.
    Requires a token with scope=hive and ACL grants on the target tables.

    URL pattern: {base}/hive/{method}/{basekey}/T{id}/L...

    Hive workflow (data snapshot distribution):
        request(basekey, table_id)   → ask the owner to share a table
        approve(basekey, id_hive)    → owner approves the request
        publish(basekey, id_hive)    → owner pushes snapshot to requester's base
    """

    def get(self, basekey: str, table_id: int, primary: int = None, filters: list = None) -> list | dict:
        path = f'T{table_id}/L'
        params = {'format': 'assoc'}

        if primary is not None:
            path = f'T{table_id}/L{primary}'
        elif filters:
            for f in filters:
                path += f'/C{f["col"]}/O{f["op"]}'
            params['V'] = filters[0]['value']

        r = requests.get(
            f'{self.base}/hive/get/{basekey}/{path}',
            headers=self._headers,
            params=params,
        )
        return self._parse(r)

    def post(self, basekey: str, table_id: int, record: dict) -> dict:
        r = requests.post(
            f'{self.base}/hive/post/{basekey}/T{table_id}',
            json={'record': record},
            headers=self._headers,
        )
        return self._parse(r)

    def put(self, basekey: str, table_id: int, primary: int | str, record: dict) -> dict:
        r = requests.put(
            f'{self.base}/hive/put/{basekey}/T{table_id}/L{primary}',
            json={'record': record},
            headers=self._headers,
        )
        return self._parse(r)

    def delete(self, basekey: str, table_id: int, primary: int | str) -> dict:
        r = requests.delete(
            f'{self.base}/hive/delete/{basekey}/T{table_id}/L{primary}',
            headers=self._headers,
        )
        return self._parse(r)

    def request(self, basekey: str, table_id: int, comment: str = '') -> dict:
        r = requests.post(
            f'{self.base}/hive/request/{basekey}',
            json={'table_id': table_id, 'comment': comment},
            headers=self._headers,
        )
        return self._parse(r)

    def approve(self, basekey: str, id_hive: int) -> dict:
        r = requests.post(
            f'{self.base}/hive/approve/{basekey}',
            json={'id_hive': id_hive},
            headers=self._headers,
        )
        return self._parse(r)

    def publish(self, basekey: str, id_hive: int) -> dict:
        r = requests.post(
            f'{self.base}/hive/publish/{basekey}',
            json={'id_hive': id_hive},
            headers=self._headers,
        )
        return self._parse(r)
