import zmq
import os
import time
import mlsimInterfaceMsgs_pb2

class MlSimConnector:

    def __init__(self, ipAddress, portNumber):
        os.environ['http_proxy'] = ''
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.ipAddress = ipAddress
        self.portNumber = portNumber
    def connect(self):
        self.socket.connect("tcp://"+self.ipAddress+ ":" + str(self.portNumber))
    def sendMessage(self, message):
        self.socket.send(message)
    def receiveMessage(self):
        return self.socket.recv()
