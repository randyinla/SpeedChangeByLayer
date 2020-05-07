# SpeedChangeByLayer
Cura plugin to insert print speed or fan speed changes on a layer by layer basis in the Cura generated GCode
Copyright (c) 2020 Randy Walker, randy@walkersystems.net

This script was inspired by the ChangeAtZ script by Steven Morlock, smorloc@gmail.com
I wanted a script that would allow me to only change print & fan speeds per layer, not when the z-axis change happens, starting/ending at the ;LAYER:xx marker comments
I started with the code from the ChangeAtZ script and have removed & re-written most of it to only handle print/fan speeds per layer
It runs with the PostProcessingPlugin which is released under the terms of the AGPLv3 or higher
This script is licensed under the Creative Commons - Attribution - Share Alike (CC BY-SA) terms

This script accepts four parameters, provided by the user to change Print and/or Fan speeds by layer:
  1) Layer number from the Cura gui on which to start the speed change
     Script will subtract 1 from the layer number provided because layers in gcode start at 0 not 1
  2) How many layers total to apply speed changes to
  3) Print Speed change percentage
     Script will automatically reset the Print Speed back to 100% at the end of the last layer
  4) Fan Speed percentage of 100%, not a % change from current fan speed
     Script will find the original Fan Speed on the last layer that has been overridden (if it existed) and reset the Fan Speed to that number or 0 at the end of the last layer affected

# PRINT SPEEDS:
Since the script ends each layer change by resetting the print speed back to 100% of the Cura speed, adding multiple instances of this script
will always calculate the percentage up or down from 100%, the original print speed set in Cura, and not from the last instance of the script
ie.If the first instance set print speed to 50% & a 2nd instance set print speed to 20%, that would equal 20% of the original Cura print speed and not 20% of 50%

# FAN SPEEDS:
The script ends each layer change by resetting the fan speed back to the last fan speed found before the last layer affected.
Fan speed changes are entered as a percentage of 100% [% of 255], not the original Cura speed or last found layer fan speed.
Resetting fan speed: If the current layer originally had a speed of 50% [50% of 255 = 127.5 PWM number for the M106 command], then the fan speed will reset to that number at the end of the speed change
