activate_this = "~/.virtualenvs/in-toto-layout/bin/activate_this.py"
execfile(activate_this, dict(__file__=activate_this))
import sys
sys.path.insert(0, "~/layout-web-tool")
from layout_tool import app as application
