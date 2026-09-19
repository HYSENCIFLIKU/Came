"""ETI/Domo client for CAME integration."""
from __future__ import annotations
import logging, threading
from typing import Callable
import requests
_LOGGER=logging.getLogger(__name__)
TIMEOUT=10
class RequestError(Exception): pass
class ServerNotFound(Exception): pass
class CommandNotFound(Exception): pass
class Domo:
    header={"Content-Type":"application/x-www-form-urlencoded","Connection":"Keep-Alive"}
    available_commands={"update":"status_update_req","relays":"relays_list_req","cameras":"tvcc_cameras_list_req","timers":"timers_list_req","thermoregulation":"thermo_list_req","analogin":"analogin_list_req","digitalin":"digitalin_list_req","lights":"nested_light_list_req","features":"feature_list_req","users":"sl_users_list_req","maps":"map_descr_req","scenarios":"scenario_activation_req","openings":"openings_list_req"}
    seasons={"off":"plant_off","winter":"winter","summer":"summer"}
    thermo_status={0:"off",1:"man",2:"auto",3:"jolly"}
    opening_actions={"stop":0,"open":1,"close":2}
    def __init__(self,host:str):
        self._host="http://"+host+"/domo/"; self._cseq=1; self.id=""; self._username=None; self._password=None
        self._lock=threading.RLock(); self._session=requests.Session(); self.items={}
        try: response=self._session.get(self._host,headers=self.header,timeout=TIMEOUT)
        except requests.RequestException as err: self._host=""; raise ServerNotFound from err
        if response.status_code!=200: self._host=""; raise ServerNotFound
    def login(self,username:str|None=None,password:str|None=None)->bool:
        with self._lock:
            if username is not None:self._username=username
            if password is not None:self._password=password
            p='command={"sl_cmd":"sl_registration_req","sl_login":"'+str(self._username)+'","sl_pwd":"'+str(self._password)+'"}'
            j=self._session.post(self._host,params=p,headers=self.header,timeout=TIMEOUT).json()
            self.id=j.get("sl_client_id",""); self._cseq=1
            if j.get("sl_data_ack_reason",-1)!=0:return False
            return True
    def _relogin(self)->bool:
        if not self._username:return False
        try:return self.login()
        except requests.RequestException:return False
    def keep_alive(self)->bool:
        with self._lock:
            p='command={"sl_client_id":"'+self.id+'","sl_cmd":"sl_keep_alive_req"}'
            j=self._session.post(self._host,params=p,headers=self.header,timeout=TIMEOUT).json()
            return True if j.get("sl_data_ack_reason",-1)==0 else self._relogin()
    def _post(self,build_param:Callable[[],str],command_name:str="UNKNOWN")->dict:
        with self._lock:
            for attempt in (1,2):
                j=self._session.post(self._host,params=build_param(),headers=self.header,timeout=TIMEOUT).json(); self._cseq+=1
                ack=j.get("sl_data_ack_reason",-1)
                if ack==0:return j
                if attempt==1 and self._relogin():continue
                raise RequestError(f"sl_data_ack_reason={ack}")
        raise RequestError("ETI/Domo request failed")
    def update_lists(self):
        for feature in self.list_request(self.available_commands["features"]).get("list",[]):
            if feature in self.available_commands:self.items[feature]=self.list_request(self.available_commands[feature])
    def list_request(self,cmd_name:str)->dict:
        if cmd_name not in self.available_commands.values():raise CommandNotFound
        def build():
            client_id="" if cmd_name=="map_descr_req" else '"client":"'+self.id+'",'
            if cmd_name=="sl_users_list_req":sl_cmd='"sl_cmd":"sl_users_list_req"'; sl_appl_msg=""
            else:
                sl_cmd='"sl_cmd":"sl_data_req"'
                sl_appl_msg='"sl_appl_msg":{'+client_id+'"cmd_name":"'+cmd_name+'","cseq":'+str(self._cseq)+'},"sl_appl_msg_type":"domo",'
            return "command={"+sl_appl_msg+'"sl_client_id":"'+self.id+'",'+sl_cmd+"}"
        return self._post(build,cmd_name)
    def switch(self,act_id:int,status:bool=True,is_light:bool=True)->dict:
        wanted="1" if status else "0"; cmd="light_switch_req" if is_light else "relay_activation_req"
        def build():return 'command={"sl_appl_msg":{"act_id":'+str(act_id)+',"client":"'+self.id+'","cmd_name":"'+cmd+'","cseq":'+str(self._cseq)+',"wanted_status":'+wanted+'},"sl_appl_msg_type":"domo","sl_client_id":"'+self.id+'","sl_cmd":"sl_data_req"}'
        return self._post(build,cmd)
    def thermo_mode(self,act_id:int,mode:int,temp:float)->dict:
        if mode not in [0,1,2,3]:raise RequestError
        value=int(round(temp*10,1))
        def build():return 'command={"sl_appl_msg":{"act_id":'+str(act_id)+',"client":"'+self.id+'","cmd_name":"thermo_zone_config_req","cseq":'+str(self._cseq)+',"extended_infos":0,"mode":'+str(mode)+',"set_point":'+str(value)+'},"sl_appl_msg_type":"domo","sl_client_id":"'+self.id+'","sl_cmd":"sl_data_req"}'
        return self._post(build,"thermo_zone_config_req")
    def change_season(self,season:str)->dict:
        if season not in ["plant_off","summer","winter"]:raise RequestError
        def build():return 'command={"sl_appl_msg":{"client":"'+self.id+'","cmd_name":"thermo_season_req","cseq":'+str(self._cseq)+',"season":"'+season+'"},"sl_appl_msg_type":"domo","sl_client_id":"'+self.id+'","sl_cmd":"sl_data_req"}'
        return self._post(build,"thermo_season_req")
    def opening(self,act_id:int,action:int)->dict:
        def build():return 'command={"sl_appl_msg":{"act_id":'+str(act_id)+',"client":"'+self.id+'","cmd_name":"opening_move_req","cseq":'+str(self._cseq)+',"wanted_status":'+str(action)+'},"sl_appl_msg_type":"domo","sl_client_id":"'+self.id+'","sl_cmd":"sl_data_req"}'
        return self._post(build,"opening_move_req")
