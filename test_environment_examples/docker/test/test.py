import json
import os

if __name__ == '__main__':
    print(json.dumps(os.listdir('.')))
    result_tag = os.getenv('RESULT_TAG', '')
    print(result_tag + ' good')
