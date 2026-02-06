# How Multiple Plaintiffs and Defendants Are Handled

This document summarizes how the preview service formats **multiple plaintiffs** and **multiple defendants** so the output matches templates like **Premises - 1 plt. and 1deft** and real documents like **Sarante, Esther - Summons & Complaint**.

## Templates in this project (same conventions)

The templates under **`backend/templates/`** use the same multi-party formatting:

| File | Notes |
|------|--------|
| **Sarante, Esther - Summons & Complaint.doc** | Example summons/complaint; same “and” rules as below. |
| **Premises - 1 plt. and 1deft_.docx** | Referenced in DB seed as `templates/Premises - 1 plt. and 1deft_.docx`; same conventions. |
| **MVA - 1 plt. and 1 deft_.docx**, **Medical Malpractice - 1 plt. and 1 deft_.docx** | Same layout when present. |

Names and defendant addresses both use the same rule: **no commas**, **“and” on its own line** between each party’s value. Names: `"Name1 and\nName2 and\nName3"`. Addresses: each field (street, city, state, zip) = `"line1 and\nline2 and\nline3"` for 2+ defendants. Matches the template.

---

## 1. What the Code Does Today

### Party names (caption: “Plaintiffs” / “Defendants”)

Used for merge fields **`«Plaintiff_name_»`** and **`«Defendant_name»`**.

| # of parties | Format | Example |
|--------------|--------|---------|
| **1** | Single name | `Jane Doe` |
| **2** | Newline + “and” + newline between each (same as addresses) | `Jane Doe`<br>`and`<br>`John Doe` |
| **3+** | Same: “and” on its own line between every name—**no commas** | `Jane Doe`<br>`and`<br>`John Doe`<br>`and`<br>`Bob Smith` |

So for **2+ parties** we use **“Name1\nand\nName2\nand\nName3”** (the word “and” on its own line between each name), matching the template. No commas.

### Defendant merge fields (same way as original template)

Defendants are **fetched from the DB** and written into **per-defendant** merge fields (defendant1_name, defendant1_street_address_, defendant1_city, defendant1_state, defendant1_zip_code, defendant1_county, and defendant2_*, …) using the template’s own placeholder names from template.fields. Each slot gets one defendant’s data; no replacing with a single concatenated field.

| # of defendants | Format | Example (streets) |
|-----------------|--------|-------------------|
| **1** | Single value | `123 Main St` |
| **2+** | **Same rule as names**: newline + “and” + newline between each value (no commas) | `123 Main St`<br>`and`<br>`456 Oak Ave` |

Names and addresses use **one shared join** (`\nand\n`) in the code, so **everything follows the same way**. Example (street): **“123 Main St\nand\n456 Oak Ave\nand\n789 Pine Rd”**. City, state, and zip use the same pattern per field. Matches the template.

### Plaintiffs – addresses

Right now only **`«Plaintiff_name_»`** is filled from the plaintiffs table.  
If your template has plaintiff address placeholders (e.g. `Plaintiff_Street_Address_`, `Plaintiff_City`, etc.), the same “line1\nand\nline2” style can be added for multiple plaintiffs in the same way as defendants.

---

## 2. How This Fits “Premises - 1 plt. and 1deft” and Sarante

- **“Premises - 1 plt. and 1deft”**  
  Built for one plaintiff and one defendant. When you **add a second defendant** (or second plaintiff) in the UI:
  - **Names** are merged as **“First Name and\nSecond Name”** into `Plaintiff_name_` or `Defendant_name`.
  - **Defendant addresses** are merged as **“Address1\nand\nAddress2”** (and same for city/state/zip) into the existing defendant placeholders.

- **Sarante, Esther - Summons & Complaint**  
  Use it to check:
  1. **Caption** – Is “and” between two party names on a new line, or on the same line?
  2. **Address block** – When there are two defendants, does the document put “and” on its own line between the two full address blocks, or between each component (street, then city, etc.)?

Our current logic does **“and” on its own line** for both names and for each address component. If Sarante uses a different pattern (e.g. “A and B” on one line, or one “and” between full blocks), we can adjust the formatters in `preview_service.py` to match.

---

## 3. How the HTML (preview_editor) Deals With It

**`backend/templates/html/preview_editor.html`** handles multiple plaintiffs/defendants like this:

1. **List view**  
   Each party is shown as its own card: “Plaintiff #1”, “Plaintiff #2”, “Defendant #1”, etc.  
   Order matches the document: the backend uses `index` (1, 2, 3…) when building “Name1 and Name2” and “line1 and line2”.

2. **Add**  
   “+ Add Plaintiff” / “+ Add Defendant” opens a form (Name, Address, City, State, Zip, County).  
   On Save → `POST /api/v1/sessions/{uuid}/plaintiffs` or `.../defendants` → new row in DB with next `index` → list refetched → preview regenerated.  
   The **“and” formatting is not done in the HTML**; it’s done when the preview DOCX is built (see §1–2).

3. **Edit / Delete**  
   Per-card Edit rewrites that party’s fields; Delete removes the row.  
   After any change, the UI refetches the party list and calls `POST .../preview/regenerate`, then reloads the DOCX preview.  
   Again, “Name1 and\\nName2” and “line1\\nand\\nline2” are applied only in the preview service, not in the HTML.

4. **Data flow**  
   - Initial data: server renders `plaintiffs` and `defendants` (from DB) into the page as `initialPlaintiffs` / `initialDefendants`, and the script renders the cards.  
   - All create/update/delete goes through the REST API; the HTML only displays the list and triggers regenerate.  
   So the HTML “deals with” multiple parties by **listing them in order** and **sending each party’s fields to the API**; the document text (“and” between names/addresses) is entirely determined by `preview_service.py`.

---

## 4. Where It’s Implemented (code)

- **Names (plaintiffs and defendants)**  
  `backend/app/services/preview_service.py`  
  - `_format_party_names_multi(...)`  
  - Used for `Plaintiff_name_` and `Defendant_name`.

- **Defendant addresses**  
  Same file:  
  - `_format_address_components_multi(defendants)`  
  - Fills `Defendant_Street_Address_`, `Defendant_City`, `Defendant_State`, `Defendant_Zip_code`.

- **UI**  
  `backend/templates/html/preview_editor.html`:  
  - “+ Add Plaintiff” / “+ Add Defendant”  
  - Each party: name, address, city, state, zip, county; Edit/Delete.  
  - Saving adds/updates/deletes via API and regenerates the preview; “and” rules are applied in the preview service, not in the HTML.

---

## 5. What to Check in Your Two Documents

When you open **Sarante, Esther - Summons & Complaint** and **Premises - 1 plt. and 1deft**:

1. **Caption (multiple defendants)**  
   - Exact layout: e.g. “DEFENDANT A and DEFENDANT B” vs “DEFENDANT A” / “and” / “DEFENDANT B”.
2. **Caption (multiple plaintiffs)**  
   - Same question for plaintiffs.
3. **Address block (2 defendants)**  
   - One “and” between two full blocks vs “and” between each line (street, city, state, zip).

Once you have that, we can match `_format_party_names_multi` and `_format_address_components_multi` to your templates and the Sarante doc exactly.
