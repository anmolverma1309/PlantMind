# Step 2 — Sample Document Corpus

## Objective
Create a realistic set of 8-10 sample industrial documents that will exercise every ingestion pathway (PDF text, scanned images, P&ID drawings, CSV data, regulatory text). Also define 15 ground-truth facts for evaluation benchmarking.

---

## 2.1 Corpus Design

We need documents that **cross-reference each other** so the knowledge graph can demonstrate cross-document insights. All documents reference a fictional refinery: **"Coastal Refinery Unit-3"**.

### Shared entities across documents (critical for cross-document queries):
| Entity | Type | Appears In |
|--------|------|-----------|
| Pump P-104 | Equipment | Work orders, maintenance report, P&ID, inspection form |
| Heat Exchanger HX-201 | Equipment | Safety procedure, work orders, P&ID |
| Compressor C-302 | Equipment | Incident report, work orders, lessons-learned |
| Valve V-045 | Equipment | P&ID, safety procedure, inspection form |
| OISD-STD-154 | Regulation | Compliance doc, safety procedure |
| John Patel | Person | Work orders, inspection form |
| Seal Failure | Failure Mode | Maintenance report, incident report |

---

## 2.2 Document Specifications

Create each document as specified. **Every file goes under `plantmind/data/sample_docs/`.**

---

### Document 1: `maintenance/work_orders.csv`
**Type:** CSV (structured data)
**Purpose:** Tests CSV parser

```csv
wo_id,date,equipment_tag,equipment_name,description,assigned_to,status,priority,hours_spent,failure_mode,root_cause
WO-2024-001,2024-01-15,P-104,Centrifugal Pump P-104,Excessive vibration detected during routine check. Bearing replacement required.,John Patel,Completed,High,6.5,Bearing Failure,Worn bearing due to misalignment
WO-2024-002,2024-02-03,HX-201,Shell & Tube Heat Exchanger HX-201,Tube bundle fouling causing reduced heat transfer. Chemical cleaning scheduled.,Sarah Khan,Completed,Medium,12.0,Fouling,Scale buildup from cooling water
WO-2024-003,2024-03-10,C-302,Reciprocating Compressor C-302,Seal leak detected on discharge side. Emergency repair.,Raj Mehta,Completed,Critical,8.0,Seal Failure,Worn mechanical seal — exceeded MTBF
WO-2024-004,2024-03-22,P-104,Centrifugal Pump P-104,Follow-up vibration analysis post-bearing replacement. Within acceptable limits.,John Patel,Completed,Low,2.0,None,Preventive check
WO-2024-005,2024-04-05,V-045,Gate Valve V-045,Valve stem packing leak during pressure test. Repacked.,John Patel,Completed,Medium,3.5,Packing Leak,Degraded packing material
WO-2024-006,2024-05-18,C-302,Reciprocating Compressor C-302,Second seal failure in 3 months. Full mechanical seal assembly replaced.,Raj Mehta,Completed,Critical,14.0,Seal Failure,Repeated seal failure — investigate alignment and operating conditions
WO-2024-007,2024-06-01,HX-201,Shell & Tube Heat Exchanger HX-201,Annual inspection and hydro test. Minor corrosion noted on shell side.,Sarah Khan,In Progress,Medium,8.0,Corrosion,Age-related material degradation
WO-2024-008,2024-06-15,P-104,Centrifugal Pump P-104,Vibration alarm triggered again. Coupling misalignment suspected.,John Patel,Open,High,0.0,Vibration,Pending investigation
```

---

### Document 2: `maintenance/maintenance_report_P104.pdf`
**Type:** PDF (text-based)
**Purpose:** Tests PDF text extractor

Create this as a text file first, then convert to PDF (or create directly). Content:

```
MAINTENANCE REPORT
==================
Equipment: Centrifugal Pump P-104
Location: Coastal Refinery Unit-3, Area A
Report Date: 2024-04-15
Prepared By: John Patel, Senior Maintenance Technician

1. SUMMARY
-----------
Pump P-104 has experienced recurring vibration issues over the past quarter. 
Two work orders (WO-2024-001 and WO-2024-008) were raised for excessive 
vibration. Root cause analysis indicates coupling misalignment between the 
pump and its driver motor, compounded by a history of bearing wear.

2. EQUIPMENT HISTORY
---------------------
- Commissioned: 2018
- Service: Crude transfer from Tank Farm to Distillation Column DC-01
- Operating Parameters: 150 m³/hr flow, 12 bar discharge pressure
- Maintenance Frequency: Quarterly vibration monitoring, annual overhaul

3. FAILURE ANALYSIS
--------------------
Date        | Issue                | Root Cause
2024-01-15  | Excessive vibration  | Worn bearing (misalignment-induced)
2024-03-22  | Follow-up check      | Vibration within limits post-repair
2024-06-15  | Vibration alarm      | Coupling misalignment (recurring)

The recurring pattern suggests the base frame may have shifted due to 
thermal expansion effects during summer operation. Recommend laser 
alignment check and base frame survey.

4. RECOMMENDATIONS
-------------------
a) Perform laser alignment of pump-motor coupling (Priority: HIGH)
b) Commission base frame leveling survey
c) Increase vibration monitoring frequency from quarterly to monthly
d) Consider upgrading to flexible coupling to tolerate minor misalignment

5. SAFETY NOTES
----------------
All maintenance performed per SOP-MAINT-012 (Rotating Equipment Maintenance 
Procedure). Lockout/Tagout verified per OISD-STD-154 requirements.

6. REGULATORY COMPLIANCE
--------------------------
Pump P-104 falls under OISD-STD-154 (Work Permit System) and Factory Act 
Section 21 (Fencing of Machinery). All work permits were obtained prior to 
maintenance activities.

Report approved by: V. Sharma, Maintenance Manager
```

> **Agent instruction:** Write this content into a `.txt` file at `plantmind/data/sample_docs/maintenance/maintenance_report_P104.txt`. The ingestion pipeline will handle it as text extraction. Alternatively, use `reportlab` or `fpdf` to generate an actual PDF.

---

### Document 3: `safety_procedures/SOP_emergency_shutdown.pdf`
**Type:** PDF (text-based)
**Purpose:** Tests PDF extractor + NER for procedure/regulation references

Create as text/PDF:

```
STANDARD OPERATING PROCEDURE
==============================
SOP ID: SOP-SAFE-007
Title: Emergency Shutdown Procedure for Unit-3
Revision: 3.1
Effective Date: 2024-01-01
Approved By: R. Sundaram, Plant Manager

1. PURPOSE
-----------
This procedure defines the steps for emergency shutdown (ESD) of Coastal 
Refinery Unit-3, covering the crude distillation column DC-01, associated 
heat exchangers (HX-201, HX-202), pumps (P-104, P-105), and compressors 
(C-301, C-302).

2. SCOPE
---------
Applicable to all operating and maintenance personnel assigned to Unit-3.
Compliance with OISD-STD-154 (Work Permit System) and PESO 
(Petroleum and Explosives Safety Organisation) guidelines is mandatory.

3. EMERGENCY SHUTDOWN STEPS
-----------------------------
Step 1: Activate ESD pushbutton at Control Room Panel CP-03
Step 2: Verify all feed pumps (P-104, P-105) have tripped
Step 3: Close emergency isolation valve V-045 on crude feed line
Step 4: Verify compressor C-302 auto-shutdown on high discharge pressure
Step 5: Open depressurization valve V-046 to flare system
Step 6: Confirm heat exchanger HX-201 cooling water flow is maintained
Step 7: Notify Control Room Operator and Shift Supervisor
Step 8: Initiate headcount at Assembly Point AP-2

4. POST-SHUTDOWN ACTIONS
--------------------------
- Do NOT restart any equipment until Root Cause Analysis is completed
- Maintain Lockout/Tagout as per OISD-STD-154 Section 4.3
- Document all actions in Shift Log and notify Safety Department
- If hydrocarbon release detected, follow SOP-ENV-003 (Spill Response)

5. EQUIPMENT REFERENCE
------------------------
| Tag    | Description                  | Normal State | ESD State |
|--------|------------------------------|-------------|-----------|
| P-104  | Crude Transfer Pump          | Running     | Tripped   |
| P-105  | Standby Transfer Pump        | Standby     | Tripped   |
| HX-201 | Feed/Effluent Heat Exchanger | Online      | Cooling   |
| C-302  | Process Gas Compressor       | Running     | Shutdown  |
| V-045  | Crude Feed Isolation Valve   | Open        | Closed    |
| V-046  | Depressurization Valve       | Closed      | Open      |

6. REGULATORY REFERENCES
--------------------------
- OISD-STD-154: Standard on Work Permit System
- PESO: Petroleum and Explosives Safety Organisation Rules
- Factory Act 1948, Section 38: Precautions against dangerous fumes
- IS 15656:2006: Hazard Identification and Risk Assessment
```

---

### Document 4: `inspection_forms/inspection_V045_scan.png`
**Type:** PNG image (simulated scanned form)
**Purpose:** Tests OCR processor

> **Agent instruction:** Generate a realistic image of a hand-filled inspection form using the generate_image tool or create a structured text-based PNG. The form should contain:

```
EQUIPMENT INSPECTION REPORT
============================
Date: 2024-05-20
Inspector: John Patel
Equipment Tag: V-045
Equipment Name: Gate Valve - Crude Feed Line
Location: Unit-3, Area B, Line CL-015

INSPECTION CHECKLIST:
[✓] Visual inspection — no external damage
[✓] Stem packing — recently replaced (ref WO-2024-005)
[✗] Actuator function test — FAILED (slow response, 8 sec vs 3 sec spec)
[✓] Position indicator — functional
[✓] Body/bonnet gasket — no leaks detected
[✗] Handwheel operation — stiff, needs lubrication

OVERALL CONDITION: FAIR
NEXT INSPECTION DUE: 2024-11-20

NOTES:
Actuator response time exceeds OISD-STD-154 requirement of ≤5 seconds
for emergency isolation valves. Recommend actuator overhaul before next
scheduled turnaround. Ref: OISD-STD-154, Clause 7.2.

Signature: J. Patel
```

---

### Document 5: `pid_drawings/unit3_pid_simplified.png`
**Type:** PNG image (simplified P&ID)
**Purpose:** Tests P&ID tag detection (OCR-based for prototype)

> **Agent instruction:** Generate a simplified P&ID diagram image showing the following equipment connected by process lines:
> - Tank TK-001 → Pump P-104 → Heat Exchanger HX-201 → Distillation Column DC-01
> - Compressor C-302 connected to DC-01 overhead
> - Valve V-045 on the line between TK-001 and P-104
> - Valve V-046 connected to flare
> - Label all equipment tags clearly

---

### Document 6: `regulatory/OISD_STD_154_excerpt.pdf`
**Type:** PDF (text-based)
**Purpose:** Tests regulatory reference extraction

```
OISD STANDARD 154 — WORK PERMIT SYSTEM (EXCERPT)
==================================================
(Oil Industry Safety Directorate)

1. SCOPE
---------
This standard covers the work permit system requirements for petroleum 
refineries, oil & gas processing plants, and petrochemical facilities.

4.3 LOCKOUT/TAGOUT REQUIREMENTS
---------------------------------
4.3.1 All energy sources shall be positively isolated before maintenance 
      work begins.
4.3.2 Lockout devices shall be applied by authorized personnel only.
4.3.3 Each worker shall apply their personal lock.
4.3.4 Tagout tags shall include: worker name, date, time, and reason.

7.2 EMERGENCY ISOLATION VALVES
-------------------------------
7.2.1 Emergency isolation valves shall be tested quarterly.
7.2.2 Valve response time shall not exceed 5 seconds from signal to 
      fully closed position.
7.2.3 Failed valves shall be reported immediately and repaired within 
      24 hours or the associated process unit shall be shut down.
7.2.4 All EIV tests shall be documented and records maintained for 
      minimum 5 years.

9.1 HOT WORK PERMITS
----------------------
9.1.1 Hot work within 15 meters of hydrocarbon-containing equipment 
      requires gas testing immediately before and during work.
9.1.2 Fire watch shall be maintained for 30 minutes after hot work 
      completion.
```

---

### Document 7: `regulatory/factory_act_excerpt.pdf`
**Type:** PDF (text-based)
**Purpose:** Second regulatory document for cross-referencing

```
THE FACTORIES ACT, 1948 — RELEVANT SECTIONS (EXCERPT)
=======================================================

SECTION 21: Fencing of Machinery
----------------------------------
(1) In every factory the following shall be securely fenced:
    (a) every moving part of a prime mover and every flywheel
    (b) the headrace and tailrace of every water-wheel and water-turbine
    (c) every part of an electric generator, motor, or rotary converter
    (d) every part of transmission machinery
(2) Fencing shall be of substantial construction and constantly maintained.
(3) No fencing shall be removed while machinery is in motion.

SECTION 38: Precautions Against Dangerous Fumes
-------------------------------------------------
(1) No person shall enter any confined space in which dangerous fumes are 
    likely to be present unless:
    (a) the space has been adequately ventilated and tested for gas
    (b) the person is wearing suitable breathing apparatus
    (c) a responsible person is stationed outside with rescue equipment
(2) Records of all confined space entries shall be maintained.
```

---

### Document 8: `maintenance/incident_report_C302.pdf`
**Type:** PDF (text-based)
**Purpose:** Cross-references with work orders to enable RCA agent demo

```
INCIDENT REPORT
================
Incident ID: INC-2024-003
Date: 2024-05-18
Time: 14:35
Location: Coastal Refinery Unit-3, Compressor Bay
Equipment: Reciprocating Compressor C-302

CLASSIFICATION: Near Miss — Hydrocarbon Release (Minor)

1. DESCRIPTION
---------------
During normal operation, the mechanical seal on Compressor C-302 discharge 
side failed catastrophically, resulting in a minor hydrocarbon gas release. 
The gas detection system GDS-07 activated at 14:35, triggering automatic 
ventilation fans. Area was evacuated per SOP-SAFE-007.

This is the SECOND seal failure on C-302 in 3 months (previous: WO-2024-003, 
dated 2024-03-10). 

2. IMMEDIATE ACTIONS TAKEN
----------------------------
- Emergency shutdown initiated per SOP-SAFE-007
- Area evacuated, headcount confirmed at AP-2
- Gas levels monitored until below LEL
- Equipment isolated and locked out per OISD-STD-154

3. ROOT CAUSE ANALYSIS
------------------------
Primary Cause: Repeated mechanical seal failure
Contributing Factors:
  a) Misalignment between compressor and driver (0.15mm offset measured, 
     spec allows max 0.05mm)
  b) Operating temperature exceeding design by 12°C during peak summer
  c) Seal material (carbon/SiC) not rated for sustained temperatures above 
     180°C — actual operating temp reached 192°C
  d) Previous repair (WO-2024-003) replaced seal but did not address 
     underlying misalignment

4. CORRECTIVE ACTIONS
-----------------------
| Action | Responsible | Due Date | Status |
|--------|------------|----------|--------|
| Full laser alignment of C-302 | Raj Mehta | 2024-06-01 | Completed |
| Upgrade to high-temp seal (SiC/SiC) | Procurement | 2024-06-15 | Ordered |
| Install temperature monitoring on seal | Instrumentation | 2024-06-10 | Completed |
| Review all compressor seals plant-wide | V. Sharma | 2024-07-01 | Pending |

5. LESSONS LEARNED
--------------------
- Repeated failures on the same equipment within a short period must trigger 
  an engineering review, not just a like-for-like replacement
- Operating temperature deviations should be flagged by the DCS alarm system — 
  alarm setpoint review needed
- This incident pattern (seal failure + misalignment + temperature exceedance) 
  should be added to the plant's Lessons Learned database for all rotating 
  equipment

Investigated by: V. Sharma, Maintenance Manager
Reviewed by: R. Sundaram, Plant Manager
```

---

## 2.3 Ground Truth Benchmark

Create this file at `plantmind/data/ground_truth.json`:

```json
{
  "benchmark_version": "1.0",
  "description": "15 ground-truth facts for evaluating PlantMind query accuracy",
  "facts": [
    {
      "id": "GT-01",
      "question": "How many work orders have been raised for Pump P-104?",
      "answer": "3 work orders: WO-2024-001, WO-2024-004, WO-2024-008",
      "source_docs": ["work_orders.csv"],
      "type": "single_document"
    },
    {
      "id": "GT-02",
      "question": "What is the root cause of recurring vibration in Pump P-104?",
      "answer": "Coupling misalignment between the pump and its driver motor, compounded by bearing wear. Base frame may have shifted due to thermal expansion.",
      "source_docs": ["maintenance_report_P104.pdf", "work_orders.csv"],
      "type": "cross_document"
    },
    {
      "id": "GT-03",
      "question": "How many seal failures has Compressor C-302 experienced?",
      "answer": "2 seal failures: WO-2024-003 (2024-03-10) and WO-2024-006/INC-2024-003 (2024-05-18)",
      "source_docs": ["work_orders.csv", "incident_report_C302.pdf"],
      "type": "cross_document"
    },
    {
      "id": "GT-04",
      "question": "What is the OISD-STD-154 requirement for emergency isolation valve response time?",
      "answer": "Response time shall not exceed 5 seconds from signal to fully closed position (Clause 7.2.2)",
      "source_docs": ["OISD_STD_154_excerpt.pdf"],
      "type": "single_document"
    },
    {
      "id": "GT-05",
      "question": "Does Valve V-045 comply with OISD-STD-154 Clause 7.2?",
      "answer": "No. Inspection found actuator response time of 8 seconds, exceeding the 5-second maximum requirement.",
      "source_docs": ["inspection_V045_scan.png", "OISD_STD_154_excerpt.pdf"],
      "type": "cross_document_compliance"
    },
    {
      "id": "GT-06",
      "question": "What equipment is involved in the emergency shutdown procedure for Unit-3?",
      "answer": "P-104, P-105, HX-201, HX-202, C-301, C-302, V-045, V-046, DC-01",
      "source_docs": ["SOP_emergency_shutdown.pdf"],
      "type": "single_document"
    },
    {
      "id": "GT-07",
      "question": "Who is assigned to maintain Pump P-104?",
      "answer": "John Patel, Senior Maintenance Technician",
      "source_docs": ["work_orders.csv", "maintenance_report_P104.pdf"],
      "type": "cross_document"
    },
    {
      "id": "GT-08",
      "question": "What was the root cause of the Compressor C-302 incident?",
      "answer": "Repeated mechanical seal failure caused by: (a) misalignment (0.15mm vs 0.05mm spec), (b) operating temperature exceeding design by 12°C (192°C actual vs 180°C rated), (c) seal material not rated for sustained high temps, (d) previous repair didn't address underlying misalignment.",
      "source_docs": ["incident_report_C302.pdf"],
      "type": "single_document"
    },
    {
      "id": "GT-09",
      "question": "What regulations apply to maintenance work on Pump P-104?",
      "answer": "OISD-STD-154 (Work Permit System) and Factory Act 1948, Section 21 (Fencing of Machinery)",
      "source_docs": ["maintenance_report_P104.pdf", "OISD_STD_154_excerpt.pdf", "factory_act_excerpt.pdf"],
      "type": "cross_document_compliance"
    },
    {
      "id": "GT-10",
      "question": "What is the recommended corrective action for the recurring vibration issue in P-104?",
      "answer": "Laser alignment of pump-motor coupling, base frame leveling survey, increase vibration monitoring from quarterly to monthly, consider upgrading to flexible coupling.",
      "source_docs": ["maintenance_report_P104.pdf"],
      "type": "single_document"
    },
    {
      "id": "GT-11",
      "question": "Are there any common failure patterns across different equipment in Unit-3?",
      "answer": "Yes — misalignment is a recurring root cause affecting both P-104 (pump-motor coupling misalignment causing vibration/bearing failure) and C-302 (compressor-driver misalignment causing seal failure). This suggests a plant-wide alignment program may be needed.",
      "source_docs": ["maintenance_report_P104.pdf", "incident_report_C302.pdf", "work_orders.csv"],
      "type": "cross_document_insight"
    },
    {
      "id": "GT-12",
      "question": "What is the ESD procedure when high discharge pressure is detected on C-302?",
      "answer": "Compressor C-302 has auto-shutdown on high discharge pressure (Step 4 of SOP-SAFE-007). The ESD sequence also includes tripping feed pumps, closing V-045, and opening V-046 to flare.",
      "source_docs": ["SOP_emergency_shutdown.pdf"],
      "type": "single_document"
    },
    {
      "id": "GT-13",
      "question": "What Factory Act requirements apply to confined space entry?",
      "answer": "Section 38: Space must be ventilated and gas-tested, person must wear breathing apparatus, a responsible person must be stationed outside with rescue equipment, and records must be maintained.",
      "source_docs": ["factory_act_excerpt.pdf"],
      "type": "single_document"
    },
    {
      "id": "GT-14",
      "question": "Which work orders were raised as critical priority?",
      "answer": "WO-2024-003 (C-302 seal leak) and WO-2024-006 (C-302 second seal failure)",
      "source_docs": ["work_orders.csv"],
      "type": "single_document"
    },
    {
      "id": "GT-15",
      "question": "What cross-document insight connects V-045 inspection results to regulatory compliance?",
      "answer": "The V-045 inspection report shows actuator response time of 8 seconds, which violates OISD-STD-154 Clause 7.2.2 (max 5 seconds). Per Clause 7.2.3, the failed valve must be repaired within 24 hours or the unit must be shut down. The SOP-SAFE-007 lists V-045 as an emergency isolation valve in the shutdown sequence.",
      "source_docs": ["inspection_V045_scan.png", "OISD_STD_154_excerpt.pdf", "SOP_emergency_shutdown.pdf"],
      "type": "cross_document_compliance"
    }
  ]
}
```

---

## 2.4 Verification Gate

**All checks must pass before proceeding to Step 3:**

### Check 1: File count
```bash
find plantmind/data/sample_docs -type f | wc -l
```
**Expected:** 8 files (1 CSV + 4 PDFs/TXTs + 2 images + 1 regulatory excerpt)

### Check 2: Ground truth file exists and is valid JSON
```bash
python -c "import json; data = json.load(open('plantmind/data/ground_truth.json')); print(f'{len(data[\"facts\"])} facts loaded')"
```
**Expected:** `15 facts loaded`

### Check 3: Cross-document references exist
Manually verify:
- P-104 appears in: work_orders.csv, maintenance_report, SOP, P&ID
- C-302 appears in: work_orders.csv, incident_report, SOP
- V-045 appears in: work_orders.csv, inspection_form, SOP, OISD excerpt
- OISD-STD-154 appears in: maintenance_report, SOP, OISD excerpt, inspection form

---

## Output of This Step

After completing Step 2, you should have:
- ✅ 8 sample documents covering all document types (PDF, CSV, image)
- ✅ Documents contain cross-referencing entities (equipment, people, regulations)
- ✅ 15 ground-truth facts defined for evaluation benchmarking
- ✅ At least 3 cross-document insights that no single document could provide alone

**→ Proceed to [Step 3 — Ingestion Pipeline](step3_ingestion_pipeline.md)**
