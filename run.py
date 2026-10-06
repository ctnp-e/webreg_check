import os
import sys

# Run from this file's directory so .env and classes.txt are always found here
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "uci"))

import discord_bot
