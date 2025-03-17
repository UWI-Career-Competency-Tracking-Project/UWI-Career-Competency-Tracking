import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from App import create_app

app = create_app()

if __name__ == '__main__':
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")
    app.run(debug=True)
