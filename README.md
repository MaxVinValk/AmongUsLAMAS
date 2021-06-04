# Dependencies

Our code was tested with `python3` on ubuntu. The following python packages should be installed (all are available from pip):

 - `pygame`
 - `numpy`
 - `graphviz`

The third package `graphviz` is a python wrapper for the Graphviz library, which should be installed separately, e.g.:

``` bash
sudo apt install graphviz
```

The code also depends on [mlsolver](https://github.com/erohkohl/mlsolver) which is included in the repository. 

# Setup an running

After cloning the repository no additional setup is required. The simulation can be ran by executing

```bash
python3 main.py
```

This should show the `pygame` interface. To go to the next turn press `space`. To view more information, click the agents or toggle to the Kripke model pane. 
