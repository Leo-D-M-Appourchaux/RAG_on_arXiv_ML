# RAG_on_arXiv_ML
Polimi Group School Project



# Libraries
use requirements.txt to install the required libraries


**If you have the following error:
```conn.enable_load_extension(True)```

Careful with the sqlite extension on macos, you'll need sqlite3 from homebrew, then make sure to have a version of python based on the right sqlite3 installation (the one from homebrew), and finally your virtual environment need to be based on this python version.

Then you need to redo the steps, make sure to have sqlite3 from homebrew, reinstall a version of python and recreate a venv with this python version.**