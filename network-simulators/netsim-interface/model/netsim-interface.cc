/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */

#include "netsim-interface.h"
#include "wave_server.h"
#include <ns3/log.h>
#include <zmqpp/zmqpp.hpp>
#include "ns3/netsimInterfaceMsgs.pb.h"

#include "ns3/vector.h"
#include "ns3/string.h"
#include "ns3/socket.h"
#include "ns3/double.h"
#include "ns3/config.h"
#include "ns3/log.h"
#include "ns3/command-line.h"
#include "ns3/mobility-model.h"
#include "ns3/yans-wifi-helper.h"
#include "ns3/position-allocator.h"
#include "ns3/mobility-helper.h"
#include "ns3/internet-stack-helper.h"
#include "ns3/ipv4-address-helper.h"
#include "ns3/ipv4-interface-container.h"
#include <iostream>

#include "ns3/ocb-wifi-mac.h"
#include "ns3/wifi-80211p-helper.h"
#include "ns3/wave-mac-helper.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("NetSimInterface");
NS_OBJECT_ENSURE_REGISTERED (NetSimInterface);

TypeId NetSimInterface::GetTypeId() {
    static TypeId tid = TypeId ("NetSimInterface")
    .SetParent<Object> ()
    .SetGroupName ("NetSim")
    .AddConstructor<NetSimInterface> ()
    ;
    return tid; 
}

NetSimInterface::~NetSimInterface() {
    NS_LOG_FUNCTION(this);
}

NetSimInterface::NetSimInterface() {
    // uint32_t numClients = 10;
    // uint32_t maxPacketSize = 1200;
    // uint32_t modelSize = 500000;
    // uint16_t interval = 1;
    // Ptr<WaveServer> server;
    this->interfacePort = 5555;
    this->zmqSocket = new zmqpp::socket(this->zmqContext, zmqpp::socket_type::reply);

    std::string endpoint = "tcp://127.0.0.1:" + std::to_string(this->interfacePort);
    this->zmqSocket->bind(endpoint);
    WaveServer *server;
    while(true) {
        zmqpp::message message;
        this->zmqSocket->receive(message);
        std::string text;
        message >> text;
        netsimInterfaceMsgs::ControllerRequest coreSimRequest;
        coreSimRequest.ParseFromString(text);

        if(coreSimRequest.messagetype() == netsimInterfaceMsgs::MSG_INIT){ // Received info to initialize a server
            netsimInterfaceMsgs::InitSimulationRequest initSimulationRequest = coreSimRequest.init();
            
            //std::cout << "Initializing Simulator..." << std::endl;
            // // Ptr<WaveServer> client = m_factory.Create<WaveServer> ();
            server = new WaveServer();
            std::cout << "Netsim: Network simulation initialized!" << std::endl;

            netsimInterfaceMsgs::ControllerResponse coreSimResponse;
            coreSimResponse.set_messagetype(netsimInterfaceMsgs::MSG_INIT);
            coreSimResponse.mutable_initres()->set_status(1);
            coreSimResponse.mutable_initres()->set_description("Nodes initialized!");

            std::string messageToSend;
            coreSimResponse.SerializeToString(&messageToSend);
            this->zmqSocket->send(messageToSend);

        }else if(coreSimRequest.messagetype() == netsimInterfaceMsgs::MSG_CRENODE){
            netsimInterfaceMsgs::CreateNodeRequest createNodeRequest = coreSimRequest.create();

            uint16_t m_nodenum = createNodeRequest.numnodes();
            //std::cout << "Received request to create " << createNodeRequest.numnodes() << " new nodes, creating..." << std::endl;
            std::map<uint32_t, std::string> nodeIDs = server->GenerateNodes(m_nodenum);
            std::cout << "Netsim: Nodes created! " << (m_nodenum + 1) << std::endl;
            /*for (auto const& x : nodeIDs)
            {
                std::cout << x.first  // string (key)
                        << ':' 
                        << x.second // string's value 
                        << std::endl;
            }*/

            netsimInterfaceMsgs::ControllerResponse coreSimResponse;
            coreSimResponse.set_messagetype(netsimInterfaceMsgs::MSG_CRENODE);
            coreSimResponse.mutable_createres()->set_status(1);
            coreSimResponse.mutable_createres()->set_description("Nodes created!");
            for(std::map<uint32_t, std::string>::iterator it = nodeIDs.begin(); it != nodeIDs.end(); it++)
            {
                (*coreSimResponse.mutable_createres()->mutable_nodeids())[it->first] = it->second;
            }
            
            std::string messageToSend;
            coreSimResponse.SerializeToString(&messageToSend);
            this->zmqSocket->send(messageToSend);

        }else if(coreSimRequest.messagetype() == netsimInterfaceMsgs::MSG_MODPOS){
            netsimInterfaceMsgs::UpdateLocationRequest updateLocationRequest = coreSimRequest.update();
            netsimInterfaceMsgs::ControllerResponse coreSimResponse;
            
            uint16_t m_nodeid = updateLocationRequest.nodeid();
            if(m_nodeid > server->GetEnvoyNum()){
                std::cout << "This node not in the server, ignoring..." << std::endl;
                coreSimResponse.set_messagetype(netsimInterfaceMsgs::MSG_MODPOS);
                coreSimResponse.mutable_updateres()->set_status(0);
                coreSimResponse.mutable_updateres()->set_description("Unknown Envoy!");
                std::string messageToSend;
                coreSimResponse.SerializeToString(&messageToSend);
                this->zmqSocket->send(messageToSend);
                continue;
            }
            float x_new = updateLocationRequest.x();
            float y_new = updateLocationRequest.y();
            Vector oldPos = server->GetPosition(m_nodeid);
            //std::cout << "Client position before update : ("<< oldPos.x << "," << oldPos.y << ")" << std::endl;
            server->SetPosition(m_nodeid, x_new, y_new);
            Vector newPos = server->GetPosition(m_nodeid);
            std::cout << "Netsim: Node ID" << m_nodeid << " position updated to : ("<< newPos.x << "," << newPos.y << ")" << std::endl;
            
            coreSimResponse.set_messagetype(netsimInterfaceMsgs::MSG_MODPOS);
            coreSimResponse.mutable_updateres()->set_status(1);
            coreSimResponse.mutable_updateres()->set_description("Nodes position updated!");
            std::string messageToSend;
            coreSimResponse.SerializeToString(&messageToSend);
            this->zmqSocket->send(messageToSend);
        }
        else if(coreSimRequest.messagetype() == netsimInterfaceMsgs::MSG_SCHTRF){
            netsimInterfaceMsgs::ScheduleTrafficRequest scheduleTrafficRequest = coreSimRequest.sche();
            
            uint32_t m_srcnodeid = scheduleTrafficRequest.srcnodeid();
            uint32_t m_dstnodeid = scheduleTrafficRequest.dstnodeid();
            uint32_t m_pktcount = scheduleTrafficRequest.pktcount();
            uint32_t m_pktsize = scheduleTrafficRequest.pktsize();
            
            server->ScheduleTraffic(m_srcnodeid, m_dstnodeid, m_pktsize, m_pktcount, Seconds (1));
            std::cout << "Netsim: Scheduled traffic between :"<< m_srcnodeid << " and " << m_dstnodeid << " num of packets = " << m_pktcount << std::endl;
            netsimInterfaceMsgs::ControllerResponse coreSimResponse;
            coreSimResponse.set_messagetype(netsimInterfaceMsgs::MSG_SCHTRF);
            coreSimResponse.mutable_scheres()->set_status(1);
            coreSimResponse.mutable_scheres()->set_description("Msg scheduled!");
            std::string messageToSend;
            coreSimResponse.SerializeToString(&messageToSend);
            this->zmqSocket->send(messageToSend);
        }
        else if(coreSimRequest.messagetype() == netsimInterfaceMsgs::MSG_RUNSIM){
            netsimInterfaceMsgs::SimulateOneStepRequest simulateOneStepRequest = coreSimRequest.sim();
            
            std::cout << "Netsim: Running packet simulation for the current round ..."<<std::endl;
            trafficInfo info =  server->SimulateOneStep();
            std::cout << "Netsim: Completed simulation for the current round! "<< std::endl;
            netsimInterfaceMsgs::ControllerResponse coreSimResponse;
            coreSimResponse.set_messagetype(netsimInterfaceMsgs::MSG_RUNSIM);
            coreSimResponse.mutable_simres()->set_status(1);
            
            std::list<int32_t> txIdList;
            std::list<int32_t> rxIdList;
            std::list<int32_t> txPktCountList;
            std::list<int32_t> rxPktCountList;

            for (auto &itr : info.pairwiseTxPktCountMap) {
                if (info.pairwiseRxPktCountMap.find(itr.first) != info.pairwiseRxPktCountMap.end()){
                    //std::cout << "Sender ID " << itr.first.first
                    //        << " Receiver ID " << itr.first.second
                    //        << " Transmitted packets " << itr.second
                    //        << " Rcvd packets " << info.pairwiseRxPktCountMap[itr.first] << std::endl;
                    coreSimResponse.mutable_simres()->mutable_txidlist()->Add(itr.first.first);
                    coreSimResponse.mutable_simres()->mutable_rxidlist()->Add(itr.first.second);
                    coreSimResponse.mutable_simres()->mutable_txpktcountlist()->Add(itr.second);
                    coreSimResponse.mutable_simres()->mutable_rxpktcountlist()->Add(info.pairwiseRxPktCountMap[itr.first]);
        
                }
            }           
            
            std::string messageToSend;
            coreSimResponse.SerializeToString(&messageToSend);
            this->zmqSocket->send(messageToSend);
            server->resetStatistics();
        }
        else{
            std::cout << "Unknown request, may add to the system later" << std::endl;
            break;
        }
        
    }
}
