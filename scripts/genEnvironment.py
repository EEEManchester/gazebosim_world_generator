#!/usr/bin/env python

import numpy as np
import random
import cv2
import json
import yaml
import random
import os

#envArray[i][j] = random.choice([True, False, False, False, False])

"""
class to generate a gazebo environments from an image
"""

class Environment(object):
	def __init__(self,param_file,input_map_name = None,out_file_name=None,input_rad_map_name = None):

		self._json_dict = self.read_json(param_file)

		if out_file_name:
			self._outputfile = out_file_name

		if input_map_name:
			self._input_map_name = input_map_name

		if input_rad_map_name:
			self._input_rad_map_name = input_rad_map_name
			

		#print self._input_map_name

		self._img = cv2.imread(self._input_map_name,cv2.IMREAD_UNCHANGED)
		cv2.imwrite(self._output_map_name,self._img)
		self._rad = cv2.imread(self._input_rad_map_name,cv2.IMREAD_UNCHANGED)

		print self._input_rad_map_name

		if (self._input_rad_map_name  != None) & (self._input_rad_map_name != ""):
			self.load_radiation()

		self.gen_objects()
		
		self.generate()

	def load_radiation(self):

		"""
		fuction to read radiation from the radiation image. each channel represents alpha,beta,gamma respectively
		These are then written into a yaml file to be loaded into the rosparam server. 
		Currently radiation detection is achieved by checkinf against these params
		This should be updated to add radiation sources into the gazebo model.
		Will require a param set in the config as not everyone will want to use this
		"""

		sources = dict()


		count = 0
		for j in range(0,len(self._rad)):
			for i in range(0,len(self._rad[j])):
				a = self._rad[j][i]
				if not ((a[0] == 0) &(a[1] == 0) & (a[2] == 0) | (a[0] == 255) &(a[1] == 255) & (a[2] == 255)):
					x = (j - self._map_centre["x"])*self._metres_per_pixel 
					y = (i - self._map_centre["y"])*self._metres_per_pixel
					if (a[0] > 0):
						sources["source_"+str(count)] = [{'x':x},{'y':y},{'z':0},{'value':float(a[0]*self._radiation_scaling)},{'type':'alpha'},{'units':str(self._radiation_units_alpha)},{'noise':2.0}]
						count +=1
					if (a[1] > 0):
						sources["source_"+str(count)] = [{'x':x},{'y':y},{'z':0},{'value':float(a[1]*self._radiation_scaling)},{'type':'beta'},{'units':str(self._radiation_units_beta)},{'noise':2.0}]
						count +=1
					if (a[2] > 0):
						sources["source_"+str(count)] = [{'x':x},{'y':y},{'z':0},{'value':float(a[2]*self._radiation_scaling)},{'type':'gamma'},{'units':str(self._radiation_units_gamma)},{'noise':2.0}]
						count +=1

					"""
					if (a[0] > 0):
						sources["source_"+str(count)] = dict(x=x,y=y,value=float(a[0]*self._radiation_scaling),'type'='alpha')
						count +=1
					if (a[1] > 0):
						sources["source_"+str(count)] = dict(x=x,y=y,value=float(a[1]*self._radiation_scaling),type='beta')
						count +=1
					if (a[2] > 0):
						sources["source_"+str(count)] = dict(x=x,y=y,value=float(a[2]*self._radiation_scaling),type='gamma')
						count +=1
					"""

		s = dict(sources=sources)

		print s

		#with open(self._radiation_file+".json", 'w') as outfile:
	 	#	json.dump(s, outfile[:-4]+"json", indent=4)

		with open(self._radiation_file, 'w') as outfile:
	 		yaml.dump(s, outfile, default_flow_style=False)



	def gen_objects(self):

		"""
			Function to detect objects in the image. 
			Free space is white. 
			Walls are black and never move. 
			Obstacles are red and barrels blue and can both move.
		"""
		blue = self._img[:,:,0]
		red = self._img[:,:,2]
		green = self._img[:,:,1]

		ret,b_max = cv2.threshold(blue,1,255,cv2.THRESH_BINARY)
		ret,r_max = cv2.threshold(red,1,255,cv2.THRESH_BINARY)
		#g_max = cv2.threshold(green,1,255,cv2.THRESH_BINARY)


		black = cv2.cvtColor(self._img, cv2.COLOR_BGR2GRAY)

		self._barrels = blue -r_max
		self._blocks = red -b_max
		self._size_array = green 
		ret,self._walls = cv2.threshold(black,1,255,cv2.THRESH_BINARY_INV)
		self._barrels = self._barrels.clip(min=0).astype(int)
		self._blocks = self._blocks.clip(min=0).astype(int)
		self._size_array = self._size_array.clip(min=0).astype(int)

	def read_json(self,f_name):

		"""
		 function to read useful params from config file
		"""
		with open(f_name) as json_file:
			data = json.load(json_file)

		self._input_map_name = data["input_map"]
		self._output_map_name = data["output_map"]
		self._input_rad_map_name = data["radiation_map"]
		self._outputfile = data["output_filename"]
		self._radiation_file = data["output_radiation_filename"]
		self._output_config_file_name = data["output_config_file_name"]
		self._templates_folder = data["templates_folder"]
		self._box = data["box"]
		self._cylinder = data["cylinder"]
		self._wall_height = data["walls"]
		self._map_centre = data["map_centre"]
		self._sizing = data["sizing"]
		self._metres_per_pixel = data["metres_per_pixel"]
		self._barrel_pos_noise = data["barrel_pos_noise"]
		self._barrel_stacking_noise = data["barrel_stacking_noise"]
		self._object_heights = data["heights"]
		self._radiation_scaling = data["radiation_scaling"]
		self._radiation_units_alpha = data["radiation_units_alpha"]
		self._radiation_units_beta = data["radiation_units_beta"]
		self._radiation_units_gamma = data["radiation_units_gamma"]
		return data


	def generate(self):

		"""
		function to write world model in sdf format. 
		This wraps the objects generated from the image with various required pre/post-amble required for the model to work.
		"""
		
		if not os.path.exists(self._outputfile):
			file(self._outputfile, 'w').close()


		open(self._outputfile, "w").writelines([l for l in open(self._templates_folder+"headerfile.txt").readlines()])

		self.gen_walls()
		self.populate(self._blocks,"box")
		self.populate(self._barrels,"cylinder")
		self.populate(self._walls,"box")
		

		open(self._outputfile, "a").writelines([l for l in open(self._templates_folder+"ground_plane.txt").readlines()])

		open(self._outputfile, "a").writelines([l for l in open(self._templates_folder+"endfile.txt").readlines()])


	def gen_walls(self):

		"""
		function to generate the walls as a single object rather than an array of boxes to reduce computational load
		"""

		horizontal_walls = self.find_walls(self._walls)
		self.clear_walls(horizontal_walls)
		vertical_walls = self.find_walls(np.transpose(self._walls),1)
		self.clear_walls(vertical_walls)
		remaining = self.find_remaining_walls(self._walls)
		self.clear_walls(remaining)

		walls_list =  [vertical_walls,remaining]
		
		walls = horizontal_walls
		for i in walls_list:
			try:
				walls = np.concatenate((walls,i),0)
			except:
				pass

		self.place_walls(walls,"box")

	def clear_walls(self,walls):
		"""
		function to clear walls which have been detected to stop corner blocks being detected twice
		"""
		if walls != None:
			for i in walls:
				for j in range(i[0][1],i[1][1]+1):
					for k in range(i[0][0],i[1][0]+1):
						self._walls[k][j] = 0


		

	def find_remaining_walls(self,array):
		"""
		Find remaining walls finds individual boxes which don't exist as part of horizonal or vertical sections of wall
		"""
		walls = []
		for j in  range(0,len(array)):
			for i in range(0,len(array[j])):	
				if array[j][i] == 255:
					walls.append([[j,i],[j,i]])

		return walls

	def find_walls(self,array,direction = 0):
		"""
			fuction to find consecutive horizonal or vertical pieces of wall
		"""

		walls = []
		for j in  range(0,len(array)):
			start_pos = None
			for i in range(0,len(array[j])):
				if (array[j][i] == 255) & (start_pos == None):
					start_pos = i
				elif (array[j][i] == 0) & (array[j][i-1] == 255) & (start_pos != None):
					if (i != start_pos+1):
						if direction == 0:
							walls.append([[j,start_pos],[j,i-1]])
						elif direction == 1:
							walls.append([[start_pos,j],[i-1,j]])

						start_pos = None
				elif (array[j][i] == 255) & (start_pos != None):
					pass
				else: 
					start_pos = None
 
		return walls
			


	def array_to_map(self,a,b):
		"""
			Convert from image_array space (cell index) to map space based in metres
		"""
		return (float(a)*self._metres_per_pixel) - (self._map_centre[b]*self._metres_per_pixel)

	def place_walls(self,walls,f_name):
		"""
			function to calcuate the size of and place walls in the world
		"""
		count = 0
		for i in walls:
			centre_pos_x = (i[0][0] + i[1][0])/2.0 
			centre_pos_y = (i[0][1] + i[1][1])/2.0 
			width = i[1][0] -i[0][0]	+ 1.0
			length = i[1][1] - i[0][1]	+ 1.0

			boxName =     "<model name='wall_"+ str(count) +"'>\n"  	
			count +=1
			open(self._outputfile, "a").writelines([boxName])
			with open(self._templates_folder+"{}1.txt".format(f_name)) as f:
				with open(self._outputfile, "a") as f1:
					for line in f:
						if "pose frame" in line:
							poseLine = "<pose frame=''>" + str(self.array_to_map(centre_pos_x,"x")) + " " + str(self.array_to_map(centre_pos_y,"x")) + " " + str(float(self._wall_height["height"])/2.0) +" 0 -0 0</pose> \n"
							f1.write(poseLine)
						elif "box" in line:
							f1.write(line)
							sizeLine = "<size>" + str(width*self._metres_per_pixel) + " " + str(length*self._metres_per_pixel) + " " + str(self._wall_height["height"]) +"</size> \n"
							f1.write(sizeLine)
							f1.write("</box>")
						elif "material" in line:
							f1.write(line)
							f1.write("<ambient>" +str(self._wall_height["colour"]) + "</ambient> \n")
							f1.write("<diffuse>" +str(self._wall_height["colour"]) + "</diffuse> \n")
							f1.write("</material>")

						else:
							f1.write(line) 
										


	def populate(self,array,f_name):
		"""
		Add to the sdf file for generating the gazebo world
		"""
		count = 0
		for x_index in range (0,array.shape[0]):
			for y_index in range (0,array.shape[1]):
				if array[x_index][y_index] > 1:
					noise_x = self.noise(self._barrel_pos_noise)
					noise_y = self.noise(self._barrel_pos_noise)
					for z_index in range (0,self._object_heights[str(array[x_index][y_index])]):				
							boxName =     "<model name='unit_{}_".format(f_name)+ str(count) +"'>\n"  	
							open(self._outputfile, "a").writelines([boxName])
							with open(self._templates_folder+"{}1.txt".format(f_name)) as f:
								with open(self._outputfile, "a") as f1:
									for line in f:
										if "pose frame" in line:
											if f_name == "cylinder":
												poseLine = "<pose frame=''>" + str(self.array_to_map(x_index,"x") +noise_x + self.noise(self._barrel_stacking_noise)) + " " + str(self.array_to_map(y_index,"y") + noise_y + self.noise(self._barrel_stacking_noise)) + " " + str(((self._json_dict[f_name]["z"]*z_index)+(self._json_dict[f_name]["z"])/2.0)*self._metres_per_pixel*self._sizing[str(self._size_array[x_index][y_index])]) +" 0 -0 0</pose> \n"
											else:	
												poseLine = "<pose frame=''>" + str(self.array_to_map(x_index,"x")) + " " + str(self.array_to_map(y_index,"y")) + " " + str(((self._json_dict[f_name]["z"]*z_index)+(self._json_dict[f_name]["z"])/2.0)*self._metres_per_pixel*self._sizing[str(self._size_array[x_index][y_index])]) +" 0 -0 0</pose> \n"
											f1.write(poseLine)
										elif "cylinder" in line:
											f1.write(line)
											f1.write("<radius>{}</radius> \n".format(self._cylinder["r"]*self._metres_per_pixel))
											f1.write("<length>{}</length> \n".format(self._cylinder["z"]*self._metres_per_pixel))
											f1.write("</cylinder> \n")
										elif "box" in line:
											f1.write(line)
											if self._size_array[x_index][y_index] == 0:
												sizeLine = "<size>" + str(self._box["x"]*self._metres_per_pixel) + " " + str(self._box["y"]*self._metres_per_pixel) + " " + str(self._box["z"]*self._metres_per_pixel) +"</size> \n"
											else:
												
												sizeLine = "<size>" + str(self._sizing[str(self._size_array[x_index][y_index])]*self._metres_per_pixel) + " " + str(self._sizing[str(self._size_array[x_index][y_index])]*self._metres_per_pixel) + " " + str(self._sizing[str(self._size_array[x_index][y_index])]*self._metres_per_pixel) +"</size> \n"
											f1.write(sizeLine)
											f1.write("</box>")
										elif "material" in line:
											f1.write(line)
											f1.write("<ambient>" +self._json_dict[f_name]["colour"] + "</ambient> \n")
											f1.write("<diffuse>" +self._json_dict[f_name]["colour"] + "</diffuse> \n")
											f1.write("</material>")
										else:
											f1.write(line) 

							count +=1
	def noise(self,n):
		"""
		Noise for placement of barrels. Limited to avoid collisions
		"""
		return (0.5-self._cylinder["r"])*n*random.uniform(-1,1)

if __name__ == "__main__":
	env = Environment("params.json")


