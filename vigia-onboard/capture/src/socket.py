import zmq

_CONTEXT = zmq.Context()

def create_socket(endpoint: str) -> zmq.Socket:
    socket = _CONTEXT.socket(zmq.PUB)
    socket.bind(endpoint)
    return socket

def close_socket(socket: zmq.Socket) -> None:
    socket.close()
    _CONTEXT.term()