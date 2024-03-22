## Use Case # 1: Why are they pitting? 
This section describes how this program arrives at the following conclusions:

When a player pits:
* For damage 
* Versus pit for fuel 
* Versus pit for wet/dry tires

### Telemetry Objects:
Use the CarIdx arrays
* CarIdxOnPitRoad
* CarIdxTireCompound

### Computation
Create a table that tracks players pit cycles, this will be determined when the CarIdxOnPitRoad switches False->True. Then track time that CarIdx has spent on pit road. Use the session info to identify what the pit road length is, and what the pit speed limit is. Compute expected time of:
* drive through penalty = (pit road length / pit speed limit)+variance
* TBD - average refuel time
* compute change in tires by tracking tire compound on pit entry and tire compount on pit exit
* Damage = if time > average refuel time

Implement a flag, join data to driver table.