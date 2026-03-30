# MRTD.py
# Group D — Fletcher 8
#
# Implements the four MRZ system requirements:
#   Req 1: scanMRZ()         — hardware stub
#   Req 2: decodeMRZ()       — decode MRZ strings into fields, validate check digits
#   Req 3: getFromDB()       — database stub (called internally by encodeMRZ)
#          encodeMRZ()       — encode document fields into MRZ strings
#   Req 4: reportMismatches() — report all check digit mismatches
#
# Fletcher-8 algorithm:
#   Two 4-bit accumulators (A, B), modulus 15 (2^4 - 1).
#   Character values: '0'-'9' -> 0-9, 'A'-'Z' -> 10-35, '<' -> 0
#   check_digit = ((B << 4) | A) % 10
#   This is the group's chosen interpretation of the standard Fletcher-8 algorithm.
#
# MRZ format (TD3 / Passport):
#   Line 1 (44 chars): [doc_type:2][issuing_country:3][name:39]
#   Line 2 (44 chars): [passport_number:9][cd:1][country_code:3]
#                      [birth_date:6][cd:1][sex:1][expiration_date:6][cd:1]
#                      [personal_number:15][cd:1]
#   Positions are 1-indexed in spec; 0-indexed in this implementation.
#   There is no composite check digit — position 44 is the personal number check digit.


# ---------------------------------------------------------------------------
# Private helper
# ---------------------------------------------------------------------------

def _fletcher8_check_digit(field):
    """
    Compute the Fletcher-8 check digit for a given MRZ field string.

    Uses two 4-bit accumulators with modulus 15 (2^4 - 1).
    Character value mapping:
        '0'-'9'  ->  0-9
        'A'-'Z'  ->  10-35
        '<'      ->  0

    Returns the check digit as an integer (0-9).
    """
    A = 0
    B = 0
    for char in field:
        if char.isdigit():
            value = int(char)
        elif char.isalpha():
            value = ord(char.upper()) - ord('A') + 10
        else:
            value = 0  # '<' and any other filler
        A = (A + value) % 15
        B = (B + A) % 15
    checksum_byte = (B << 4) | A
    return checksum_byte % 10


# ---------------------------------------------------------------------------
# Requirement 1 — Hardware stub
# ---------------------------------------------------------------------------

def scanMRZ():
    """
    Stub representing the hardware MRZ scanner interface.

    Returns a tuple of (line1, line2), each a 44-character MRZ string.
    Hardware implementation is not in scope; this method exists as a
    mockable interface for testing purposes.

    Returns:
        tuple: (line1, line2) — two 44-character MRZ strings
    """
    pass


# ---------------------------------------------------------------------------
# Requirement 3 — Database stub (called internally by encodeMRZ)
# ---------------------------------------------------------------------------

def getFromDB():
    """
    Stub representing the database interface for retrieving document fields.

    Returns a dictionary of travel document fields matching the structure
    of records_decoded.json. Record selection is the responsibility of the
    database layer; this stub exists as a mockable interface for testing.

    Note: Requirements do not specify how a specific record is selected.
    For unit testing, this function is mocked to return a desired record.

    Returns:
        dict with keys: issuing_country, last_name, given_name,
                        passport_number, country_code, birth_date,
                        sex, expiration_date, personal_number
    """
    pass


# ---------------------------------------------------------------------------
# Requirement 2 — Decode
# ---------------------------------------------------------------------------

def decodeMRZ():
    """
    Decode MRZ strings into structured fields and validate check digits
    using the Fletcher-8 algorithm.

    Calls scanMRZ() internally to retrieve the two MRZ strings.
    For unit testing, mock scanMRZ() to supply the desired input.

    Collects all errors and validation failures — does not stop at the first
    problem encountered.

    Returns:
        dict with keys:
            issuing_country (str)
            last_name (str)
            given_name (str)       — space-separated given names
            passport_number (str)
            country_code (str)
            birth_date (str)       — YYMMDD
            sex (str)
            expiration_date (str)  — YYMMDD
            personal_number (str)
            check_digits (dict)    — per-field validation results
            errors (list)          — present only if input errors were found
    """
    scanned = scanMRZ()

    if scanned is None:
        return {"errors": [{"field": "scanMRZ", "error": "No data returned from scanner"}]}

    line1, line2 = scanned
    errors = []

    # Validate input lengths
    if len(line1) != 44:
        errors.append({
            "field": "line1",
            "error": "Expected 44 characters, got {}".format(len(line1))
        })
    if len(line2) != 44:
        errors.append({
            "field": "line2",
            "error": "Expected 44 characters, got {}".format(len(line2))
        })

    if errors:
        return {"errors": errors}

    # --- Parse line 1 ---
    # Positions (1-indexed): doc_type[1-2], issuing_country[3-5], name[6-44]
    issuing_country = line1[2:5].rstrip('<')

    name_field = line1[5:44]
    name_parts = name_field.split('<<')
    last_name = name_parts[0].replace('<', ' ').strip()
    if len(name_parts) > 1:
        given_name = name_parts[1].rstrip('<').replace('<', ' ').strip()
    else:
        given_name = ''

    # --- Parse line 2 ---
    # Positions (1-indexed):
    #   passport_number[1-9], cd[10], country_code[11-13],
    #   birth_date[14-19], cd[20], sex[21],
    #   expiration_date[22-27], cd[28],
    #   personal_number[29-43], cd[44]

    passport_number_raw = line2[0:9]
    passport_cd_extracted = int(line2[9]) if line2[9].isdigit() else None

    country_code = line2[10:13].rstrip('<')

    birth_date = line2[13:19]
    birth_cd_extracted = int(line2[19]) if line2[19].isdigit() else None

    sex = line2[20]

    expiration_date = line2[21:27]
    expiration_cd_extracted = int(line2[27]) if line2[27].isdigit() else None

    personal_number_raw = line2[28:43]
    personal_cd_extracted = int(line2[43]) if line2[43].isdigit() else None

    # Strip filler from variable-length fields
    passport_number = passport_number_raw.rstrip('<')
    personal_number = personal_number_raw.rstrip('<')

    # --- Validate check digits ---
    passport_cd_computed = _fletcher8_check_digit(passport_number_raw)
    birth_cd_computed = _fletcher8_check_digit(birth_date)
    expiration_cd_computed = _fletcher8_check_digit(expiration_date)
    personal_cd_computed = _fletcher8_check_digit(personal_number_raw)

    check_digits = {
        "passport_number": {
            "extracted": passport_cd_extracted,
            "computed": passport_cd_computed,
            "valid": passport_cd_extracted == passport_cd_computed
        },
        "birth_date": {
            "extracted": birth_cd_extracted,
            "computed": birth_cd_computed,
            "valid": birth_cd_extracted == birth_cd_computed
        },
        "expiration_date": {
            "extracted": expiration_cd_extracted,
            "computed": expiration_cd_computed,
            "valid": expiration_cd_extracted == expiration_cd_computed
        },
        "personal_number": {
            "extracted": personal_cd_extracted,
            "computed": personal_cd_computed,
            "valid": personal_cd_extracted == personal_cd_computed
        }
    }

    result = {
        "issuing_country": issuing_country,
        "last_name": last_name,
        "given_name": given_name,
        "passport_number": passport_number,
        "country_code": country_code,
        "birth_date": birth_date,
        "sex": sex,
        "expiration_date": expiration_date,
        "personal_number": personal_number,
        "check_digits": check_digits
    }

    if errors:
        result["errors"] = errors

    return result


# ---------------------------------------------------------------------------
# Requirement 3 — Encode
# ---------------------------------------------------------------------------

def encodeMRZ():
    """
    Encode travel document fields from the database into two MRZ strings.

    Calls getFromDB() internally to retrieve the document fields.
    Computes and inserts check digits using the Fletcher-8 algorithm.
    Document type is hardcoded as 'P<' (not present in source data).

    For unit testing, mock getFromDB() to supply the desired input record.

    Returns:
        tuple: (line1, line2) — two 44-character MRZ strings
               If getFromDB() returns None, returns a dict with an errors list.
    """
    fields = getFromDB()

    if fields is None:
        return {"errors": [{"field": "getFromDB", "error": "No data returned from database"}]}

    # --- Build line 1 ---
    doc_type = 'P<'

    issuing_country = fields.get('issuing_country', '')
    issuing_country_padded = (issuing_country + '<<<')[:3]

    last_name = fields.get('last_name', '')
    given_name = fields.get('given_name', '')
    given_name_encoded = given_name.replace(' ', '<')
    name_field = last_name + '<<' + given_name_encoded
    name_field_padded = (name_field + '<' * 39)[:39]

    line1 = doc_type + issuing_country_padded + name_field_padded

    # --- Build line 2 ---
    passport_number = fields.get('passport_number', '')
    passport_number_padded = (passport_number + '<' * 9)[:9]
    passport_cd = str(_fletcher8_check_digit(passport_number_padded))

    country_code = fields.get('country_code', '')
    country_code_padded = (country_code + '<<<')[:3]

    birth_date = fields.get('birth_date', '')
    birth_date_padded = (birth_date + '000000')[:6]
    birth_cd = str(_fletcher8_check_digit(birth_date_padded))

    sex = fields.get('sex', '<')
    sex_char = sex[0] if sex else '<'

    expiration_date = fields.get('expiration_date', '')
    expiration_date_padded = (expiration_date + '000000')[:6]
    expiration_cd = str(_fletcher8_check_digit(expiration_date_padded))

    personal_number = fields.get('personal_number', '')
    personal_number_padded = (personal_number + '<' * 15)[:15]
    personal_cd = str(_fletcher8_check_digit(personal_number_padded))

    line2 = (passport_number_padded + passport_cd +
             country_code_padded +
             birth_date_padded + birth_cd +
             sex_char +
             expiration_date_padded + expiration_cd +
             personal_number_padded + personal_cd)

    return (line1, line2)


# ---------------------------------------------------------------------------
# Requirement 4 — Report mismatches
# ---------------------------------------------------------------------------

def reportMismatches(decoded):
    """
    Report all check digit mismatches from a decoded MRZ record.

    Always runs to completion — collects all mismatches before returning.

    Args:
        decoded (dict): The dictionary returned by decodeMRZ()

    Returns:
        list: One dict per mismatch, each containing:
                field (str)                  — name of the mismatched field
                extracted_check_digit (int)  — check digit found in the MRZ string
                computed_check_digit (int)   — check digit computed by Fletcher-8
              Empty list if all check digits are valid.
    """
    mismatches = []

    check_digits = decoded.get('check_digits', {})

    for field, cd_info in check_digits.items():
        if not cd_info.get('valid', True):
            mismatches.append({
                'field': field,
                'extracted_check_digit': cd_info['extracted'],
                'computed_check_digit': cd_info['computed']
            })

    return mismatches
