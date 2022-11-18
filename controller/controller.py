import os
import time
import yaml
from google.protobuf.any_pb2 import Any
from physicsSimConnector import CarlaConnector
from mlSimConnector  import MlSimConnector
from netSimConnector import NetSimConnector
import netsimInterfaceMsgs_pb2
import mlsimInterfaceMsgs_pb2
import random

class MlWinsController:
    NETSIM_MAX_PKT_SIZE = 1200
    def __init__(self, configFile):
        os.environ['http_proxy'] = ''
        configuration = None
        self.mlSimConnectors = {}
        self.netSimConnector = None
        with open(configFile, 'r') as file:
            configuration = yaml.safe_load(file)
        if configuration:
            self.numOfRounds = configuration['controller']['number_of_rounds']
            self.numOfCollaborators = configuration['mlSimulator']['num_of_collaborators']
            self.numOfAggregators = configuration['mlSimulator']['num_of_aggregators']
            self.numOfTicksPerRound = int(configuration['physicsSimulator']['number_of_ticks_per_round'])
            self.physicsSimConnector = CarlaConnector(configuration['physicsSimulator']['ip_address'], configuration['physicsSimulator']['port_number'])
            self.physicsSimConnector.initialize(configuration['physicsSimulator']['town_map'])
            
            for i in range(1, int(self.numOfCollaborators)+1):
                mlSimConnector = MlSimConnector(configuration['mlSimulator']['collaborator'+str(i)]['ip_address'], configuration['mlSimulator']['collaborator'+str(i)]['port_number'])
                mlSimConnector.connect()
                self.mlSimConnectors['collaborator'+str(i)] = mlSimConnector
            self.netSimConnector = NetSimConnector(configuration['netSimulator']['ip_address'], configuration['netSimulator']['port_number'])
            self.netSimConnector.connect()

            

    
    def control(self):
        randomFailureEvent = {}
        tempList = [1, 2, 3]
        for i in range(0, self.numOfRounds):
            randomFailureEvent[i] = random.sample(tempList, 1)
        
        # Initialize netsim
        coreSimRequest = netsimInterfaceMsgs_pb2.ControllerRequest()
        coreSimRequest.messageType = netsimInterfaceMsgs_pb2.MSG_INIT
        coreSimRequest.init.simTime = time.time() * 1000
        self.netSimConnector.sendMessage(coreSimRequest.SerializeToString())
        print ('Controller --> Netsim:', 'Sent initialization command')

        message = self.netSimConnector.receiveMessage()
        coreSimResponse = netsimInterfaceMsgs_pb2.ControllerResponse()
        coreSimResponse.ParseFromString(message)
        print ('Controller <-- Netsim:', 'Initialization Successful!')
        #print('Receive a message ', coreSimResponse.messageType, coreSimResponse.initRes.status, coreSimResponse.initRes.description)

        # Create nodes on netsim
        coreSimRequest = netsimInterfaceMsgs_pb2.ControllerRequest()
        coreSimRequest.messageType = netsimInterfaceMsgs_pb2.MSG_CRENODE
        coreSimRequest.create.numNodes = self.numOfCollaborators
        self.netSimConnector.sendMessage(coreSimRequest.SerializeToString())
        print ('Controller --> Netsim:', 'Instantiate nodes. Num of aggregators = ', self.numOfAggregators, 'Num of collaborators = ', self.numOfCollaborators)

        message = self.netSimConnector.receiveMessage()
        coreSimResponse = netsimInterfaceMsgs_pb2.ControllerResponse()
        coreSimResponse.ParseFromString(message)
        assert(coreSimResponse.messageType == netsimInterfaceMsgs_pb2.MSG_CRENODE)
        assert(coreSimResponse.HasField('createRes'))

        netsimCollaboratorIds = []
        netsimAggregatorIds = []
        if coreSimResponse.createRes.status == 1:
            print ('Controller <-- Netsim:', 'Node creation is successful!')
            for k in coreSimResponse.createRes.nodeIDs:
                v = coreSimResponse.createRes.nodeIDs[k]
                #print ('Created node id and type', k, v)
                if v == 'Envoy':
                    netsimCollaboratorIds.append(k)
                elif v == 'Director':
                    netsimAggregatorIds.append(k)
                else: print('Unexpected node type is created', k, v)

        #print(netsimCollaboratorIds, netsimAggregatorIds)

        # Initialize openfl
        collaboratorNames = {}
        collaboratorNameToNetsimIdMap = {}
        netsimIdToCollaboratorNameMap = {}
        collaboratorNameToPhysicsSimIdMap = {}
        index = 0
        for id in self.mlSimConnectors:
            mlsimInterfaceMsg = mlsimInterfaceMsgs_pb2.MlSimInterfaceMessage()
            mlsimInterfaceMsg.messageType = mlsimInterfaceMsgs_pb2.CMD_INIT_REQ
            mlsimInterfaceMsg.initRequest.description = "Initialization"
            self.mlSimConnectors[id].sendMessage(mlsimInterfaceMsg.SerializeToString())
            print ('Controller --> openFL:', 'Sent initialization command for collaborator', index+1)

            receivedMsg = self.mlSimConnectors[id].receiveMessage()
            mlsimInterfaceMsg = mlsimInterfaceMsgs_pb2.MlSimInterfaceMessage()
            mlsimInterfaceMsg.ParseFromString(receivedMsg)
            clientName = ''
            assert(mlsimInterfaceMsg.messageType == mlsimInterfaceMsgs_pb2.CMD_INIT_RSP)
            assert mlsimInterfaceMsg.HasField('initResponse')
            collaboratorNames[id] = mlsimInterfaceMsg.initResponse.clientName
            collaboratorNameToPhysicsSimIdMap[collaboratorNames[id]] = mlsimInterfaceMsg.initResponse.mobileNodeId
            print ('Controller <-- openFL:', 'Initialization successful for collaborator', index+1, 'name:', collaboratorNames[id])
            collaboratorNameToNetsimIdMap[collaboratorNames[id]] = netsimCollaboratorIds[index]
            netsimIdToCollaboratorNameMap[netsimCollaboratorIds[index]] = collaboratorNames[id]
            index = index + 1
        self.physicsSimConnector.tick()
        
        # Update location of aggregator on NetSim
        coreSimRequest = netsimInterfaceMsgs_pb2.ControllerRequest()
        coreSimRequest.messageType = netsimInterfaceMsgs_pb2.MSG_MODPOS
        coreSimRequest.update.nodeID = netsimAggregatorIds[0]
        coreSimRequest.update.x =  -50
        coreSimRequest.update.y =  -40
        self.netSimConnector.sendMessage(coreSimRequest.SerializeToString())
        message = self.netSimConnector.receiveMessage()
        coreSimResponse = netsimInterfaceMsgs_pb2.ControllerResponse()
        coreSimResponse.ParseFromString(message)
        #print(coreSimResponse)

        #for m in collaboratorNameToPhysicsSimIdMap:
        #    print('collaborator --> Node Id', m, collaboratorNameToPhysicsSimIdMap[m])
        #    print ('location', self.physicsSimConnector.getCurrentLocation(collaboratorNameToPhysicsSimIdMap[m]))
        
        for round in range (0, self.numOfRounds):
            for i in range(0, self.numOfTicksPerRound)   :
                self.physicsSimConnector.tick()
            # Send sim step request
            print ('Controller --> openFL:', 'Launch tasks for round', round)
            for id in self.mlSimConnectors:   
                mlsimInterfaceMsg = mlsimInterfaceMsgs_pb2.MlSimInterfaceMessage()
                mlsimInterfaceMsg.messageType = mlsimInterfaceMsgs_pb2.CMD_SIM_STEP_REQ
            
                mlsimInterfaceMsg.simStepRequest.simTime = time.time() * 1000
                mlsimInterfaceMsg.simStepRequest.round = round
                mlsimInterfaceMsg.simStepRequest.clientName = collaboratorNames[id]
                self.mlSimConnectors[id].sendMessage(mlsimInterfaceMsg.SerializeToString())
           
            for m in collaboratorNameToPhysicsSimIdMap: 
                # Update location on NetSim
                coreSimRequest = netsimInterfaceMsgs_pb2.ControllerRequest()
                coreSimRequest.messageType = netsimInterfaceMsgs_pb2.MSG_MODPOS
                coreSimRequest.update.nodeID = collaboratorNameToNetsimIdMap[m]
                print('Controller --> Carla', '(Round:', round, '):', 'Get current location for collaborator', m)
                location = self.physicsSimConnector.getCurrentLocation(collaboratorNameToPhysicsSimIdMap[m])
                coreSimRequest.update.x =  location.x
                coreSimRequest.update.y =  location.y
                self.netSimConnector.sendMessage(coreSimRequest.SerializeToString())
                print('Controller --> netsim', '(Round:', round, '):', 'Update current location for collaborator', m, 'to', location)
                message = self.netSimConnector.receiveMessage()
                coreSimResponse = netsimInterfaceMsgs_pb2.ControllerResponse()
                coreSimResponse.ParseFromString(message)
                #print(coreSimResponse)
                
            while True:
                # Receive msg
                rcvdSimStepResponses = {}
                messageStatus = {}
                for id in self.mlSimConnectors:
                    receivedMsg = self.mlSimConnectors[id].receiveMessage()
                    mlsimInterfaceMsg = mlsimInterfaceMsgs_pb2.MlSimInterfaceMessage()
                    mlsimInterfaceMsg.ParseFromString(receivedMsg)
                    if mlsimInterfaceMsg.messageType == mlsimInterfaceMsgs_pb2.CMD_MSG_TX_REQ:
                        assert mlsimInterfaceMsg.HasField('msgTxRequest')
                        print('Controller <-- openFL', '(Round:', round, '):', 'Request to perform RPC call from collaborator', mlsimInterfaceMsg.msgTxRequest.clientName,
                                'with message size', mlsimInterfaceMsg.msgTxRequest.messageSize, 'bytes')
                        
                        # Schedule msg TX on netsim
                        coreSimRequest = netsimInterfaceMsgs_pb2.ControllerRequest()
                        coreSimRequest.messageType = netsimInterfaceMsgs_pb2.MSG_SCHTRF
                        coreSimRequest.sche.srcNodeID = collaboratorNameToNetsimIdMap[mlsimInterfaceMsg.msgTxRequest.clientName]
                        coreSimRequest.sche.dstNodeID = netsimAggregatorIds[0]
                        coreSimRequest.sche.pktSize = min(MlWinsController.NETSIM_MAX_PKT_SIZE, mlsimInterfaceMsg.msgTxRequest.messageSize)
                        coreSimRequest.sche.pktCount = int(mlsimInterfaceMsg.msgTxRequest.messageSize/coreSimRequest.sche.pktSize)
                        print ('Controller --> netsim', '(Round:', round, '):','Sending scheduling request for',  
                            mlsimInterfaceMsg.msgTxRequest.clientName, 'Number of packets = ', coreSimRequest.sche.pktCount)
                        messageStatus[mlsimInterfaceMsg.msgTxRequest.clientName] = 0
                        self.netSimConnector.sendMessage(coreSimRequest.SerializeToString())
                        # Receive msg TX response from netsim
                        message = self.netSimConnector.receiveMessage()
                        coreSimResponse = netsimInterfaceMsgs_pb2.ControllerResponse()
                        coreSimResponse.ParseFromString(message)
                        #print(coreSimResponse)

                    elif mlsimInterfaceMsg.messageType == mlsimInterfaceMsgs_pb2.CMD_SIM_STEP_RSP:
                        assert mlsimInterfaceMsg.HasField('simStepResponse')
                        rcvdSimStepResponses[mlsimInterfaceMsg.simStepResponse.clientName] = 1
                        print('Controller --> netsim', '(Round:', round, '):','Received round completion message from', mlsimInterfaceMsg.simStepResponse.clientName)
                    else:
                        print('Unexpected Message Type! Aborting simulation ...', mlsimInterfaceMsg.messageType)
                        return
                
                if len(rcvdSimStepResponses) == self.numOfCollaborators:
                    break  
                # Send request to netsim to run simulation
                coreSimRequest = netsimInterfaceMsgs_pb2.ControllerRequest()
                coreSimRequest.messageType = netsimInterfaceMsgs_pb2.MSG_RUNSIM
                self.netSimConnector.sendMessage(coreSimRequest.SerializeToString())
                
                # Receive response for simulation run from netsim
                message = self.netSimConnector.receiveMessage()
                coreSimResponse = netsimInterfaceMsgs_pb2.ControllerResponse()
                coreSimResponse.ParseFromString(message)
                #print(coreSimResponse)
                assert coreSimResponse.HasField('simRes')
                
                for responseIndex in range (0, len(coreSimResponse.simRes.txIdList)):
                    messageStatus[netsimIdToCollaboratorNameMap[coreSimResponse.simRes.txIdList[responseIndex]]] = (coreSimResponse.simRes.txPktCountList[responseIndex] == coreSimResponse.simRes.rxPktCountList[responseIndex])
                    print ('Controller <-- netsim', '(Round:', round, '):','Rcvd RPC call status for', 
                        netsimIdToCollaboratorNameMap[coreSimResponse.simRes.txIdList[responseIndex]], 
                        'status', (coreSimResponse.simRes.txPktCountList[responseIndex] == coreSimResponse.simRes.rxPktCountList[responseIndex]))

                for id in self.mlSimConnectors:
                    
                    # Send msg TX response
                    mlsimInterfaceMsg = mlsimInterfaceMsgs_pb2.MlSimInterfaceMessage()
                    mlsimInterfaceMsg.messageType = mlsimInterfaceMsgs_pb2.CMD_MSG_TX_RSP
                
                    mlsimInterfaceMsg.msgTxResponse.simTime = time.time() * 1000
                    
                    # Synthetic failure model
                    #collabNumber = int(collaboratorNames[id].split('_')[1])
                    #if collabNumber in randomFailureEvent[round]:
                    #    mlsimInterfaceMsg.msgTxResponse.status = 0
                    #    print('Sending packet failure event for', round, collaboratorNames[id])
                    #else: mlsimInterfaceMsg.msgTxResponse.status = 1
                    
                    mlsimInterfaceMsg.msgTxResponse.status = messageStatus[collaboratorNames[id]]
                    mlsimInterfaceMsg.msgTxResponse.clientName = collaboratorNames[id]
                    self.mlSimConnectors[id].sendMessage(mlsimInterfaceMsg.SerializeToString())
                    #print('Sent msg status for', mlsimInterfaceMsg.msgTxResponse.clientName, 'status', mlsimInterfaceMsg.msgTxResponse.status)

            time.sleep(1)
            
        
def main():
    mlwinsController = MlWinsController(os.path.join(os.path.dirname(__file__), 'mlwinsSimConfig.yaml')) 
    mlwinsController.control()


if __name__ == "__main__":
    main()