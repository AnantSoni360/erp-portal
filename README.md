# MMTPL – Store & Inventory Management ERP Portal

A modern, high-performance web-based Store and Inventory Management ERP Portal developed for **MMTPL**, digitizing the 21-sheet `MMTPL_Store_Tracker.xlsx` workbook into a centralized enterprise portal.

---

## Key Achievements & Parity Guarantee

* **100.00% Exact Reconciliation Parity:** All **849 materials** in the database match the original Excel workbook's calculated book balances down to the exact decimal.
* **100% Data Preservation:** All **19 contractor accounts** (within `C001`–`C020`), all **1,545 inward receipts**, and all **6,103 contractor issue/return records** migrated with full references and review notes preserved.
* **Dual-Condition Calculation Formula:**
  $$\text{Current Book Balance} = \sum \text{Valid Booked Inward} - \sum \text{Valid Posted Issues} + \sum \text{Valid Posted Returns}$$
  - *Valid Booked Inward:* $\text{Status} = \text{'Book'} \land \text{Check} = \text{'OK'}$
  - *Valid Posted Issue:* $\text{Status} = \text{'Posted'} \land \text{Check} = \text{'OK'}$
  - *Valid Posted Return:* $\text{Status} = \text{'Posted'} \land \text{Check} = \text{'OK'}$
  - *Quarantined:* Flagged transactions remain pending in the verification queue without affecting inventory balances.
* **Returnable Material Accounting:** Contractor liability is computed strictly on returnable materials ($\text{Outstanding Returnables} = \text{Returnable Issues} - \text{Returns}$); consumables are accounted as consumed.
* **Negative Stock Prevention:** Real-time stock threshold validation with authorized manager override and mandatory justification logging.
* **Material-Specific Welding Rod Conversion:** Automatic case conversion (5 packets/case for 6013 3.15 mm; 4 packets/case for standard rods).
* **Theme:** Executive **White & Royal Blue** (`#1D4ED8` / `#2563EB` / `#FFFFFF`) enterprise design system.

---

## 1-Click Launch (Windows)

Simply double-click:
```bat
start_portal.bat
```
Or run from PowerShell / Command Prompt:
```powershell
python run_portal.py
```
This automatically boots the FastAPI backend and launches the portal in your default web browser at **`http://127.0.0.1:8000`**.

---

## Seeded User Roles (Instant 1-Click Role Switcher)

The application includes pre-configured accounts with an instant role-switching dropdown in the top header:

| Role | Username | Password | Purpose & Capabilities |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full system control, materials catalog, user management, audit review |
| **Store Manager** | `manager` | `manager123` | Audit & Verification desk, transaction approvals, stock reconciliation, reports |
| **Store Employee** | `employee` | `employee123` | Store Inward receipts, Contractor Issue & Return recording |
| **Management** | `management` | `view123` | Executive dashboard, analytics, read-only audit ledgers and downloads |

---

## Functional ERP Modules

1. **Executive Dashboard (`/dashboard`):** Real-time physical inventory volume metrics, 9-category distribution charts, top contractor consumption charts, flagged queue alert box, and recent store movement ledger.
2. **Material Master Catalog (`/materials`):** 849 materials with fuzzy search, category filter, stock status badges (`OK`, `Reorder`, `Negative`), new material registration with opening stock support, and full chronological stock ledgers.
3. **Material Inward Desk (`/inward`):** 1,545 consignment records with auto-generated receipt IDs, duplicate detection, and booking status controls (`Book` vs `Flagged`).
4. **Issue & Return Desk (`/transactions`):** 6,103 contractor issue and return records with live stock availability verification, negative stock override guard, and returnable vs consumable tagging.
5. **Contractor Management (`/contractors`):** 19 contractor accounts (`C001`–`C020`) with individual itemized ledgers and outstanding returnable material tracking.
6. **Transaction Verification Queue (`/verification`):** Audit review desk for store managers to inspect flagged slips, assign missing item IDs, and approve or exclude transactions with recorded justification.
7. **Stock Reconciliation Explorer (`/reconciliation`):** Comparative ledger validating the mathematical proof $E - F + G$ side-by-side with the original Excel sheet.
8. **Reports & Analytics (`/reports`):** Formatted downloads of current stock ledgers, contractor consumption summaries, and audit logs in Excel (`.xlsx`) and PDF formats.
9. **Audit Trail (`/audit`):** Complete immutable log capturing who modified what, previous values, new values, reasons, and timestamps.

---

## Technology Stack

* **Frontend:** React 18, Vite, Tailwind CSS, Lucide React icons, Recharts SVG analytics.
* **Backend:** Python 3.12, FastAPI, Uvicorn ASGI server.
* **Database & ORM:** SQLite / PostgreSQL, SQLAlchemy 2.0.
* **Authentication:** JWT (JSON Web Tokens), Bcrypt password hashing.
* **Excel & PDF Processing:** OpenPyXL, Pandas, ReportLab.
* **Containerization:** Docker & Docker Compose (`docker-compose.yml`).
