# Machine Learning for Wireless Networking Systems Simulator

> [!CAUTION]
> **PROJECT NOT UNDER ACTIVE MANAGEMENT**
> * This project will no longer be maintained by Intel.
> * Intel has ceased development and contributions including, but not limited to, maintenance, bug fixes, new releases, or updates, to this project.  
> * Intel no longer accepts patches to this project.  
> * If you have an ongoing need to use this project, are interested in independently developing it, or would like to maintain patches for the open source software community, please create your own fork of this project.

The `Machine Learning for Wireless Networking Systems Simulator` integrates Intel’s open-source tools (a) CARLA for modeling vehicular environments and autonomous driving, (b) Open Federated Learning for privacy preserving distributed machine learning, and (c) ns3 based wireless simulator. The tool allows for evaluation of machine learning optimizations across wireless as well as the application stack and can be used to evaluate the E2E performance with realistic datasets.


## Brief intro to the current Network Sim interface

Our current interface works with a **socket interface** connecting the `python` and `NS3`. The interface contains a `Wave Server` inside and this server will deal with all the traffics.

Currently our methods contains:

* Init Simulation: Where the interface will create a new server instance.

* Create Nodes(# Nodes): Where the server will create a given number of wifi devices centered all at (0.,0.) with no velocity. The server will give the list of created nodes and their types as a response.

* Update Location(ID, x, y): The server will give new locations to the given node. If the node doesn't exist, return an error.

* Schedule traffics(src, dst, pktsize, pktcount): This function will schedule a traffic between the given source and destination, the two nodes are now connected by socket.

* Run simulation(): Start the simulation with previously scheduled traffices. The server will collect transmitted and received packets from the sockets, store them in a map and send back to the controller.

Notice that the traffic collection happens when the socket connection sends or receives a packet, a transmission failure means that the sockets fails to receive a certain packet.

<!-- First Review - 10/31/2023 MRB -->
