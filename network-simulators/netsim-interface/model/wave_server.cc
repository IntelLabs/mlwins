/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2005,2006,2007 INRIA
 * Copyright (c) 2013 Dalian University of Technology
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 *
 */
/**
 * This example shows basic construction of an 802.11p node.  Two nodes
 * are constructed with 802.11p devices, and by default, one node sends a single
 * packet to another node (the number of packets and interval between
 * them can be configured by command-line arguments).  The example shows
 * typical usage of the helper classes for this mode of WiFi (where "OCB" refers
 * to "Outside the Context of a BSS")."
 */

#include "ns3/vector.h"
#include "ns3/string.h"
#include "ns3/socket.h"
#include "ns3/double.h"
#include "ns3/config.h"
#include "ns3/object.h"
#include "ns3/log.h"
#include "ns3/command-line.h"
#include "ns3/mobility-model.h"
#include "ns3/yans-wifi-helper.h"
#include "ns3/position-allocator.h"
#include "ns3/mobility-helper.h"
#include "ns3/internet-stack-helper.h"
#include "ns3/ipv4-address-helper.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/ipv4-interface-container.h"
#include <iostream>

#include "ns3/ocb-wifi-mac.h"
#include "ns3/wifi-80211p-helper.h"
#include "ns3/wave-mac-helper.h"
#include "wave_server.h"

/*
 * In WAVE module, there is no net device class named like "Wifi80211pNetDevice",
 * instead, we need to use Wifi80211pHelper to create an object of
 * WifiNetDevice class.
 *
 * usage:
 *  NodeContainer nodes;
 *  NetDeviceContainer devices;
 *  nodes.Create (2);
 *  YansWifiPhyHelper wifiPhy;
 *  YansWifiChannelHelper wifiChannel = YansWifiChannelHelper::Default ();
 *  wifiPhy.SetChannel (wifiChannel.Create ());
 *  NqosWaveMacHelper wifi80211pMac = NqosWave80211pMacHelper::Default();
 *  Wifi80211pHelper wifi80211p = Wifi80211pHelper::Default ();
 *  devices = wifi80211p.Install (wifiPhy, wifi80211pMac, nodes);
 *
 * The reason of not providing a 802.11p class is that most of modeling
 * 802.11p standard has been done in wifi module, so we only need a high
 * MAC class that enables OCB mode.
 */

namespace ns3{ 

NS_LOG_COMPONENT_DEFINE ("WaveServer");


trafficInfo m_info;


TypeId WaveServer::GetTypeId() {
    static TypeId tid = TypeId ("WaveServer")
    .SetParent<Object> ()
    .SetGroupName ("NetSim")
    .AddConstructor<WaveServer> ()
    ;
    return tid; 
}

WaveServer::WaveServer()
{
    m_numClients = 1;
    m_maxPacketSize = 1200;
    m_modelSize = 50000;
    m_interval = 1;
  

}

WaveServer::~WaveServer()
{
    NS_LOG_FUNCTION (this);
}

void
WaveServer::SetPosition(uint16_t nodeID, double x, double y){
    Ptr <MobilityModel> mobility = m_nodes.Get(nodeID)->GetObject<MobilityModel>();
    mobility->SetPosition(Vector(x,y,0.0));
}

Vector
WaveServer::GetPosition(uint16_t nodeID){
    Ptr <MobilityModel> mobility = m_nodes.Get(nodeID)->GetObject<MobilityModel>();
    
    return mobility->GetPosition();
}

uint32_t
WaveServer::GetEnvoyNum(){
    return m_nodes.GetN();
}

void WaveServer::ReceivePacket (Ptr<Socket> socket)
{

  Ptr <Packet> packet;
  Address senderAddr;
  while (packet = socket->RecvFrom (senderAddr))
    {
      Ptr<Node> rxNode = socket->GetNode ();
      Ptr<Node> txNode = nullptr;
      if (InetSocketAddress::IsMatchingType (senderAddr)){
          InetSocketAddress addr = InetSocketAddress::ConvertFrom (senderAddr);
          int nodes = ipv4InterfaceContainer.GetN ();
          for (int i = 0; i < nodes; i++){
              if (addr.GetIpv4 () == ipv4InterfaceContainer.GetAddress (i) ){
                  txNode = m_nodes.Get(i);
                  break;
                }
            }
        }
      // std::cout << "Received one packet!" << packet->GetSize() << std::endl;
      uint32_t rxbytes = packet->GetSize();
      if(rxbytes > 0){
        m_info.m_rxPktCountsList[rxNode->GetId()] += 1;
        m_info.m_rxThroughputList[rxNode->GetId()] += rxbytes;
        if (txNode != nullptr){
          //std::cout << "Received one packet! " << packet->GetSize() << std::endl;
          m_info.pairwiseRxPktCountMap[std::pair(txNode->GetId(), rxNode->GetId())] += 1;
        }
      } 
    }
}

static void GenerateTraffic (Ptr<Socket> socket, uint32_t pktSize,
                             uint32_t pktCount, Time pktInterval, uint32_t dstNode)
{
  if (pktCount > 0)
    {
      uint32_t bytesSent = socket->Send (Create<Packet> (pktSize));
      if(bytesSent > 0){
        m_info.m_txThroughputList[socket->GetNode ()->GetId ()] += bytesSent;
        m_info.m_txPktCountsList[socket->GetNode ()->GetId ()] += 1;
        m_info.pairwiseTxPktCountMap[std::pair(socket->GetNode ()->GetId (), dstNode)] += 1;
      }
      else{
        return;
      }
      
      Simulator::Schedule (pktInterval, &GenerateTraffic,
                           socket, pktSize,pktCount - 1, pktInterval, dstNode);
    }
  else
    {
      socket->Close ();
    }
}



void
WaveServer::ScheduleTraffic(uint16_t srcNode, uint16_t dstNode, uint32_t pktSize,
                            uint32_t pktCount, Time pktInterval)
{
    TypeId tid = TypeId::LookupByName ("ns3::UdpSocketFactory");
    Ptr<Socket> recvSink = Socket::CreateSocket (m_nodes.Get (dstNode), tid);
    InetSocketAddress local = InetSocketAddress (Ipv4Address::GetAny (), 80);
    recvSink->Bind (local);
    recvSink->SetRecvCallback (MakeCallback (&WaveServer::ReceivePacket, this));

    Ptr<Socket> source = Socket::CreateSocket (m_nodes.Get (srcNode), tid);
    InetSocketAddress remote = InetSocketAddress (Ipv4Address ("255.255.255.255"), 80);
    source->SetAllowBroadcast (true);
    source->Connect (remote);

    Simulator::ScheduleWithContext (source->GetNode ()->GetId (),
                                  Seconds ((float) rand()/RAND_MAX), &GenerateTraffic,
                                  source, pktSize, pktCount, pktInterval, dstNode); 


    // Simulator::Stop (Seconds (2+0.001));
    
    

    // Ptr<FlowMonitor> monitor;

    // FlowMonitorHelper flowmon;
  
    // monitor = flowmon.InstallAll ();

    // monitor->CheckForLostPackets ();
    // std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats ();

    // monitor->SerializeToXmlFile("test_flow_in.xml", true, true);
    // Simulator::Destroy();
    // Simulator::Run();

    
                             
}

std::map<uint32_t, std::string>
WaveServer::GenerateNodes(uint16_t NodeNums)
{
    m_nodes.Create(NodeNums + 1);
    m_nodesIDs[0] = "Director";
    for(int i = 1; i < NodeNums + 1; i++){
      m_nodesIDs[i] = "Envoy"; 
    }
    m_numClients = NodeNums;
    std::string phyMode ("OfdmRate6MbpsBW10MHz");
    YansWifiPhyHelper wifiPhy;
    YansWifiChannelHelper wifiChannel = YansWifiChannelHelper::Default ();
    Ptr<YansWifiChannel> channel = wifiChannel.Create ();
    wifiPhy.SetChannel (channel);
    // ns-3 supports generate a pcap trace
    wifiPhy.SetPcapDataLinkType (WifiPhyHelper::DLT_IEEE802_11);
    NqosWaveMacHelper wifi80211pMac = NqosWaveMacHelper::Default ();
    Wifi80211pHelper wifi80211p = Wifi80211pHelper::Default ();
    wifi80211p.SetRemoteStationManager ("ns3::ConstantRateWifiManager",
                                      "DataMode",StringValue (phyMode),
                                      "ControlMode",StringValue (phyMode));
    m_devices = wifi80211p.Install (wifiPhy, wifi80211pMac, m_nodes);
    wifiPhy.EnablePcap ("wave-simple-80211p", m_devices);
    MobilityHelper mobility;
    Ptr<ListPositionAllocator> positionAlloc = CreateObject<ListPositionAllocator> ();
    for(int i = 0; i < NodeNums+1; i++){
        positionAlloc->Add (Vector (0.0, 0.0, 0.0));
    }
    mobility.SetPositionAllocator (positionAlloc);
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (m_nodes);
    InternetStackHelper internet;
    internet.Install (m_nodes);

    Ipv4AddressHelper ipv4;
    NS_LOG_INFO ("Assign IP Addresses.");
    ipv4.SetBase ("10.1.1.0", "255.255.255.0");
    ipv4InterfaceContainer = ipv4.Assign (m_devices);

    return m_nodesIDs;

}

trafficInfo
WaveServer::SimulateOneStep()
{
    

    // Simulator::Stop (Seconds (1+0.001));
    Simulator::Run();

    for(uint32_t itr = 0; itr < m_nodes.GetN(); ++itr){
      std::cout << "Netsim: Stats for the current round for Node ID: " << itr << " TX Packets: " << 
        m_info.m_txPktCountsList.find(itr)->second << " RX Packets: " << 
        m_info.m_rxPktCountsList.find(itr)->second << std::endl;
      //std::cout << "TX Throughput: " << m_info.m_txThroughputList.find(itr)->second << std::endl;
      //std::cout << "RX Throughput: " << m_info.m_rxThroughputList.find(itr)->second << std::endl;
    }

    //Simulator::Destroy();

    return m_info;

}

void WaveServer::resetStatistics(){
  m_info.m_txPktCountsList.clear();
  m_info.m_rxPktCountsList.clear();
  m_info.m_txThroughputList.clear();
  m_info.m_rxThroughputList.clear();
  m_info.pairwiseTxPktCountMap.clear();
  m_info.pairwiseRxPktCountMap.clear();
}

}

