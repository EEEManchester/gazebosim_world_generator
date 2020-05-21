# Gazebosim World Generator

*A work in progress!*

A node for generating and evolving gazebosim compatible worlds from pixel images.

The repository contains a ROS node called generate_environment which when running offered the services generate_world and evolve_world.

These services require a config file to be passed and optionally can also be passed a map(image) to overwrite the image defined in the config file. This allows a generic config file to be applied to different maps.

## Drawing a map

An example of how to draw the maps can be seen in the video in the media folder. Here you can see that (currently) the maps have three types of objects, being walls, boxes and cylinders. Walls never move where as boxes and cylinders can be moved around using the Evolve_world service. The convention used for drawing maps is:

* Walls are black
* Cubes are red
* Cylinders are blue

The green channel is reserved for generating none standard sized objects. This will be discussed in section Config File.

One a world has been drawn, it needs to be saved as an image. I suggest using .tiff as it does not compress the image, which can cause issues further down the line with colour shifts. 

For examples of environemts see the maps folder.

## The Config File

A example config file can be found in the config folder. 
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


For the heights and 
### Required settings

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

#### Additional settings

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

The map file location can be passed in or pulled from the config file. The config file is required.

### Evolve_world

To evolve the world from your config file and map please call: 

rosservice call rosservice call /evolve_world "map_file: 'optional:location/of/map' config_file: 'required:location/of/config/file'" 

**Note that currently the radiation locations do not move with the barrels!!!! To be added**

### Radiation mapper

If a radiation file is included in the config file. The generate_world service will also create a radiation.yaml file. Radiation maps must be the same size as the environment map to allow for relative locations radiation to match up with the physical world, The RGB channels of each pixel map to Alpha,Beta and Gamma values scaled by the radiation scaling parameter. This can then be loaded into the ros param server using the rosparam load function in ROS.

## Jackle_with_lidar Launchfile

A launch file for loading a clearpath jackle with lidar and the base environment has been included to allow for testing/map generation.

## ToDo

* Remove all of the hardcoding of variables
* Tidy up config file to have output folder and then filenames rather than having to constantly repeat text
* Make radiation location update with barrels


