/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
#ifndef WAVE_SERVER_H
#define WAVE_SERVER_H

#include "ns3/vector.h"
#include "ns3/string.h"
#include "ns3/socket.h"
#include "ns3/object.h"
#include "ns3/double.h"
#include "ns3/config.h"
#include "ns3/log.h"
#include "ns3/command-line.h"
#include "ns3/mobility-model.h"
#include "ns3/yans-wifi-helper.h"
#include "ns3/position-allocator.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/mobility-helper.h"
#include "ns3/internet-stack-helper.h"
#include "ns3/ipv4-address-helper.h"
#include "ns3/ipv4-interface-container.h"
#include <iostream>

#include "ns3/ocb-wifi-mac.h"
#include "ns3/wifi-80211p-helper.h"
#include "ns3/wave-mac-helper.h"

namespace ns3 {

    struct trafficInfo
    {
    std::map<uint16_t, int> m_rxPktCountsList;
    std::map<uint16_t, int> m_txPktCountsList;
    std::map<uint16_t, int> m_rxThroughputList;
    std::map<uint16_t, int> m_txThroughputList;
    std::map<std::pair<int, int>, int> pairwiseTxPktCountMap;
    std::map<std::pair<int, int>, int> pairwiseRxPktCountMap;
    };


    class WaveServer: public Object{
        public:

        static TypeId GetTypeId(void);
        WaveServer();
        virtual ~WaveServer ();

        void SetPosition(uint16_t nodeID, double x, double y);
        Vector GetPosition(uint16_t nodeID);
        void ReceivePacket (Ptr<Socket> socket);
        uint32_t GetEnvoyNum();

        void ScheduleTraffic(uint16_t srcNode, uint16_t dstNode, uint32_t pktSize,
                            uint32_t pktCount, Time pktInterval);

        std::map<uint32_t, std::string> GenerateNodes(uint16_t NodeNums);

        trafficInfo SimulateOneStep();
        
        void resetStatistics();

        private:

        NodeContainer m_nodes;
        NetDeviceContainer m_devices;
        std::map <uint32_t, std::string> m_nodesIDs;
        Ipv4InterfaceContainer ipv4InterfaceContainer;
        
        uint32_t m_numClients;
        uint32_t m_maxPacketSize;
        double m_modelSize;
        uint16_t m_interval;
        
        
    };
}

#endif /* WAVE_SERVER_H */