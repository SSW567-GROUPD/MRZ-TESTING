import json
from unittest.mock import patch
import MRTD

def main():
    with open('records_decoded.json') as f:
        data = json.load(f)
    records = data['records_decoded']
    encoded = []
    for record in records:
        flat = {**record['line1'], **record['line2']}
        with patch('MRTD.getFromDB', return_value=flat):
            line1, line2 = MRTD.encodeMRZ()
        encoded.append(line1 + ';' + line2)
    with open('records_encoded.json', 'w') as f:
        json.dump({'records_encoded': encoded}, f, indent=2)

if __name__ == '__main__':
    main()