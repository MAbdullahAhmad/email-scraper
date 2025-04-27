import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from core.util.functions.env import env

app_config = {

  # Debug
  "debug": env("DEBUG", False),

}
