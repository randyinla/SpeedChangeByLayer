# SpeedChangeByLayer - Copyright (c) 2020 Randy Walker, randy@walkersystems.net
# This script was inspired by the ChangeAtZ script by Steven Morlock, smorloc@gmail.com
# I wanted a script that would allow me to only change print & fan speeds per layer, not when the z-axis change happens, starting/ending at the ;LAYER:xx marker comments
# I started with the code from the ChangeAtZ script and have removed & re-written most of it to only handle print/fan speeds per layer
# It runs with the PostProcessingPlugin which is released under the terms of the AGPLv3 or higher
# This script is licensed under the Creative Commons - Attribution - Share Alike (CC BY-SA) terms
#
# This script accepts four parameters, provided by the user to change Print and/or Fan speeds by layer:
#   1) Layer number from the Cura gui on which to start the speed change
#      Script will subtract 1 from the layer number provided because layers in gcode start at 0 not 1
#   2) How many layers total to apply speed changes to
#   3) Print Speed change percentage
#      Script will automatically reset the Print Speed back to 100% at the end of the last layer
#   4) Fan Speed percentage of 100%, not a % change from current fan speed
#      Script will find the original Fan Speed on the last layer that has been overridden (if it existed) and reset the Fan Speed to that number or 0 at the end of the last layer affected
#
# PRINT SPEEDS:
# Since the script ends each layer change by resetting the print speed back to 100% of the Cura speed, adding multiple instances of this script
# will always calculate the percentage up or down from 100%, the original print speed set in Cura, and not from the last instance of the script
# ie.If the first instance set print speed to 50% & a 2nd instance set print speed to 20%, that would equal 20% of the original Cura print speed and not 20% of 50%
#
# FAN SPEEDS:
# The script ends each layer change by resetting the fan speed back to the last fan speed found before the last layer affected.
# Fan speed changes are entered as a percentage of 100% [% of 255], not the original Cura speed or last found layer fan speed.
# Resetting fan speed: If the current layer originally had a speed of 50% [50% of 255 = 127.5 PWM number for the M106 command], then the fan speed will reset to that number at the end of the speed change

## Changelog:
## V0.1.0 - Initial version, pulled in bits & pieces from other scripts
## V0.2.0 - Both Print Speed & Fan Speed work for 1 total layer
##        - Print Speed works with total layers > 1
##        - Added the UM.Logger
##        - Multiple instances properly calculates how many have been applied to the gcode
## V0.3.0 - Changed Fan Speed field from PWM numbers between 0-255 to a percentage of 100%, not a % of original Cura fan speed or current layer fan speed,
##          like changing fan speed on front panel of machine during a print
##        - Added SpeedChangeByLayer instance # and total number of layers affected by each instance in SpeedChangeByLayer starting comment
##        - Added speed type name & percentage amount as comment after each actual speed change command
##        - Split the command string, "str" into 2 separate strings: startStr & endStr, to accomodate comments placed in the GCode
##        - Storing percentage entered by user for each speed type in a separate props attribute, "per" to accomodate comments placed in the GCode
##        - Updated notes/description
##        TODO: - Scan each layer prior to endLayer for fan speed changes, replacing stored fan speed on each layer up until 2nd to last affected layer

## Gcode commands used:
## M220 S<percentage> - Affects both print & travel speeds up or down from original speed set in Cura. Same effect as changing the speed % on the printer during printing
## M106 S<PWM_number> - Affects the fan speed
## M605 Save print & fan speeds to UM
## M606 Recall print & fan speeds from UM

from UM.Logger import Logger

import re

from ..Script import Script

class SpeedChangeByLayer(Script):
    version = "0.3.0"
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"Speed Change By Layer """ + self.version + """",
            "key":"SpeedChangeByLayer",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "layer_number":
                {
                    "label": "Cura Preview Layer No.",
                    "description": "Layer number from Cura Preview GUI to start speed change on",
                    "unit": "",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": -100,
                    "minimum_value_warning": 1
                },
                "number_of_layers":
                {
                    "label": "How Many Layers Total",
                    "description": "How many layers total this speed change is applied to",
                    "unit": "",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": 1,
                    "maximum_value_warning": 50
                },
                "change_print_speed":
                {
                    "label": "Change Print Speed",
                    "description": "Select to change the print speed (print & travel)",
                    "type": "bool",
                    "default_value": false
                },
                "print_speed":
                {
                    "label": "Print Speed",
                    "description": "Percentage of original Cura speed (print & travel).  Behaves just like changing the print speed percentage on the machine's panel during printing",
                    "unit": "%",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 1,
                    "minimum_value_warning": 10,
                    "maximum_value_warning": 150,
                    "enabled":"change_print_speed"
                },
                "change_fan_speed":
                {
                    "label": "Change Fan Speed",
                    "description": "Select to change Fan Speed",
                    "type": "bool",
                    "default_value": false
                },
                "fan_speed":
                {
                    "label": "Fan Speed",
                    "description": "New fan speed as percentage of 100% [% of 255] (not of original Cura speed or current layer speed). Behaves just like changing the fan speed percentage on the machine's panel during printing",
                    "unit": "%",
                    "type": "int",
                    "default_value": 100,
                    "minimum_value": 1,
                    "maximum_value": 100,
                    "minimum_value_warning": 10,
                    "enabled": "change_fan_speed"
                }
            }
        }"""

    def getValue(self, line, key, default = None): #replace default getvalue due to comment-reading feature
        if not key in line or (";" in line and line.find(key) > line.find(";") and
                                   not ";SpeedChangeByLayer" in key and not ";LAYER:" in key):
            return default
        subPart = line[line.find(key) + len(key):] #allows for string lengths larger than 1
        if ";SpeedChangeByLayer" in key:
            m = re.search("^[0-4]", subPart)
        elif ";LAYER:" in key:
            m = re.search("^[+-]?[0-9]*", subPart)
        else:
            #the minus at the beginning allows for negative values, e.g. for delta printers
            m = re.search("^[-]?[0-9]*\.?[0-9]*", subPart)
        if m == None:
            return default
        try:
            return float(m.group(0))
        except:
            return default

    def execute(self, data):
        props = {   "printSpeed": { "on": self.getSettingValueByKey("change_print_speed"),
                                    "startStr": "M220 S{} ;Print speed {}% of original Cura speed\n",
                                    "endStr": "M220 S%f ;Resetting print speed\n",
                                    "per": self.getSettingValueByKey("print_speed"),
                                    "new": self.getSettingValueByKey("print_speed"),
                                    "old": 100},
                    "fanSpeed": {   "on": self.getSettingValueByKey("change_fan_speed"),
                                    "startStr": "M106 S{} ;Fan speed {}% of 100% [% of 255]\n",
                                    "endStr": "M106 S%f ;Resetting fan speed\n",
                                    "per": self.getSettingValueByKey("fan_speed"),
                                    "new": 255 * (self.getSettingValueByKey("fan_speed")*.01),
                                    "old": 0}}
        total_layers = max(int(self.getSettingValueByKey("number_of_layers")),1)
        done_layers = 0
        current_fan_layer = -100000
        current_layer = -100000
        # IsUM2: Used for reset of values (ok for Marlin/Sprinter), has to be set to 1 for UltiGCode (work-around for missing default values)
        # state 0: deactivated, state 1: activated, state 2: active, but below z,
        # state 3: active and partially executed (multi layer), state 4: active and passed z
        state = 1
        IsUM2 = False
        oldValueUnknown = False
        instance = 0
        target_layer = int(self.getSettingValueByKey("layer_number"))-1
        end_layer = target_layer + total_layers
        index = 0
        for active_layer in data:
            if "M107" in active_layer: # store existing fan setting per layer
                props["fanSpeed"]["old"] = 0
            if "M106" in active_layer:
                fan_lines = active_layer.split("\n")
                for line in fan_lines:
                    if ";LAYER:" in line:
                        current_fan_layer = self.getValue(line, ";LAYER:", current_fan_layer)
                    if "M106" in line and current_fan_layer == target_layer:
                        props["fanSpeed"]["old"] = float(line[6:])
            new_gcode = ""
            speed_gcode = ""
            lines = active_layer.split("\n")
            for line in lines:
                if line.strip() == "":
                    continue
                if ";Generated with Cura_SteamEngine" in line:
                    instance += 1
                    new_gcode += ";SpeedChangeByLayer instances: %d\n" % instance
                IsUM2 = ("FLAVOR:UltiGCode" in line) or IsUM2
                if ";SpeedChangeByLayer instances:" in line:
                    try:
                        prevInstance = int(line[30:])
                    except:
                        prevInstance = instance
                    instance = prevInstance
                if ";LAYER:" in line: # CURRENT LAYER NUMBER
                    current_layer = self.getValue(line, ";LAYER:", current_layer)
                    # START SPEED CHANGE
                    if current_layer == target_layer:
                        if total_layers-done_layers>0: #still layers to go?
                            speed_gcode += ";SpeedChangeByLayer V%s instance #%d: Starting at layer %d for a total of %d %s\n" % (self.version, instance, current_layer, total_layers, 'layers' if total_layers > 1 else 'layer')
                            for speedType in props:
                                if props[speedType]["on"]:
                                    speed_gcode += props[speedType]["startStr"].format(format(props[speedType]["new"], '.6f'), props[speedType]["per"])
                            done_layers += 1
                    # END SPEED CHANGE
                    if current_layer == end_layer:
                        speed_gcode += ";SpeedChangeByLayer V%s: Reset layer %d\n" % (self.version, current_layer-1)
                        if IsUM2 and oldValueUnknown: #executes on UM2 with Ultigcode and machine setting
                            speed_gcode += "M606 S%d;recalls saved settings\n" % (instance-1)
                        else: #executes on RepRap, UM2 with Ultigcode and Cura setting
                            for speedType in props:
                                if props[speedType]["on"]:
                                    speed_gcode += props[speedType]["endStr"] % float(props[speedType]["old"])
                # Adding line back into new_gcode or not
                if not ("M84" in line or "M25" in line or ("G1" in line and (state==3 or state==4)) or
                        ";SpeedChangeByLayer instances:" in line):
                        if ";LAYER:" in line and current_layer == target_layer:
                            new_gcode += line + "\n" + speed_gcode
                        elif ";LAYER:" in line and current_layer == end_layer:
                            new_gcode += speed_gcode + line + "\n"
                        else:
                            # Remove existing fan commands from the range of layers fanSpeed changes
                            if props["fanSpeed"]["on"]:
                                if current_layer == target_layer:
                                    if not ("M106" in line or "M107" in line):
                                        new_gcode += line + "\n"
                                else:
                                    new_gcode += line + "\n"
                            else:
                                new_gcode += line + "\n"
            data[index] = new_gcode
            index += 1
        return data
