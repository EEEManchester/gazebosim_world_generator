#!/usr/bin/env python

import numpy as np
import random
import cv2
import json
import random
import os

"""
Evolve loads in the target environment image alters it and regenerates the world to allow for 


Evolve is currently limited to worlds where no objects are bigger than the metres per pixel value, due to collisions when adding in the new items
i.e. if metres_per_pixel = 1.0 objects must be less than 1 metre wide

This could be checked by rather than just choosing a nsew neighbour, selecting the neighbour nsew which is n cells away from the object then checking it wont foul on any other objects!!!
"""

class Evolve(object):
	def __init__(self,param_file,input_map_name = None,output_map_name = None):

		self._json_dict = self.read_json(param_file)
		if output_map_name:
			self._output_map_name = output_map_name
		if input_map_name:
			self._input_map_name = input_map_name
			
		self._img = cv2.imread(self._input_map_name,cv2.IMREAD_UNCHANGED)

		self.remove(self._evolution["number_of_barrels_to_remove"],0)
		self.add(self._evolution["number_of_extra_barrels"],0)
		self.remove(self._evolution["number_of_blocks_to_remove"],2)
		self.add(self._evolution["number_of_extra_blocks"],2)
		self.save_img()
	

	def read_json(self,f_name):

		"""
			Loads parameters from json file required for evolving an environment
		"""
		with open(f_name) as json_file:
			data = json.load(json_file)

		self._input_map_name = data["input_map"]
		self._output_map_name = data["output_map"]
		self._outputfile = data["output_filename"]
		self._object_heights = data["heights"]
		self._sizing = data["sizing"]
		self._evolution = data["map_evolution"]

		return data

	def remove(self,no_to_remove,channel):

		"""
		function to remove objects from the world. 
		"""

		neighbours = [[-1,0],[1,0],[0,1],[0,-1]]
		other_channels = [0,2]
		other_channels.remove(channel)

		open_neighbours = []
		
		for i in range(0,len(self._img)):
			for j in range(0,len(self._img[i])):
				if (self._img[i,j,channel] > 0) & (self._img[i,j,other_channels[0]]== 0):
					for k in neighbours:
						a = i+k[0]
						b = j+k[1]
						if (0 <= a < len(self._img))& (0 <= b < len(self._img[i])):
							if (self._img[a,b,0] == 255) & (self._img[a,b,1] == 255) & (self._img[a,b,2] == 255):
								open_neighbours.append([i,j])
								break
		
		if len(open_neighbours) < no_to_remove:
			no_to_remove = len(open_neighbours)
		
		for i in range(0,no_to_remove):
			selection = random.choice(open_neighbours)
			open_neighbours.remove(selection)
			if len(self._img[selection[0],selection[1]]) == 3:
				self._img[selection[0],selection[1]] = [255,255,255]
			elif len(self._img[selection[0],selection[1]]) == 4:
				self._img[selection[0],selection[1]] = [255,255,255,255]

	def add(self,no_to_add,channel):

		"""
		function to add objects to the world. They must be bordering objects of the same type
		"""

		neighbours = [[-1,0],[1,0],[0,1],[0,-1]]
		other_channels = [0,2]
		other_channels.remove(channel)

		closed_neighbours = []
		for i in range(0,len(self._img)):
			for j in range(0,len(self._img[i])):
				if (self._img[i,j,0] == 255) & (self._img[i,j,1] == 255) & (self._img[i,j,2] == 255):
					for k in neighbours:
						a = i+k[0]
						b = j+k[1]
						if (0 <= a < len(self._img))& (0 <= b < len(self._img[i])):
							if (self._img[a,b,channel] == 255) & (self._img[a,b,other_channels[0]]== 0):							
								closed_neighbours.append([i,j])
								break
		if len(closed_neighbours) < no_to_add:
			no_to_add = len(closed_neighbours)

		for i in range(0,no_to_add):
			selection = random.choice(closed_neighbours)
			closed_neighbours.remove(selection)
			self._img[selection[0],selection[1],channel] = 	random.choice(self._object_heights.keys())
			self._img[selection[0],selection[1],other_channels] = 0 	

			if channel == 0:
				self._img[selection[0],selection[1],1] = 0
			else:
				self._img[selection[0],selection[1],1] = random.choice(self._sizing.keys())



	def save_img(self):
		cv2.imwrite(self._output_map_name,self._img) 
	

if __name__ == "__main__":
	e = Evolve("src/world_generator/config/params.json")
				

