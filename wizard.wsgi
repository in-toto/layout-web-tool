activate_this = "~/.virtualenvs/wizard/bin/activate_this.py"
execfile(activate_this, dict(__file__=activate_this))
import sys
sys.path.insert(0, "~/wizard")
from wizard import app as application
