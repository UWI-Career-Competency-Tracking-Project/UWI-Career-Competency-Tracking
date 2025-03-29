import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from App import create_app

app = create_app('development')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")
        
    app.run(debug=True)
