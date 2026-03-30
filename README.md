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

## Python Version

This project requires **Python 3.7.15**. See [Managing Python with Conda](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-python.html) for help switching versions.

---

## Decisions Log

The following decisions were made to resolve ambiguities in the original requirements.

| # | Decision | Resolution |
|---|----------|------------|
| 1 | Fletcher-8 modulus | `% 15` (two 4-bit accumulators, standard Fletcher-8) — group's chosen interpretation, documented in code |
| 2 | Error handling approach | Collect and return all errors; never stop at first failure |
| 3 | Composite check digit | Does not exist per assignment figure; position 44 of line 2 is the personal number check digit |
| 4 | `encodeMRZ` data source | `encodeMRZ()` takes no parameter; calls `getFromDB()` internally |
| 5 | Field naming | Use `country_code` and `expiration_date` to match `records_decoded.json` key names |
| 6 | Name encoding/decoding | `given_name` is space-separated in source data; encode by replacing spaces with `<` and joining with `<<` after last name; reverse on decode |
| 7 | Document type | Not present in source data; hardcoded as `P<` in `encodeMRZ`; stripped from decoded output |
| 8 | `getFromDB` record selection | Requirements do not specify how a specific record is selected. `getFromDB()` takes no parameters; record selection is the database layer's responsibility. For unit testing, `getFromDB()` is mocked to return the desired record. |
| 9 | `decodeMRZ` data source | `decodeMRZ()` takes no parameter; calls `scanMRZ()` internally, mirroring the same pattern as `encodeMRZ`/`getFromDB`. For unit testing, `scanMRZ()` is mocked to return the desired input. |
