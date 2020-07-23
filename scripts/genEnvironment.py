#!/usr/bin/env python

import numpy as np
import random
import cv2
import json
import yaml
import random
import os
import rospy

#envArray[i][j] = random.choice([True, False, False, False, False])

"""
class to generate a gazebo environments from an image
"""

class Environment(object):
	def __init__(self,param_file,input_map_name = None,out_file_name=None,input_rad_map_name = None):

		self._json_dict = self.read_params(param_file)
		prefix = input_map_name.split('/')[-1].split('.')[0]+'/'

		self.check_param_server(prefix)
		if bool(self._json_dict) == False:
			self._json_dict = rospy.get_param(prefix[:-1])

		print self._json_dict

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

		if (self._input_rad_map_name  != None) & (self._input_rad_map_name != "")& (self._input_rad_map_name != "None"):
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
					if self._radiation_output_file_format == 0:
						if (a[0] > 0):
							sources["source_"+str(count)] = {'x':x,'y':y,'z':0,'value':float(a[0]*self._radiation_scaling),'type':'alpha','units':str(self._radiation_units_alpha),'noise':2.0}
							count +=1
						if (a[1] > 0):
							sources["source_"+str(count)] = {'x':x,'y':y,'z':0,'value':float(a[1]*self._radiation_scaling),'type':'beta','units':str(self._radiation_units_beta),'noise':2.0}
							count +=1
						if (a[2] > 0):
							sources["source_"+str(count)] = {'x':x,'y':y,'z':0,'value':float(a[2]*self._radiation_scaling),'type':'gamma','units':str(self._radiation_units_gamma),'noise':2.0}
							count +=1
					elif self._radiation_output_file_format == 1:
						if (a[0] > 0):
							sources["source_"+str(count)] = {'x':x},{'y':y},{'z':0},{'value':float(a[0]*self._radiation_scaling)},{'type':'alpha'},{'units':str(self._radiation_units_alpha)},{'noise':2.0}
							count +=1
						if (a[1] > 0):
							sources["source_"+str(count)] = {'x':x},{'y':y},{'z':0},{'value':float(a[1]*self._radiation_scaling)},{'type':'beta'},{'units':str(self._radiation_units_beta)},{'noise':2.0}
							count +=1
						if (a[2] > 0):
							sources["source_"+str(count)] = {'x':x},{'y':y},{'z':0},{'value':float(a[2]*self._radiation_scaling)},{'type':'gamma'},{'units':str(self._radiation_units_gamma)},{'noise':2.0}
							count +=1

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
		white = (blue/3.0) +(red/3.0) + (green/3.0)
		ret,white = cv2.threshold(white,250,255,cv2.THRESH_BINARY)

		#try removing white by filtering on the gray image!!! the you can use custom colours!!!
		blue_no_white = (blue -white)
		red_no_white = (red -white)


		self._barrels = blue_no_white- r_max
		self._blocks =  red_no_white - b_max
		self._size_array = green -white
		ret,self._walls = cv2.threshold(black,1,255,cv2.THRESH_BINARY_INV)
		self._barrels = self._barrels.clip(min=0).astype(int)
		self._blocks = self._blocks.clip(min=0).astype(int)
		self._size_array = self._size_array.clip(min=0).astype(int)

		leftovers = (blue_no_white-self._barrels) + (red_no_white-self._blocks) + self._size_array
		ret,mask = cv2.threshold(leftovers,1,255,cv2.THRESH_BINARY)
		self._custom = self._img
		self._custom[mask==0] = [0,0,0,0]

	def check_param_server(self,prefix):

		"allows setting of default values if not provided through either the config file or loaded into rosparam server"

		if rospy.has_param(prefix+"input_map"):
			self._input_map_name = rospy.get_param(prefix+"input_map")
		elif self._input_map_name == None:
			self._input_map_name = "default_value"
		if rospy.has_param(prefix+"output_map"):
			self._output_map_name = rospy.get_param(prefix+"output_map")
		elif self._output_map_name == None:
			self._output_map_name = "default_value"
		if rospy.has_param(prefix+"radiation_map"):
			self._input_rad_map_name = rospy.get_param(prefix+"radiation_map")
		elif self._input_rad_map_name == None:
			self._input_rad_map_name = "default_value"
		if rospy.has_param(prefix+"output_filename"):
			self._outputfile = rospy.get_param(prefix+"output_filename")
		elif self._outputfile == None:
			self._outputfile = "default_value"
		if rospy.has_param(prefix+"output_radiation_filename"):
			self._radiation_file = rospy.get_param(prefix+"output_radiation_filename")
		elif self._radiation_file == None:
			self._radiation_file = "default_value"
		if rospy.has_param(prefix+"output_config_file_name"):
			self._output_config_file_name = rospy.get_param(prefix+"output_config_file_name")
		elif self._output_config_file_name == None:
			self._output_config_file_name = "default_value"
		if rospy.has_param(prefix+"templates_folder"):
			self._templates_folder = rospy.get_param(prefix+"templates_folder")
		elif self._templates_folder == None:
			self._templates_folder = "default_value"
		if rospy.has_param(prefix+"box"):
			self._box = rospy.get_param(prefix+"box")
		elif self._box == None:
			self._box = "default_value"
		if rospy.has_param(prefix+"cylinder"):
			self._cylinder = rospy.get_param(prefix+"cylinder")
		elif self._cylinder == None:
			self._cylinder = "default_value"
		if rospy.has_param(prefix+"walls"):
			self._wall_height = rospy.get_param(prefix+"walls")
		elif self._wall_height == None:
			self._wall_height = "default_value"
		if rospy.has_param(prefix+"map_centre"):
			self._map_centre = rospy.get_param(prefix+"map_centre")
		elif self._map_centre == None:
			self._map_centre = "default_value"
		if rospy.has_param(prefix+"sizing"):
			self._sizing = rospy.get_param(prefix+"sizing")
		elif self._sizing == None:
			self._sizing = "default_value"
		if rospy.has_param(prefix+"metres_per_pixel"):
			self._metres_per_pixel = rospy.get_param(prefix+"metres_per_pixel")
		elif self._metres_per_pixel == None:
			self._metres_per_pixel = "default_value"
		if rospy.has_param(prefix+"barrel_pos_noise"):
			self._barrel_pos_noise = rospy.get_param(prefix+"barrel_pos_noise")
		elif self._barrel_pos_noise == None:
			self._barrel_pos_noise = "default_value"
		if rospy.has_param(prefix+"barrel_stacking_noise"):
			self._barrel_stacking_noise = rospy.get_param(prefix+"barrel_stacking_noise")
		elif self._barrel_stacking_noise == None:
			self._barrel_stacking_noise = "default_value"
		if rospy.has_param(prefix+"heights"):
			self._object_heights = rospy.get_param(prefix+"heights")
		elif self._object_heights == None:
			self._object_heights = "default_value"
		if rospy.has_param(prefix+"radiation_scaling"):
			self._radiation_scaling = rospy.get_param(prefix+"radiation_scaling")
		elif self._radiation_scaling == None:
			self._radiation_scaling = "default_value"
		if rospy.has_param(prefix+"radiation_units_alpha"):
			self._radiation_units_alpha = rospy.get_param(prefix+"radiation_units_alpha")
		elif self._radiation_units_alpha == None:
			self._radiation_units_alpha = "default_value"
		if rospy.has_param(prefix+"radiation_units_beta"):
			self._radiation_units_beta = rospy.get_param(prefix+"radiation_units_beta")
		elif self._radiation_units_beta == None:
			self._radiation_units_beta = "default_value"
		if rospy.has_param(prefix+"radiation_units_gamma"):
			self._radiation_units_gamma = rospy.get_param(prefix+"radiation_units_gamma")
		elif self._radiation_units_gamma == None:
			self._radiation_units_gamma = "default_value"
		if rospy.has_param(prefix+"radiation_output_file_format"):
			self._radiation_output_file_format = rospy.get_param(prefix+"radiation_output_file_format")
		elif self._radiation_output_file_format == None:
			self._radiation_output_file_format = "default_value"
		if rospy.has_param(prefix+"custom_models"):
			self._custom_models = rospy.get_param(prefix+"custom_models")
		elif self._custom_models == None:
			self._custom_models = None
		

	def read_params(self,f_name):

		"""
		 function to read useful params from config file
		"""
		if ".json" in f_name:
			with open(f_name) as json_file:
				data = json.load(json_file)
		elif "yaml" in f_name:
			with open(f_name) as yaml_file:
				data = yaml.load(yaml_file)		
		else:
			data = {}		
		if "input_map" in data:
			self._input_map_name = data["input_map"]
		if "output_map" in data:
			self._output_map_name = data["output_map"]
		if "radiation_map" in data:
			self._input_rad_map_name = data["radiation_map"]
		if "output_filename" in data:
			self._outputfile = data["output_filename"]
		if "output_radiation_filename" in data:
			self._radiation_file = data["output_radiation_filename"]
		if "output_config_file_name" in data:
			self._output_config_file_name = data["output_config_file_name"]
		if "templates_folder" in data:
			self._templates_folder = data["templates_folder"]
		if "box" in data:
			self._box = data["box"]
		if "cylinder" in data:
			self._cylinder = data["cylinder"]
		if "walls" in data:
			self._wall_height = data["walls"]
		if "map_centre" in data:
			self._map_centre = data["map_centre"]
		if "sizing" in data:
			self._sizing = data["sizing"]
		if "metres_per_pixel" in data:
			self._metres_per_pixel = data["metres_per_pixel"]
		if "barrel_pos_noise" in data:
			self._barrel_pos_noise = data["barrel_pos_noise"]
		if "barrel_stacking_noise" in data:
			self._barrel_stacking_noise = data["barrel_stacking_noise"]
		if "heights" in data:
			self._object_heights = data["heights"]
		if "radiation_scaling" in data:
			self._radiation_scaling = data["radiation_scaling"]
		if "radiation_units_alpha" in data:
			self._radiation_units_alpha = data["radiation_units_alpha"]
		if "radiation_units_beta" in data:
			self._radiation_units_beta = data["radiation_units_beta"]
		if "radiation_units_gamma" in data:
			self._radiation_units_gamma = data["radiation_units_gamma"]
		if "radiation_output_file_format" in data:
			self._radiation_output_file_format = data["radiation_output_file_format"]
		if "custom_models" in data:
			self._custom_models = data["custom_models"]
				
		return data


	def generate(self):

		"""
		function to write world model in sdf format. 
		This wraps the objects generated from the image with various required pre/post-amble required for the model to work.
		"""
		
		if not os.path.exists(self._outputfile):
			file(self._outputfile, 'w').close()


		open(self._outputfile, "w").writelines([l for l in open(self._templates_folder+"headerfile.sdf").readlines()])

		self.gen_walls()
		self.populate(self._blocks,"box")
		self.populate(self._barrels,"cylinder")
		self.populate(self._walls,"box")
		self.populate(self._custom,"custom")
		

		open(self._outputfile, "a").writelines([l for l in open(self._templates_folder+"ground_plane.sdf").readlines()])

		open(self._outputfile, "a").writelines([l for l in open(self._templates_folder+"endfile.sdf").readlines()])


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

			name = "wall_"+ str(count) 
			pose = str(self.array_to_map(centre_pos_x,"x")) + " " + str(self.array_to_map(centre_pos_y,"y")) + " " + str(float(self._wall_height["height"])/2.0) + " 0 0 0"
			size = str(width*self._metres_per_pixel) + " " + str(length*self._metres_per_pixel) + " " + str(self._wall_height["height"])
			colour = str(self._wall_height["colour"])
			keywords = {'name': name, 'pose': pose, 'size': size, 'colour': colour}			
			count +=1
			open(self._outputfile, "a")
			with open(self._templates_folder+"{}.sdf".format(f_name)) as f:
				with open(self._outputfile, "a") as f1:
					for line in f:

						f1.write(line.format('',**keywords)) 
										


	def populate(self,array,f_name):
		"""
		Add to the sdf file for generating the gazebo world
		"""

		count = 0
		for x_index in range (0,array.shape[0]):
			for y_index in range (0,array.shape[1]):
				if type(array[x_index][y_index]) is np.ndarray:
					test = sum(array[x_index][y_index])
				else:
					test = array[x_index][y_index]
				if test > 1:
					keywords = {'name': '','pose':'','radius': '','length': '','radius': '','size': '','colour': ''}
					if f_name == "custom":
						for c in self._custom_models:
							col = np.asarray((self._custom_models[c]["value"].lstrip().split(" ")),dtype=int)	
							if (col[0] == array[x_index][y_index][0]) & (col[1] == array[x_index][y_index][1]) & (col[2] == array[x_index][y_index][2]):		
								name = self._custom_models[c]["name"]
								if self._custom_models[c]["pose_noise"]:
									n = self._custom_models[c]["pose_noise"]
								else:
									n = 0.0
								noise_x = self.noise(n)
								noise_y = self.noise(n)
								keywords['name'] =     name+"_"+str(count)  
								keywords['pose'] = str(self.array_to_map(x_index,"x")+noise_x) + " " + str(self.array_to_map(y_index,"y")+noise_y) + " " + str(self._custom_models[c]["z_offset"]) +" 0 -0 0"	
								keywords['dae_location'] = self._custom_models[c]["dae_location"]
								print keywords
								open(self._outputfile, "a")
								with open(self._templates_folder+"{}.sdf".format(name)) as f:
									with open(self._outputfile, "a") as f1:
										for line in f:
											f1.write(line.format('',**keywords)) 
						count +=1

					else:		
						if f_name == "cylinder":
							noise_x = self.noise(self._barrel_pos_noise)
							noise_y = self.noise(self._barrel_pos_noise)
							name = "cylinder"
							keywords['radius'] = self._cylinder["r"]*self._metres_per_pixel
							keywords['length'] = self._cylinder["z"]*self._metres_per_pixel
						elif f_name == 'box':	
							name = "box"
							if self._size_array[x_index][y_index] == 0:
								keywords['size'] = str(self._box["x"]*self._metres_per_pixel) + " " + str(self._box["y"]*self._metres_per_pixel) + " " + str(self._box["z"]*self._metres_per_pixel)
							else:		
								keywords['size'] = str(self._sizing[str(self._size_array[x_index][y_index])]*self._metres_per_pixel) + " " + str(self._sizing[str(self._size_array[x_index][y_index])]*self._metres_per_pixel) + " " + str(self._sizing[str(self._size_array[x_index][y_index])]*self._metres_per_pixel)

						if self._json_dict[name]["colour"]:
							keywords['colour'] = self._json_dict[name]["colour"]

						for z_index in range (0,self._object_heights[str(array[x_index][y_index])]):				
							keywords['name'] =     name+"_"+str(count)  	
							if name == "cylinder":
								keywords['pose'] = str(self.array_to_map(x_index,"x") +noise_x + self.noise(self._barrel_stacking_noise)) + " " + str(self.array_to_map(y_index,"y") + noise_y + self.noise(self._barrel_stacking_noise)) + " " + str(((self._json_dict[f_name]["z"]*z_index)+(self._json_dict[f_name]["z"])/2.0)*self._metres_per_pixel*self._sizing[str(self._size_array[x_index][y_index])]) +" 0 -0 0"			
							elif name == 'box':
								keywords['pose'] = str(self.array_to_map(x_index,"x")) + " " + str(self.array_to_map(y_index,"y")) + " " + str(((self._json_dict[f_name]["z"]*z_index)+(self._json_dict[f_name]["z"])/2.0)*self._metres_per_pixel*self._sizing[str(self._size_array[x_index][y_index])]) +" 0 -0 0"
							
							open(self._outputfile, "a")
							with open(self._templates_folder+"{}.sdf".format(name)) as f:
								with open(self._outputfile, "a") as f1:
									for line in f:
										f1.write(line.format('',**keywords)) 

							count +=1

	def noise(self,n):
		"""
		Noise for placement of barrels. Limited to avoid collisions
		"""
		return (0.5-self._cylinder["r"])*n*random.uniform(-1,1)

if __name__ == "__main__":
	env = Environment("params.json")


