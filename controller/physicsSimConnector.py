#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import glob
import os
import sys

try:
    #sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
    #    sys.version_info.major,
    #    sys.version_info.minor,
    #    'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
    sys.path.append(glob.glob(os.path.join(os.path.dirname(__file__), '../physics-simulators/carla/carla-0.9.11-py3.7-linux-x86_64.egg'))[0])
except IndexError:
    print('File not found!')

import carla

import random
import time

import argparse

import math
import queue
import numpy as np
import cv2

class CarlaConnector:
    def __init__(self, ipAddress, portNumber):
        self.ipAddress = ipAddress
        self.portNumber = portNumber
        
    def initialize(self, townMap=None):  
        # First of all, we need to create the client that will send the requests
        # to the simulator. Here we'll assume the simulator is accepting
        # requests in the localhost at port 2000.
        client = carla.Client(self.ipAddress, self.portNumber)
        client.set_timeout(10.0)


        traffic_manager = client.get_trafficmanager(8001)
        traffic_manager.set_random_device_seed(1)
        
        self.world = client.load_world(townMap)    
        settings = self.world.get_settings()
        settings.synchronous_mode = True # Enables synchronous mode
        
        traffic_manager.set_synchronous_mode(True)
        settings.fixed_delta_seconds = 0.05
        self.world.apply_settings(settings)

        actor_list = self.world.get_actors()
        print('destroying current actors')
        client.apply_batch([carla.command.DestroyActor(x) for x in actor_list])
        print('done.')

    def showListOfActors(self):
        actorList = self.world.get_actors()
        print(actorList)
        #actor = actor_list.find(id)
    def getCurrentLocation(self, id):
        actorList = self.world.get_actors()
        actor = actorList.find(int(id))
        assert(actor != None)
        print(actor.id, actor.get_location())
        return actor.get_location()
    def tick(self):
        self.world.tick()

def main():
    connector = CarlaConnector('127.0.0.1', '2000')
    connector.initialize()


if __name__ == '__main__':

    main()
