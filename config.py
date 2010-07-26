#!/usr/bin/env python
#----------------------------------------------------------------------------
# (c) Rob Hague 2010 rob@rho.org.uk
#----------------------------------------------------------------------------

import os, os.path

# Login
login = os.getlogin()
password = "passw0rd"

# Override configuration with a user file, if present
try:
    execfile(os.path.expanduser('~/.worksheet.py'))
except:
    pass

