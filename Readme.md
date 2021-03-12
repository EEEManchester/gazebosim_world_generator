# Gazebosim World Generator

*A work in progress!*

A node for generating and evolving gazebosim compatible worlds from pixel images.

The repository contains a ROS node called generate_environment which when running offered the services generate_world and evolve_world.

These services require a config file to be passed and optionally can also be passed a map(image) to overwrite the image defined in the config file. This allows a generic config file to be applied to different maps.

## Example Generation

Firstly watch the video in the media folder to get an understanding of what this repository is trying to do. It uses config files and coloured pixels to represent environments to generate. 

If you have successfully downloaded this repository try launching the world file custom_env2.world, found the world/custom_env2/ folder. You should see very little other than the walls. If you compare this world to the custom_env2.tiff int he maps folder there are obviously items missing. This is due to worlds which use custom model requiring the models to either be hardcoded or on your systems gazebo model path. If you wish to use the gazbeo model path this will make specifying model locations easier but is not required and for the purposes of this example we shall simply hardcode the locations. 

The first thing which need to be changed are these model locations. These can be found in config file /config/custom_env2.yaml. scroll down to file the definitions of the custom models and each models dae_location. They should start "/home/tom/ROS..... These need to be replaced with yourown file path. The files themselves exist in the meshes folder of this repository, or if you wish to use meshes from another location you can specify other locations too. 

Once you have swapped out the file paths you shold be able to run the world builder. This is done by running:

"rosrun gazebosim_world_generator generate_environment.py" 

This will make a service called generate_world appear. 

You can them call the service from your catkin_ws using:

rosservice call /generate_world "map_file: 'src/gazebosim_world_generator/maps/custom_env2.tiff' 
config_file: 'src/gazebosim_world_generator/config/custom_env2.yaml' "

Specifying the location of the image you want to make into a world and its config file. 

Once this service has run you should be able to open the world file in world/custom_env2/custom_env2.world and see an office scenario where some chairs and tables have been added, with chairs in two different orientations along with sound double high stacked bookcases.

Feel free to mess with this world or any of the others provided to familirise youself with the basic world generation.


## Drawing a map

An example of how to draw the maps can be seen in the video in the media folder. Here you can see that (currently) the maps have three types of objects, being walls, boxes and cylinders. Walls never move where as boxes and cylinders can be moved around using the Evolve_world service. The convention used for drawing maps is:

* Walls are black
* Cubes are red
* Cylinders are blue
* Custom models can now be specified with specific rgb colour codes **NB: See the custom_env2 yaml file for how an example of how to use custom models**

The green channel for boxes and cylinders is reserved for generating none standard sized objects. This will be discussed in section Config File.

Once a world has been drawn, it needs to be saved as an image. I suggest using .tiff as it does not compress the image, which can cause issues further down the line with colour shifts. 

For examples of environments see the maps folder.

## The Config File

Both Yaml and Json are now supported (Yaml is best).

A example config file can be found in the config folder, with custom_env2 being the most complete example showing all possibilities. 
These files are used to layout all of the parameters which are needed for using the map builder.

The required fields are needed for generating a base world. 

The scaling factors for boxes and cylinders are related to the metres_per_pixel value, such that 1.0 will result in each dimentions equaling the metres_per_pixel value.

The heights and sizing varables are user written dictionaries, which are used to map colour values to useable values. The colour values come from the respective red(boxes) and blue(cylinders) colour channels of a pixel. If you watch the video in the media folder you can see in the top left of the environment, how different shades of blue map to different stacking heights of cylinders. The channel is used by the sizing dictionary in a similar way.

For heights and example of:
**"100":1,**
**"200":2**
would result in the colour values of 100 mapping to a stacking height of 1 unit and a colour value of 200 to a stacking height of 2 units. This allows a user to define upto 255 different stacking heights. "0" cannot be used. 

Similarly for sizing:
**"0":1.0,**
**"100":0.25,**
**"200":0.5,**
would result in a scaling of the boxes or cylinders to to 1.0,0.25or 0.5 of the default values depending on the values. Here 255 custom values can be used with "0" always being the default size.


### Required settings

All parameters should be inside of a tag which shares the name of the world to be generated. I suggest you look at the custom_env2.yaml file for reference. 

key| sub-key | type | description
---| --- | --- | ---
**metres_per_pixel**||float|The number of metres one pixel represents
**input_map**||string|location of the input map file
**output_map**||string|location of the output map file
**output_world_filename**||string|location to output the gazebosim world file
**templates_folder**||string|location of the templates folder
**barrel_pos_noise**||float| noise factor when positionsing the cylinders set ot zero to remove
**barrel_stacking_noise**||float|noise factor for the vertically stacked barrels
**map_centre**|| dictionary|coordinate of the pixel which will be the centre of the map
-|x|int| x cell
-|y|int| y cell
**box**||dictionary|variables relating to default box sizes.
-|x|float| default x scaling
-|y|float| default y scaling
-|z|float| default z scaling
-|colour|string|RGBA colour of box objects format: "(float float float float)"
**cylinder**||dictary|variables relating to default cylinder sizes.
-|r|float| default radius scaling
-|z|float| default z scaling
-|colour|string|RGBA colour of cylinder objects format: "(float float float float)"
**walls**|||dictionary| A dictionary 
 -|height|float| height of walls objects
 -|colour|string|RGBA colour of wall objects format: "(float float float float)"
**heights**||dictionary| A dictionary which maps the pixel colour to the number of objects to stack vertically
 -|"value"|float|the colour value and it's related stacking height
**sizing**||dictionary|
-|"value"|float|the colour value and it's related scaling factor

#### Using custom models

It is possible to use custom meshes within the world builder. To do this certain parameters need to be provided. They are as follows.

key| sub-key | type | description
---| --- | --- | ---
**identifier**||string|A way of identifying a unique model/mesh
**-**|name|string|the name of the mesh to be used for this model
**-**|value| bgr value|bgr colour code which relates a pixel to this model
**-**|z_offset|float|centre offset of the model, to stop models spawning in the floor
**-**|rotation|float|radian angle of rotation of the model
**-**|dae_location|string|filepath to model to use MUST BE HARDCODED
**-**|pose_noise|float|If you would like the model to be moved slightly 
**-**|stacking|int|(Optional) How many models high should be stacked
**-**|height|float|(Optional) The vertical offset in metres each items shoudl be stacked at 

To better understand the use of custom models, I suggest you look at the custom_env2.yaml file. Here you can see how the custom models have been implemented, and how the same mesh can be used with different colours to give different outputs. i.e. chair and chair_90, where the chairs default orientation has been changed.

#### Additional settings

#####Whilst still usable the radiation settings have been depreciated in favour of the radiation sensors/sources package, with the evolver due to also be overhauled.


The additional settings relating to evolution used by evolve_world service. 

The radiation additional settings are used if a radiation map has been included for generation. 


key| sub-key | type | description
---| --- | --- | ---
**map_evolution**||dictionary|
-|number_of_barrels_to_remove|int|the number of cylinders to add at each evolution
-|number_of_extra_barrels|int|the number of cylinders to remove at each evolution
-|number_of_blocks_to_remove|int|the number of boxes to remove at each evolution 
-|number_of_extra_blocks|int|the number of boxes to add at each evolution
**radiation_map**||string|
**output_radiation_filename**||string|
**radiation_scaling**||float| value to scale 0-255 pixel values to real radiation values
**radiation_units_alpha**||string|units of radiation for alpha sensor
**radiation_units_beta** ||string|units of radiation for beta sensor
**radiation_units_gamma**||string|units of radiation for gamma sensor

## Usage

Both nodes require the generate_environments node to be running. This is invoked using: rosrun gazebosim_world_generator generate_environment.py

### Generate_world

To generate the world from your config file and map please call: 

rosservice call rosservice call /generate_world "map_file: 'optional:location/of/map' config_file: 'required:location/of/config/file'" 

The map file location can be passed in or pulled from the config file. 

The config file is required! 

If you wish to overwrite any of the option on a temporary basis rather than editing the config file, it can be done by changing the corrisponding element from the rosparam server. The easiest way to do this is to rosparam load the config yaml file into the param server, find the name of the parameter you wish to change using rosparam set and then call the service as normal. When running the service loads the passed in config file and then checks if any missing/altered params exist on the rosparam server.

### Evolve_world

To evolve the world from your config file and map please call: 

rosservice call rosservice call /evolve_world "map_file: 'optional:location/of/map' config_file: 'required:location/of/config/file'" 

Inside the config files there are options under map_evolution which allow you to specify if models should be added or taken away to cause changed. This is currently being overhauled to be more useful.



### Radiation mapper DEPRICICATED!!! USE THE RADIATION SENSORS AND SOURCES INSTEAD!!!

If a radiation file is included in the config file. The generate_world service will also create a radiation.yaml file. Radiation maps must be the same size as the environment map to allow for relative locations radiation to match up with the physical world, The RGB channels of each pixel map to Alpha,Beta and Gamma values scaled by the radiation scaling parameter. This can then be loaded into the ros param server using the rosparam load function in ROS.

## Jackle_with_lidar Launchfile

A launch file for loading a clearpath jackle with lidar and the base environment has been included to allow for testing/map generation.

## ToDo

* Tidy up config file to have output folder and then filenames rather than having to constantly repeat text
