# Dependencies

Our code was tested with `python3` on Ubuntu and MacOS.
Various python packages where used that can be obtained via pip. For the exact programs, see [the requirements file](requirements.txt).

Additionally, the `graphviz` package is a python wrapper for the Graphviz library, which should be installed separately, e.g.:

``` bash
sudo apt install graphviz
```

The code builds on [mlsolver](https://github.com/erohkohl/mlsolver) which is included in the repository. Note that an altered version is used, which was based on [the work of previous students of Logical Aspects of Multi-Agent Systems](https://github.com/JohnRoyale/MAS2018), in particular their implementation of the knowledge operator within the mlsolver framework.

# Setup and running

After cloning the repository, installing the packages and the Graphviz library, no additional setup is required. The simulation can be ran by executing

```bash
python3 main.py
```

This should show the `pygame` interface. The buttons on the right of the simulation act as simulation controls. In addition, the spacebar can be used to progress the simulation by one step. To view more information, click the agents or toggle to the Kripke model button, which will show a rendition of the current Kripke model.

# Command Line Arguments
When launching the simulation without command line arguments, default parameters are used for various variables. If one wishes to change these, this can be done with the following commands:

- --headless: Toggles headless mode. In headless mode, the pygame window is not shown and the simulation is run for a set amount of steps instead, after which a log file is produced from which data can be extracted.
 - --num_steps INT: If the program is executed in headless mode, this argument sets the amount of simulated full runs should be performed.
 - log_name STRING: If the program is executed in headless mode, one can specify the name of the log file that gets created. Note that this is optional, and not setting a name will result in a date-time stamped log instead.
- --num_crew INT: The number of crewmates
- --num_tasks INT: Sets the number of tasks that each agent has to complete for a win
- --visuals: Sets the number of tasks that are visual tasks, which can be seen by others when they are performed
- --num_imp INT: The number of impostors. Currently only 1 and 2 are supported.
- --cooldown INT: How many ACT steps must pass before the impostor can kill (again)
- --stat_thres FLOAT: A threshold which determines how likely it is for an impostor to remain in a room instead of moving to an adjacent room. A value of 0.2 represents a 20\% chance of remaining in the same room.

# Program and file structure
The simulation is launched from main.py, which creates an instance of the controller class. This class controls the simulation flow. This controller is given the map and information on the agents. If the simulation is running in visual mode, several panes are created for displaying game information.

### Folders
#### GUI
Contains various GUI elements such as text boxes and the tab manager.
#### mlsolver
Contains the mlsolver code (source mentioned in dependencies), adapted by us.
#### util
Provides an abstract base class for message passing as well as a file containing scripts for extracting information from a plot.

### home directory
#### Agent.py
Contains all logic regarding the behaviour of all types of agents.
#### controller.py
Contains the logic for the simulation flow.
#### logger.py
Contains a class responsible for the gathering and displaying of information collected during a run.
#### main.py
The entry-point of the program.
#### map.py
Contains all functionality with regards to maps, such as navigation, as well as the specific map used during the simulation.
#### pane.py
Contains functionality with regards to displaying the simulation.
#### room_events.py
Contains a basic class detailing the form of events, that can be seen by agents in the same room as the event.
#### task.py
Contains a basic class detailing the structure of a task.
