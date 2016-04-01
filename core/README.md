# ladder Core API

The core API contains all the low-level functionality such as adding/editing/deleting matches, players, etc.
This will also contain all the analytics and rating calculations.


## Usage
For testing purposes, run `python load_fake_data.py` to fill up database with data. This will fail if there are
already contents in the database collections specified unless the `--force` flag is used.