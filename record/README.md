# Data Recording

Record new data from CARLA

1. Start the carla simulator
1. Spawn some traffic from the carla examples `python3 spawn_npc.py -n 30 -w 30`
1. Spawn the ego vehicle `python3 manual_control.py`
1. Start the autopilot with key `P` and log data at interesting states `Ctrl + R`
1. Record the sensor data with key `R` while replaying the log `Ctrl + P`.
1. Save the data of the output folder `_out`
1. Repeat (5) and (6) for a different weather condition (Change weather with key `C`)

Having the same data for different weather conditions allows us to reuse the ROI labels that we created once.

To replay a recording file after restarting the manual control the hero actor need to be attached. Use the example replayer and our manual control with hero attach option

```shell script
python3 start_replaying.py -f <manual_recording.rec>
python3 manual_control.py --attach_ego_vehicle
```
