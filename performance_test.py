import json
import time
import csv
from unittest.mock import patch
import MRTD

def encode_record(record):
    flat = {**record['line1'], **record['line2']}
    with patch('MRTD.getFromDB', return_value=flat):
        return MRTD.encodeMRZ()

def decode_and_check(line1, line2):
    with patch('MRTD.scanMRZ', return_value=(line1, line2)):
        decoded = MRTD.decodeMRZ()
    if 'errors' in decoded:
        return False
    for cd in decoded['check_digits'].values():
        if not cd['valid']:
            return False
    return True

def main():
    with open('records_decoded.json') as f:
        data = json.load(f)
    records = data['records_decoded']
    ks = list(range(1000, 10001, 1000)) + [100]  # 100,1000,...,10000
    ks.sort()
    results = []
    for k in ks:
        subset = records[:k]
        # without tests
        start = time.perf_counter()
        for record in subset:
            encode_record(record)
        time_no_tests = time.perf_counter() - start
        # with tests
        start = time.perf_counter()
        for record in subset:
            line1, line2 = encode_record(record)
            if not decode_and_check(line1, line2):
                print(f"Validation failed for record {subset.index(record)}")
        time_with_tests = time.perf_counter() - start
        results.append((k, time_no_tests, time_with_tests))
    with open('performance_results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['num_lines', 'exec_time_no_tests', 'exec_time_with_tests'])
        for row in results:
            writer.writerow(row)

if __name__ == '__main__':
    main()