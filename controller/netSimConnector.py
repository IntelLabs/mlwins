import zmq
import os
import time
import random
import netsimInterfaceMsgs_pb2

class NetSimConnector:

    def __init__(self, serverAddress, portNumber):
        os.environ['http_proxy'] = ''
        self.serverAddress = serverAddress
        self.portNumber = portNumber
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)

    def connect (self): 
        self.socket.connect("tcp://" + self.serverAddress + ':' + str(self.portNumber))
    def sendMessage(self, message):
        self.socket.send(message)
    def receiveMessage(self):
        return self.socket.recv()
    def communicate(self):
        nodeList = []
        for request in [0,1,3,4]:
            
            print(f"Sending request simstep …")
            # coreSimRequest = netsimInterfaceMsgs_pb2.coreSimRequest()

            coreSimRequest = netsimInterfaceMsgs_pb2.ControllerRequest()
            coreSimRequest.messageType = request
            

            if request == 0:
                coreSimRequest.init.simTime = time.time()
                self.socket.send(coreSimRequest.SerializeToString())
                message = self.socket.recv()
                coreSimResponse = netsimInterfaceMsgs_pb2.ControllerResponse()
                coreSimResponse.ParseFromString(message)
                print(coreSimResponse)
            
            elif request == 1:

                coreSimRequest.create.numNodes = 2
                self.socket.send(coreSimRequest.SerializeToString())
                message = self.socket.recv()
                coreSimResponse = netsimInterfaceMsgs_pb2.ControllerResponse()
                coreSimResponse.ParseFromString(message)
                print(coreSimResponse)


            elif request == 2:
                
                coreSimRequest.update.nodeID = 1
                # nodeList.append(updateLocationRequest.nodeID)
                coreSimRequest.update.x =  100
                coreSimRequest.update.y =  100
                self.socket.send(coreSimRequest.SerializeToString())
                message = self.socket.recv()
                coreSimResponse = netsimInterfaceMsgs_pb2.ControllerResponse()
                coreSimResponse.ParseFromString(message)
                print(coreSimResponse)


            elif request == 3:

                # coreSimRequest.sche = netsimInterfaceMsgs_pb2.ScheduleTrafficRequest
                coreSimRequest.sche.srcNodeID = 1
                coreSimRequest.sche.dstNodeID = 0
                coreSimRequest.sche.pktCount = 241229
                coreSimRequest.sche.pktSize = 1200
                print('Sending message', coreSimRequest)
                self.socket.send(coreSimRequest.SerializeToString())
                message = self.socket.recv()
                coreSimResponse = netsimInterfaceMsgs_pb2.ControllerResponse()
                coreSimResponse.ParseFromString(message)
                print(coreSimResponse)

                
                coreSimRequest = netsimInterfaceMsgs_pb2.ControllerRequest()
                coreSimRequest.messageType = request
                coreSimRequest.sche.srcNodeID = 2
                coreSimRequest.sche.dstNodeID = 0
                coreSimRequest.sche.pktCount = 241229
                coreSimRequest.sche.pktSize = 1200
                print('Sending message', coreSimRequest)
                self.socket.send(coreSimRequest.SerializeToString())
                message = self.socket.recv()
                coreSimResponse = netsimInterfaceMsgs_pb2.ControllerResponse()
                coreSimResponse.ParseFromString(message)
                print(coreSimResponse)


            elif request == 4:

                # coreSimRequest.sim = netsimInterfaceMsgs_pb2.SimulateOneStepRequest
                self.socket.send(coreSimRequest.SerializeToString())
                message = self.socket.recv()
                coreSimResponse = netsimInterfaceMsgs_pb2.ControllerResponse()
                coreSimResponse.ParseFromString(message)
                print(coreSimResponse)

            else:

                print("Unknown request, continuing...")
                continue
            

def main():
    connector = NetSimConnector('127.0.0.1', '5555')
    connector.connect()
    connector.communicate()


if __name__ == "__main__":
    main()