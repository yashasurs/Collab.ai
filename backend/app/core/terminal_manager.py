import docker
import asyncio
import threading
from typing import Dict

class TerminalManager:
    def __init__(self):
        self.client = docker.from_env()
        self.active_terminals: Dict[str, any] = {} # sid -> socket

    async def create_terminal_socket(self, container_id: str, sid: str, on_data_cb):
        """
        Creates an interactive shell inside a container and starts a thread to read its output.
        """
        try:
            container = self.client.containers.get(container_id)
            # Create exec instance with tty and stdin
            exec_id = self.client.api.exec_create(
                container.id, 
                cmd="/bin/sh", # Use sh as default for all OS images
                stdin=True, 
                tty=True, 
                stdout=True, 
                stderr=True
            )
            
            # Start exec instance and get back a socket
            sock = self.client.api.exec_start(exec_id['Id'], detach=False, tty=True, stream=True, socket=True)
            self.active_terminals[sid] = sock

            # Run reading in a separate thread to not block event loop
            def read_from_socket():
                try:
                    # Docker socket returns raw stream
                    # We need to skip the 8-byte header if not using TTY, 
                    # but with TTY=True, it should be a raw stream.
                    while sid in self.active_terminals:
                        data = sock.read(4096)
                        if not data:
                            break
                        asyncio.run_coroutine_threadsafe(on_data_cb(sid, data), asyncio.get_event_loop())
                except Exception as e:
                    print(f"Terminal read error for {sid}: {e}")
                finally:
                    self.close_terminal(sid)

            threading.Thread(target=read_from_socket, daemon=True).start()
            return True
        except Exception as e:
            print(f"Failed to create terminal for {container_id}: {e}")
            return False

    def write_to_terminal(self, sid: str, data: str):
        if sid in self.active_terminals:
            try:
                self.active_terminals[sid].write(data.encode())
            except Exception as e:
                print(f"Terminal write error for {sid}: {e}")
                self.close_terminal(sid)

    def resize_terminal(self, sid: str, cols: int, rows: int):
        # Resizing exec instance is tricky since we don't hold the exec ID directly in active_terminals
        # For simplicity, we might skip this or implement a more complex tracking
        pass

    def close_terminal(self, sid: str):
        if sid in self.active_terminals:
            sock = self.active_terminals.pop(sid)
            try:
                sock.close()
            except:
                pass

terminal_manager = TerminalManager()
