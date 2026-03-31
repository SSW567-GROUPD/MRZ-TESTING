# MRZ-TESTING
### Group D

---

## MRZ Format Reference (TD3 / Passport)

### Line 1 (44 characters)

| Field           | Positions | Length |
|-----------------|-----------|--------|
| Document type   | 1–2       | 2      |
| Issuing country | 3–5       | 3      |
| Name            | 6–44      | 39     |

Name format: `LASTNAME<<FIRSTNAME<MIDDLENAME`, padded with `<`.

### Line 2 (44 characters)

| Field                       | Positions | Length |
|-----------------------------|-----------|--------|
| Passport number             | 1–9       | 9      |
| Passport # check digit      | 10        | 1      |
| Country code                | 11–13     | 3      |
| Birth date (YYMMDD)         | 14–19     | 6      |
| Birth date check digit      | 20        | 1      |
| Sex                         | 21        | 1      |
| Expiration date (YYMMDD)    | 22–27     | 6      |
| Expiration date check digit | 28        | 1      |
| Personal number             | 29–43     | 15     |
| Personal # check digit      | 44        | 1      |

---

## Data Format Discrepancies

The performance testing files (`records_decoded.json` and `records_encoded.json`) do not directly match the input and output formats of the implemented functions. The differences are documented here so that anyone writing tests or integration code is aware of them.

---

### `getFromDB()` — return format

**What `records_decoded.json` looks like (one record):**
```json
{
  "line1": {
    "issuing_country": "CIV",
    "last_name": "LYNN",
    "given_name": "NEVEAH BRAM"
  },
  "line2": {
    "passport_number": "W620126G5",
    "country_code": "CIV",
    "birth_date": "591010",
    "sex": "F",
    "expiration_date": "970730",
    "personal_number": "AJ010215I"
  }
}
```

**What `getFromDB()` is currently assumed to return (flat dict):**
```json
{
  "issuing_country": "CIV",
  "last_name": "LYNN",
  "given_name": "NEVEAH BRAM",
  "passport_number": "W620126G5",
  "country_code": "CIV",
  "birth_date": "591010",
  "sex": "F",
  "expiration_date": "970730",
  "personal_number": "AJ010215I"
}
```

**Discrepancy:** `records_decoded.json` uses a nested structure with `line1` and `line2` sub-dicts. The current implementation assumes `getFromDB()` returns a flat dict with all fields at the top level. This is an unresolved assumption — see Decision 10 below.

---

### `encodeMRZ()` — return format

**What `records_encoded.json` looks like (one record):**
```
"P<CIVLYNN<<NEVEAH<BRAM<<<<<<<<<<<<<<<<<<<<<<;W620126G54CIV5910106F9707302AJ010215I<<<<<<6"
```
A single string with line 1 and line 2 joined by `;`.

**What `encodeMRZ()` currently returns:**
```python
("P<CIVLYNN<<NEVEAH<BRAM<<<<<<<<<<<<<<<<<<<<<<", "W620126G5...")
```
A tuple of two separate strings.

**Discrepancy:** The performance testing file uses a single semicolon-delimited string. The function returns a tuple. Any code that uses `encodeMRZ()` to produce output in the format of `records_encoded.json` must join the tuple with `;`.

---

### `scanMRZ()` — return format

**What `records_encoded.json` looks like (one record):**
```
"P<CIVLYNN<<NEVEAH<BRAM<<<<<<<<<<<<<<<<<<<<<<;W620126G54CIV5910106F9707302AJ010215I<<<<<<6"
```
A single semicolon-delimited string.

**What `scanMRZ()` is currently assumed to return:**
```python
("P<CIVLYNN<<NEVEAH<BRAM<<<<<<<<<<<<<<<<<<<<<<", "W620126G5...")
```
A tuple of two separate strings.

**Discrepancy:** If `records_encoded.json` is used as input to drive `decodeMRZ()` via a mock of `scanMRZ()`, each record must be split on `;` before being returned as a tuple.

---

### `decodeMRZ()` — return format

**What `records_decoded.json` looks like (one record):** Nested with `line1` and `line2` sub-dicts (see above).

**What `decodeMRZ()` currently returns:** A flat dict with all fields at the top level, plus a `check_digits` key not present in `records_decoded.json`.

**Discrepancy:** The return structure of `decodeMRZ()` does not match the structure of `records_decoded.json`. They share the same field names and values, but `decodeMRZ()` returns a flat dict while the file uses nested sub-dicts. Additionally, `decodeMRZ()` includes `check_digits` validation results that are not in the source file.

---

## Python Version

This project requires **Python 3.7.15**. See [Managing Python with Conda](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-python.html) for help switching versions.

---

## Decisions Log

The following decisions were made to resolve ambiguities in the original requirements.

| #   | Decision                     | Resolution                                                                                                                                                                                                                                                                                                                   |
| --- | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Fletcher-8 modulus           | No standard library exists for Fletcher-8; implementations vary. The modulus could be 15 (2⁴ − 1, mathematically correct for 4-bit accumulators) or 16 (simpler bitmasking). Group chose `% 15` as the more defensible interpretation. This affects every check digit result.                                                |
| 2   | Error handling approach      | Requirements do not specify behavior on invalid input. Decision: collect and return all errors in the result dict rather than raising an exception or stopping at the first failure. This applies to `decodeMRZ` and `encodeMRZ`.                                                                                            |
| 3   | Composite check digit        | The ICAO standard includes a composite check digit at position 44 of line 2, covering multiple fields. The assignment figure does not label this position as composite — it labels it as the personal number check digit. Group has assumed the composite check digit is therefore not implemented.                          |
| 4   | `encodeMRZ` data source      | The requirements specify that database interaction must be defined as a stub method (`getFromDB()`). `encodeMRZ()` therefore takes no parameter and calls `getFromDB()` internally. |
| 5   | Field naming                 | The test data file `records_decoded.json` uses `country_code` and `expiration_date` as key names. These are used throughout to ensure consistency between the data source and the implementation.                                                                                                                            |
| 6   | Name encoding/decoding       | In `records_decoded.json`, given names are space-separated (e.g. `"NEVEAH BRAM"`). In the MRZ string, names are `<`-separated with `<<` between last name and given name. `encodeMRZ` replaces spaces with `<`; `decodeMRZ` reverses this.                                                                                   |
| 7   | Document type                | The test data file `records_decoded.json` does not include a document type field. It is hardcoded as `P<` (standard passport) in `encodeMRZ` and not included in the `decodeMRZ` return value.                                                                                                                               |
| 8   | `getFromDB` record selection | The requirements do not specify how a specific record is selected from the database. `getFromDB()` takes no parameters, so record selection is the responsibility of the database layer. For unit testing, `getFromDB()` is mocked to return the desired record.                                                             |
| 9   | `decodeMRZ` data source      | The requirements specify that hardware scanning must be defined as a stub method (`scanMRZ()`). By the same reasoning as Decision 4, `decodeMRZ()` takes no parameter and calls `scanMRZ()` internally. For unit testing, `scanMRZ()` is mocked to return the desired input.                                                 |
| 10  | `getFromDB` return structure | `records_decoded.json` uses a nested structure with `line1` and `line2` sub-dicts. The current implementation assumes `getFromDB()` returns a flat dict with all fields at the top level. **This is unresolved.** The group must decide: does `getFromDB()` return the nested structure (matching the data file) or a flat dict (matching the current implementation)? `encodeMRZ()` must be updated accordingly. |
