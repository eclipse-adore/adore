# traffic predictor
This is a traffic prediction node that takes
a description of the state of each vehicle, including position and velocity.
and outputs a navigation message vector of points representing the center of 
the lane in the direction of the navigation goal.

This node/program provides a GNU Makefile for building, testing, and running.

Before starting make sure your ADORe workspace is built:
```
cd ros2_workspace
make build
```

1. Build the package with (within the ADORe CLI):
```bash
make cli
cd ros2_workspace/src/traffic_predictor
make build
```

2. start a scenario(within the ADORe CLI):
```bash
cd adore_scenarios/simuation_scenarios
ros2 launch adso_demo_1.py
```
or
```bash
make cli
cd adore_scenarios/simuation_scenarios
ros2 launch adso_demo_2.py
```

3. Run the node(within the ADORe CLI):
```bash
make cli
cd ros2_workspace/src/traffic_predictor
make run
```

4. In another terminal/shell the output can be observed(within the ADORe CLI):
```bash
make cli
ros2 topic echo /ego_vehicle/traffic_prediction
```
