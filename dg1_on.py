import sqlite3
from time import sleep, time
import requests
import asyncio

# Reuse database connection across the script
DB_PATH = 'data.db'

class Status:
    def __init__(self, machine, code, tipe):
        self._name = machine
        self._code = code
        self._type = tipe

        # API endpoints
        self._api_endpoints = {
            'ON': {'start': 'api-on', 'update': 'api-on-update'},
            'IN': {'start': 'api-steam', 'update': 'api-steam-update'},
            'OUT': {'start': 'api-condensate', 'update': 'api-condensate-update'}
        }

        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0",
            "Accept": "/",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "X-Requested-With": "XMLHttpRequest"
        }

    def _execute_query(self, query, params=()):
        """Helper to execute a SQL query and commit changes."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall()

    def update_value(self, value):
        """Update VALUE_OLD field in the database."""
        self._execute_query("UPDATE SENSOR SET VALUE_OLD = ? WHERE NAME = ?;", (value, self._name))

    def update_session(self, value):
        """Update SESSION field in the database."""
        self._execute_query("UPDATE SENSOR SET SESSION = ? WHERE NAME = ?;", (value, self._name))

    def get_session(self):
        """Retrieve the session value from the database."""
        result = self._execute_query("SELECT SESSION FROM SENSOR WHERE NAME = ?;", (self._name,))
        return result[0][0] if result else '0'

    def _send_request(self, api, data):
        """Send an HTTP POST request and return the response text."""
        try:
            response = requests.post(url=api, headers=self._headers, json=data)
            print(response.text)
            return response.text
        except Exception as e:
            print(f"Error sending request: {e}")
            return None

    def send_on(self):
        """Send an 'ON' status to the appropriate API."""
        print(f"{self._name} ON")
        data = {"code": self._code, "time": round(time())}
        api = self._api_endpoints[self._type]['start']

        while True:
            response = self._send_request(api, data)
            if response:
                session_id = response.split('"')[9]
                self.update_session(session_id)
                break

    def send_off(self):
        """Send an 'OFF' status to the appropriate API."""
        print(f"{self._name} OFF")
        session = self.get_session()
        data = {
            "code": self._code,
            "time": round(time()),
            "session": session,
            "off": "1"
        }
        api = self._api_endpoints[self._type]['update']

        while True:
            response = self._send_request(api, data)
            if response and 'OK' in response:
                self.update_session('0')
                break

    def send_update(self):
        """Send an 'UPDATE' status to the appropriate API."""
        print(f"{self._name} UPDATE")
        session = self.get_session()
        data = {"code": self._code, "time": round(time()), "session": session}
        api = self._api_endpoints[self._type]['update']

        while True:
            response = self._send_request(api, data)
            if response:
                break

    def get_value(self):
        """Retrieve and compare the current and old values from the database."""
        result = self._execute_query("SELECT VALUE, VALUE_OLD, SESSION FROM SENSOR WHERE NAME = ?;", (self._name,))
        if not result:
            return 'NONE'  # If no data found, return 'NONE'

        value_now, value_old, session = result[0]
        self.update_value(value_now)

        if value_now == 1:
            if value_now == value_old:
                return 'UPDATE' if session and session != '0' else 'ON'
            return 'ON'
        else:
            if value_now == value_old:
                return 'OFF' if session != '0' else 'NONE'
            return 'OFF'

    async def loop_on(self):
        """Continuously check and send 'ON' or 'OFF' status."""
        while True:
            status = self.get_value()
            if status == 'ON':
                self.send_on()
            elif status == 'OFF':
                self.send_off()
            await asyncio.sleep(1)

    async def loop_update(self):
        """Continuously send 'UPDATE' status every 3 minutes."""
        while True:
            status = self.get_value()
            if status == 'UPDATE':
                self.send_update()
            await asyncio.sleep(180)

# Example usage with Station 1
on_dg1 = Status('ON_DG1', 'MD1', 'ON')

async def main():
    """Main async function to run tasks."""
    await asyncio.gather(on_dg1.loop_on())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except asyncio.CancelledError:
        print("Process interrupted.")
