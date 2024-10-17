import sqlite3
from time import sleep, time
import requests
import asyncio
import requests


connect = sqlite3.connect('data.db')
cursor = connect.cursor()

class Status:
    def __init__(self, machine, code, tipe):
        self.__type = tipe
        self.__code = code
        self.__name = machine
        self.__connect = sqlite3.connect('data.db')
        self.__cursor = self.__connect.cursor()
        self.__api_on = 'api-on'
        self.__api_on_update = 'api-on-update'
        self.__api_steam = 'apt-steam'
        self.__api_steam_update = 'api-steam-update'
        self.__api_condensate = 'api-condensate'
        self.__api_condensate_update = 'api-condesate-update'
        self.__header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0",
            "Accept": "/",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "X-Requested-With": "XMLHttpRequest"
           }

    def update_data(self, value):
        command =   """UPDATE SENSOR SET VALUE_OLD = ? WHERE NAME = ?;"""
        self.__cursor.execute(command, (value, self.__name))
        self.__connect.commit()
        return True
    def update_session(self, value):
        command =   """UPDATE SENSOR SET SESSION = ? WHERE NAME = ?;"""
        self.__cursor.execute(command, (value, self.__name))
        self.__connect.commit()
        return True
    def send_on(self):
        print(self.__name,'ON')
        data = {
            "code": self.__code,
            "time": round(time())
        }
        while True:
            if self.__type == 'ON':
                api = self.__api_on
            if self.__type == 'IN':
                api = self.__api_steam
            if self.__type == 'OUT':
                api = self.__api_condensate
            try:
                    session = requests.post(url=api, headers=self.__header, data=data)
                    print(session.text)
                    session = session.text.split('"')
                    # print(session[0])
                    # print(session[1])
                    # print(session[9])
                    session = session[9]
                    self.update_session(str(session))
                    break
            except Exception as error:
                print(error)
    
    def send_off(self):
        print(self.__name, 'OFF')
        session = self.get_session()
        data = {
            "code": self.__code,
            "time": round(time()),
            "session": session,
            "off": "1"
        }
        while True:
            if self.__type == 'ON':
                api = self.__api_on_update
            if self.__type == 'IN':
                api = self.__api_steam_update
            if self.__type == 'OUT':
                api = self.__api_condensate_update
            try:
                send = requests.post(url=api, headers=self.__header, json=data)
                print(send.text)
                status = send.text.split('"')[5]
                if status == 'OK':
                    print("Here")
                    self.update_session('0')
                    break
                if status == 'FAILED':
                    break
            except Exception as error:
                print(error)
    
    def send_update(self):
        print(self.__name, "UPDATE")
        session = self.get_session()
        data = {
            "code": self.__code,
            "time": round(time()),
            "session": session,
        }
        while True:
            if self.__type == 'ON':
                api = self.__api_on_update
            if self.__type == 'IN':
                api = self.__api_steam_update
            if self.__type == 'OUT':
                api = self.__api_condensate_update
            try:
                send = requests.post(url=api, headers=self.__header, data=data)
                print(send.text)
                break
            except Exception as error:
                print(error)

    def get_session(self):
        data = []
        name = self.__name
        session = self.__cursor.execute('''SELECT * FROM SENSOR WHERE NAME = ?''',(name,))
        
        #append the data from db to array because cant get it rawly
        for row in session:
            data.append(row)
            # print(row)
        return str(data[0][5])
            
    def get_value(self):
        data = [] #create array for store data
        name = self.__name
        # print(name)
        #get data from database with name parameter
        self.__data = self.__cursor.execute('''SELECT * FROM SENSOR WHERE NAME = ?''',(name,))
        
        #append the data from db to array because cant get it rawly
        for row in self.__data:
            data.append(row)
            # print(row)
        #return the value and comparison with old value, true if value different
        data_now = data[0][3]
        data_old = data[0][4]
        session = data[0][5]
        #update data old on db
        self.update_data(data_now)
        print(data_old)
        print(session)
        #return the status by comparison of the old value
        if data_now == 1:
            if data_now == data_old:
                if session == None or session == '0':
                    return 'ON'
                return 'UPDATE'
            else:
                return 'ON'
        if data_now == 0:
            if data_now == data_old:
                if session != '0':
                    return 'OFF'
                return 'NONE'
            else:
                return 'OFF'
        
    async def loop_on(self):
        #loop for on off status
        while True:
            status = self.get_value()
            if status == 'ON':
                self.send_on()
            if status == 'OFF':
                self.send_off()
            # print("Here")
            await asyncio.sleep(1)
            
    
    async def loop_update(self):
        #loop for update on status
        while True:
            status = self.get_value()
            if status == 'UPDATE':
                self.send_update()
            await asyncio.sleep(180)
    
      
#update session with name and session input


# Station 1    
# on_st1 = Status('ON_ST1','MS1','ON')
# in_st1 = Status('IN_ST1','MS1','IN')
# out_st1 = Status('OUT_ST1','MS1','OUT')
on_dg1 = Status('ON_DG1','MD1','ON')
# on_sp1 = Status('ON_SP1','MSP1','ON')

# #Station 2
# on_st2 = Status('ON_ST2','MS2','ON')
# in_st2 = Status('IN_ST2','MS2','IN')
# out_st2 = Status('OUT_ST2','MS2','OUT')
# on_dg2 = Status('ON_DG2','MD2','ON')
# on_sp2 = Status('ON_SP2','MSP2','ON')

# #station 3
# on_st3 = Status('ON_ST3','MS3','ON')
# in_st3 = Status('IN_ST3','MS3','IN')
# out_st3 = Status('OUT_ST3','MS3','OUT')
# on_dg3 = Status('ON_DG3','MD3','ON')
# on_sp3 = Status('ON_SP3','MSP3','ON')

async def main():
   await asyncio.gather(on_dg1.loop_on()
                        )

try:
    asyncio.run(main())
except asyncio.CancelledError:
    pass

# while True:
#     try:
#         print(Steammer1.get_value())
#         # Steammer1.send_update()
#         # sensor = []
#         # name = "ON_ST1"
#         # data=cursor.execute('''SELECT * FROM SENSOR WHERE NAME = ?''',(name,))
#         # for row in data:
#         #     # print(row)
#         #     sensor.append(row)
#         # print(sensor[0][3])

#         # connect.commit()
#         # sensor.clear()
#         sleep(10)

#     except Exception as error:
#         print(error)
#         sleep(1)
