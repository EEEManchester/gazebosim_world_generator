#!/usr/bin/env python

import rospy
from genEnvironment import Environment
from evolveEnvironment import Evolve
from gazebosim_world_generator.srv import Gen_Base_World,Gen_Base_WorldResponse 
from datetime import datetime
import os 
import json
from shutil import copyfile

"""
Todo

Remove hardcoding of variables

Currently radiation is output to yaml file for loading into the param server. 

This will move to add gazebo radiation sources to the world model once the radiation sources are wokring properly 

When the world evolves currently full stacks are added or removed this could be altered to just individual barrels 

Currently the radiation map does not change with evolutions of the map. This should be implemented

Add write config files to Environment

Copy rad files to folders too
"""


class ServiceCaller(object):

    def __init__(self):
        
        self._s = rospy.Service('generate_world', Gen_Base_World, self.handle_base_world)
        self._t = rospy.Service('evolve_world', Gen_Base_World, self.handle_modified_world)
        print "Ready to generate worlds"


    def handle_base_world(self,rec):

        if (rec.map_file == ""): 
            rec.map_file = None
        
        e = Environment(rec.config_file,input_map_name=rec.map_file)
        
        return True
        

    def handle_modified_world(self,rec):
        
        now = datetime.now().strftime("%Y_%m_%d_%H%M%S") 

        folder_name = "src/gazebosim_world_generator/worlds/evolved_" + now
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        if (rec.map_file == ""): 
            rec.map_file = None

        old_map_name = folder_name +"/old.tiff"
        radiation_name = folder_name +"/radiation.tiff"
        output_map_name = folder_name +"/map.tiff"
        world_name = folder_name +"/environment.world"
        config_name = folder_name +"/config.json"


        print rec.map_file
        v = Evolve(rec.config_file,input_map_name=rec.map_file,output_map_name = output_map_name)
        e = Environment(rec.config_file,input_map_name=v._output_map_name,out_file_name=world_name)
        
        old_map_src,old_rad_src = self.write_config(rec.config_file,config_name,output_map_name,world_name,rec.map_file)

        copyfile(old_map_src, old_map_name)


        #THIS WILL NEED CHANGING ONCE EVOLVING RADIATION IS IMPLEMENTED!!!
        copyfile(old_rad_src, radiation_name)


        return True

    def write_config(self,cf,config_name,output_map_name,world_name,input_map_name):
        with open(cf) as json_file:
            data = json.load(json_file)  

        data["output_map"] =  output_map_name
        data["output_filename"] =  world_name  

        if input_map_name:
            data["input_map"] =  input_map_name

        with open(config_name, 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)
        
        return data["input_map"],data["radiation_map"]


        
if __name__ == "__main__":
    rospy.init_node('gazebosim_world_generator')
    x = ServiceCaller()

    rospy.spin()