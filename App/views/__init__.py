# blue prints are imported 
# explicitly instead of using *
from .index import index_views
from .auth import auth    
from .dashboard import dashboard_views
from .main import main_views

views = [index_views, auth, dashboard_views, main_views] 
# blueprints must be added to this list