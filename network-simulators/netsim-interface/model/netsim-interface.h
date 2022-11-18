/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
#ifndef NETSIM_INTERFACE_H
#define NETSIM_INTERFACE_H

#include "ns3/object.h"
#include "ns3/object-factory.h"
#include <zmqpp/zmqpp.hpp>
#include "wave_server.h"

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

namespace ns3 {

    class NetSimInterface: public Object {
        public:
            static TypeId GetTypeId(void);

            NetSimInterface();
            virtual ~NetSimInterface();
        private:
            uint32_t interfacePort;
            zmqpp::context zmqContext;
            zmqpp::socket *zmqSocket;
            ObjectFactory m_factory;
            // Ptr<WaveServer> server;
    };

}

#endif /* NETSIM_INTERFACE_H */

