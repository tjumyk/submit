import json
import os

if __name__ == '__main__':
    print(json.dumps(os.listdir('.')))
