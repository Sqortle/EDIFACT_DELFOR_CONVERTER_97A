# EDIFACT (DELFOR) to XML Converter

This Python script provides a robust object-oriented solution (`XMLConverter` class) for transforming raw **EDIFACT** messages, specifically those in the **DELFOR** (Delivery Forecast) standard, into a structured XML format. It utilizes the `xml.etree.ElementTree` library for efficient XML construction.

## Features

  * **EDIFACT Parsing:** Splits the raw EDIFACT string based on the segment terminator (`'`) and component separator (`+`).
  * **Segment Mapping:** Contains a dedicated `SegmentsClass` to map specific EDIFACT segments (e.g., `NAD`, `BGM`, `LIN`, `DTM`, `QTY`, `SCC`) and their qualified data elements to the correct XML tags.
  * **Header Extraction:** Performs an initial pass to extract top-level header information (`BGM`, `NAD`, `DTM`) and builds the XML header structure.
  * **Line Item Iteration:** Executes a second pass to iterate through line item segments (`LIN`, `SCC`, `QTY`, `DTM`) to build `<ARTICLE_LINE>` and `<SCHEDULE_LINE>` elements.
  * **Data Sanitation:** Includes a `sanitize` method to clean up raw EDIFACT data by removing newlines (`\n`, `\r`) and excess whitespace.
  * **Formatted Output:** Uses a custom `indent` utility function for generating clean, human-readable XML output.

-----

## Prerequisites

  * **Python 3:** The script is written in standard Python 3 and requires no external libraries beyond the built-in `xml.etree.ElementTree`.

## How to Use

### 1\. File Setup

1.  Save the Python code as a file (e.g., `delfor97a.py`).

2.  Your raw EDIFACT message must be placed within the `edifact_message` multiline string at the end of the script:

    ```python
    edifact_message = """
    # Paste your raw EDIFACT content here, e.g.:
    UNB+...
    BGM+...
    NAD+...
    LIN+...
    QTY+3:4331'
    SCC+4'
    DTM+158:20251010:102'
    """
    ```

### 2\. Execution

Run the script from your terminal:

```bash
python3 edifact_converter.py
```

### 3\. Output

The script will generate a single XML file named **`delforoutput.xml`** in the same directory where you run the script. The output uses `ISO-8859-1` encoding.

-----

## Key Classes and Methods

### `XMLConverter` Class

This is the main driver class responsible for the overall conversion process.

| Method | Description |
| :--- | :--- |
| `__init__` | Initializes the converter, stores the message, initializes `SegmentsClass`, and starts the `convert` process. |
| `sanitize(text)` | Cleans input text by stripping whitespace and removing newlines. |
| `safe_split_component(component)` | Safely splits a component (e.g., `CODE:VALUE`) into its identifier and value parts. |
| `indent(elem, level)` | Recursively applies indentation to the generated `ElementTree` for clean XML formatting. |
| `convert(edifact_message)` | Manages the two-pass iteration over segments to construct the final XML tree. |

### `SegmentsClass` Class

This class groups functions for handling the detailed mapping of individual EDIFACT segments to specific XML tags.

| Function | EDIFACT Segment | Purpose |
| :--- | :--- | :--- |
| `NADfunction` | `NAD` (Name and Address) | Extracts `VENDOR_NO` (Qualifier `SU`) and `SHIP_FROM` (Qualifier `SF`). |
| `BGMfunction` | `BGM` (Beginning of Message) | Extracts the document's `MESSAGE_ID`. |
| `DTMfunction` | `DTM` (Date/Time/Period) | Maps various date qualifiers (e.g., `137`, `159`, `158`, `11`) to corresponding XML date tags (`VALID_FROM`, `VALID_UNTIL`, `DELIVERY_DUE_DATE`, `LAST_RECEIPT_DATE`). |
| `RFFfunction` | `RFF` (Reference) | Extracts the `SUPPLIER_REF`. |
| `QTYfunction` | `QTY` (Quantity) | Maps quantity qualifiers (e.g., `79` for last receipt, `3` for cumulative demand) to the appropriate quantity XML tags. |
| `LINfunction` | `LIN` (Line Item) | Creates a new `<ARTICLE_LINE>`, assigns a sequential `SCHEDULE_NO`, and extracts the `EAN_CODE`. |
| `SCCfunction` | `SCC` (Scheduling Conditions) | Creates a new `<SCHEDULE_LINE>` (when qualifier is `4`) and initializes it with line-level data (`DOCK_CODE`, `CUSTOMER_PO_NO`). |
