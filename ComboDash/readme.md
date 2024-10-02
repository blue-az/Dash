# Project Title

ComboViz

## Description

Combined dashboard and CalMatch using ChatGPT

## Getting Started

query = """
    SELECT _id, date, TYPE, TRACKID, ENDTIME, CAL, AVGHR, MAX_HR from TRACKRECORD
    """

### Dependencies

import warnings
import base64
import io
from datetime import date
import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from dash import Dash, Input, Output, dcc, html, callback, dash_table
import plotly.express as px
import plotly.graph_objects as go

* Downloads data from MiiFit dataframe

### Executing program

* How to run the program
* Step-by-step bullets
```
python3 main.py
```

## Authors

blueaz

## Version History

* 0.2
    * Various bug fixes and optimizations
* 0.1
    * Initial Release

## License

This project is licensed under the [NAME HERE] License - see the LICENSE.md file for details

## Acknowledgments

Inspiration, code snippets, etc.
* [awesome-readme](https://github.com/matiassingers/awesome-readme)
* [PurpleBooth](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)
* [dbader](https://github.com/dbader/readme-template)
* [zenorocha](https://gist.github.com/zenorocha/4526327)
* [fvcproductions](https://gist.github.com/fvcproductions/1bfc2d4aecb01a834b46)
