# Project Title

SynthDataDash

## Description

Dash app that provides an input selection for dates and then outputs a scatter plot, a histogram, and summary statistics for the chosen time period. Also, there is an option to separate by stroke type. The input data source is synthetically generated data that simulates a tennis sensor.

## Getting Started

Select date range of interest and then scatter plot and histogram axes. You can also select stroke type. Changing any input will update the graph automatically.

### Dependencies

import warnings
import sqlite3
from datetime import date
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import wrangle # imports synthetic data from data folder

### Executing program

* How to run the program
* Step-by-step bullets
```
(.venv) python3 main.py
```

# Installing in python virtual environment (Debian/Ubuntu)

sudo apt install python3-full
sudo apt install python3-venv
sudo apt install python3-pip
python3 -m venv .venv
pip3 install {dependencies}

## Authors

blueaz

## Version History

* 0.1
    * Initial Release

## License

This project is licensed under the GNU License

