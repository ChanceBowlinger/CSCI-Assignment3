import socketserver
import logging
import json
import random
import socket
import threading

from message import message, message_type

logging.basicConfig(level=logging.DEBUG,
                    format='%(name)s: %(message)s',
                    )


class request_handler(socketserver.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        self.logger = logging.getLogger('request_handler')
        self.logger.debug('__init__')
        self.central_hub : central_hub = server
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)
        return

    def handle(self):
        self.logger.debug('handle')

        # Echo the back to the client
        data = self.request.recv(1024).decode('utf-8')

        data = json.loads(data)
        data : message = message(**data)
        if data.message_type == message_type.CONNECT_TO_CENTRAL_HUB:
            self.central_hub.players.append(data.sent_by)
            self.request.send("Connected to central hub".encode('utf-8'))
        else:
            active_players = self.central_hub.get_active_players(data.sent_by)

            new_message = message(message_type=message_type.NEW_NEIGHBOR_RESPONSE, sent_by=self.central_hub.server_address, content=active_players)
            self.request.send(json.dumps(new_message.__dict__).encode('utf-8'))
        return

class central_hub(socketserver.TCPServer):
    
    def __init__(self, server_address, handler_class=request_handler):
        self.logger = logging.getLogger('central_hub')
        self.logger.debug('__init__')
        socketserver.TCPServer.__init__(self, server_address, handler_class)
        self.players = []
        return
    
    def ping_player(self, player):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect((player[0], player[1]))
            s.close()
            return True
        except OSError:
            return False

    # Return a list of active players connected to the central hub
    def get_active_players(self, requesting_player):
        active, dead = [], []
        for player in self.players:
            if list(player) == list(requesting_player):
                continue
            if self.ping_player(player):
                active.append(player)
            else:
                dead.append(player)
        for player in dead:
            self.players.remove(player)
        if len(active) > 5:
            return random.sample(active, 5)
        return active

if __name__ == '__main__':
    address = ('localhost', 3000) # let the kernel give us a port

    server = central_hub(address, request_handler)
    ip, port = server.server_address # find out what port we were given

    logger = logging.getLogger('central_hub')
    logger.info('Central Hub is on %s:%s', ip, port)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    logger.info('Serving in background thread, press Ctrl+C to stop')
    try:
        while server_thread.is_alive():
            server_thread.join(timeout=1.0)
    except KeyboardInterrupt:
        logger.info('Shutting down...')
        server.shutdown()