# Medical Multimodal Data Anonymizer & BIDS Pipeline (MRI & EEG)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![BIDS Standard](https://img.shields.io/badge/BIDS-v1.9+-success.svg)](https://bids.neuroimaging.io/)
[![HIPAA Safe Harbor](https://img.shields.io/badge/Compliance-HIPAA%20Safe%20Harbor-orange.svg)](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html)
[![DICOM PS 3.15](https://img.shields.io/badge/Standard-DICOM%20PS%203.15%20Annex%20E-blueviolet.svg)](https://dicom.nema.org/medical/dicom/current/output/html/part15.html)

A secure, unified de-identification and ingestion pipeline that converts clinical neuroimaging (**MRI / DICOM**) and electrophysiology (**EEG / EDF**) data into a standardized, fully compliant **Brain Imaging Data Structure (BIDS)** dataset.

---

## 📌 Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Privacy & De-Identification Standards](#privacy--de-identification-standards)
- [BIDS Architecture & Data Flow](#bids-architecture--data-flow)
- [Project Structure](#project-structure)
- [Installation & Requirements](#installation--requirements)
- [Usage](#usage)
  - [Interactive CLI (`main.py`)](#interactive-cli-mainpy)
  - [Programmatic API](#programmatic-api)
- [De-Identification Rules Reference](#de-identification-rules-reference)
- [References](#references)

---

## 📖 Overview

When preparing hospital and clinical data for research, neuroscientists face two critical hurdles:
1. **Patient Privacy Regulations:** Strictly removing Protected Health Information (PHI) under **HIPAA Safe Harbor (45 CFR § 164.514)** and **DICOM PS 3.15 Annex E Basic Profile**.
2. **Data Heterogeneity:** Clinical scans and signal recordings come in disparate proprietary formats (vendor-specific DICOM slices, EDF montages).

This project provides an automated, end-to-end Python pipeline that:
- De-identifies raw **DICOM MRI slices**, stores them in BIDS `sourcedata/`, and converts them into 3D/4D **BIDS NIfTI (`.nii.gz` + `.json`)**.
- Sanitizes binary headers of **EEG EDF files**, standardizes clinical event annotations, and exports them directly into **BIDS-EEG** format with complete metadata sidecars (`.tsv` and `.json`).

---

## ✨ Key Features

- **HIPAA Safe Harbor & DICOM PS 3.15 Compliance:**
  - Complete removal of the 18 direct personal identifiers (names, patient IDs, institutions, physicians, accession numbers).
  - Deletion of all private vendor tags (`remove_private_tags()`).
  - Validation against burned-in annotations (`BurnedInAnnotation`).
  - Stripping of time fields to eliminate exact timestamp tracking.
- **Deterministic UID Replacement:**
  - Maintains referential integrity across slices and series by remapping `StudyInstanceUID`, `SeriesInstanceUID`, and `SOPInstanceUID` with deterministic hierarchical UIDs.
- **Synchronized Date-Shifting:**
  - Shifts all acquisition and study dates backward by a customizable offset (`shift_days`) to preserve longitudinal intervals while obfuscating the true calendar dates.
- **Automated DICOM-to-NIfTI Conversion:**
  - Integrates `dcm2niix` to stack multi-slice DICOMs into compressed 3D NIfTI volumes (`.nii.gz`) and generate BIDS JSON sidecars.
- **Clinical EEG Annotation Standardization:**
  - Normalizes clinical seizure markers, slowing, and spikes into standardized machine-readable labels (e.g., `seizure_bilateral_tonic`, `seizure_focal_myoclonic`, `eeg_slowing_frontal_left`).
- **Full BIDS Compliance:**
  - Generates all BIDS dataset-level metadata: `dataset_description.json`, `participants.tsv`, `participants.json`, and scan logs (`*_scans.tsv`).

---

## 🛡️ Privacy & De-Identification Standards

| Protection Layer | Implementation Mechanism | Standard / Law |
| :--- | :--- | :--- |
| **Direct Identifiers** | Replaced with pseudo IDs (e.g., `sub-01`), cleared empty strings | HIPAA Safe Harbor § 164.514(b)(2) |
| **Private Elements** | Strips all vendor-specific private tags (`group % 2 == 1`) | DICOM PS 3.15 Annex E |
| **Temporal Obfuscation** | Reversible date-shifting with constant offset; timestamps cleared | HIPAA Safe Harbor § 164.514(b)(2)(i)(C) |
| **UID Cryptography** | Deterministic UID generation with project prefix `1.2.826.0.1.3680043.10.` | DICOM PS 3.15 Annex E |
| **Burned-In Annotation** | Automatic exception thrown if `BurnedInAnnotation == "YES"` | Safe Harbor Visual Inspection |
| **Audit Trail** | Header marked with `PatientIdentityRemoved = "YES"` and de-id methods | DICOM PS 3.15 Annex E Audit Trail |

---

## 🏗️ BIDS Architecture & Data Flow

Why are DICOM files placed in `sourcedata/` while EEG files are placed in `bids_root/`?

```
                     ┌───────────────────────────────┐
                     │ Raw Hospital Data (data/)     │
                     └───────────────┬───────────────┘
                                     │
                     ┌───────────────┴───────────────┐
                     │                               │
              [ MRI / DICOM ]                  [ EEG / EDF ]
                     │                               │
       MedicalDicomAnonymizer                  cleaned_annotations()
        (Date Shift, UID Remap)               (Event Standardization)
                     │                               │
                     ▼                               ▼
       bids_root/sourcedata/                   mne_bids.write_raw_bids()
     sub-XX/ses-YY/anat/*.dcm                  (Header Sanitization)
                     │                               │
                     ▼                               │
              dcm2niix conversion                    │
                     │                               │
                     ▼                               ▼
        bids_root/sub-XX/ses-YY/anat/     bids_root/sub-XX/ses-YY/eeg/
           ├── sub-XX_ses-YY_T1w.nii.gz      ├── sub-XX_ses-YY_task-ltm_eeg.edf
           └── sub-XX_ses-YY_T1w.json        ├── sub-XX_ses-YY_task-ltm_channels.tsv
                                             ├── sub-XX_ses-YY_task-ltm_events.tsv
                                             └── sub-XX_ses-YY_task-ltm_eeg.json
```

1. **MRI / DICOM (Sourcedata $\rightarrow$ NIfTI):**  
   The BIDS standard for structural neuroimaging **strictly requires NIfTI format** (`.nii` or `.nii.gz`). DICOM slices cannot live in the BIDS root. They are preserved in `bids_root/sourcedata/` and converted to 3D NIfTI volumes in `bids_root/sub-XX/ses-YY/anat/`.
2. **EEG / EDF (Direct BIDS):**  
   Under the **BIDS-EEG extension** (Pernet et al., 2019), `.edf` is an officially recognized primary format in the BIDS dataset root. `mne_bids` sanitizes the binary header, shifts recording dates, and generates all required TSV/JSON sidecars directly in `bids_root/sub-XX/ses-YY/eeg/`.

---

## 📂 Project Structure

```text
medical-data-anonymizer/
├── DICOM/
│   ├── batch_anonymization.py   # DICOM batch processor & dcm2niix conversion pipeline
│   └── dicom_anonymizer.py      # Core MedicalDicomAnonymizer (UID mapping, date shift)
├── EEG/
│   ├── batch_anonymization.py   # EEG BIDS ingestion pipeline using mne-bids
│   ├── cleaned_annotations.py   # Annotation extractor and cleaner for raw EEG
│   └── standardize_label.py     # Rule-based clinical event label normalizer
├── data/                        # Sample input datasets
│   ├── dcm/                     # Sample raw DICOM slices
│   └── eeg/                     # Sample raw EDF recording
├── bids_root/                   # Generated output directory (BIDS compliant)
│   ├── dataset_description.json
│   ├── participants.tsv
│   ├── participants.json
│   ├── sourcedata/              # Anonymized source DICOM slices
│   └── sub-01/
│       └── ses-01/
│           ├── anat/            # BIDS NIfTI volume + JSON sidecar
│           └── eeg/             # BIDS EDF recording + TSV/JSON sidecars
├── main.py                      # Unified interactive CLI entry point
├── requirements.txt             # Project dependencies
└── README.md                    # Project documentation
```

---

## ⚙️ Installation & Requirements

### 1. Prerequisites
- **Python:** 3.10 or higher
- **dcm2niix:** Required for DICOM-to-NIfTI conversion.

### 2. Install Python Dependencies
```bash
git clone https://github.com/MiladKhazaei/medical-data-anonymizer.git
cd medical-data-anonymizer
pip install -r requirements.txt
```

*Contents of `requirements.txt`:*
```txt
mne==1.13.2
mne_bids==0.19.0
pydicom==3.0.2
dcm2niix==1.0.20260724
```

> **Note on `dcm2niix`:** Installing `dcm2niix` via pip provides the precompiled binary. Alternatively, on Linux: `sudo apt install dcm2niix`, or on macOS: `brew install dcm2niix`.

---

## 🚀 Usage

### Interactive CLI (`main.py`)

Run the unified command-line pipeline:
```bash
python main.py
```

The interactive prompt will guide you through:
1. Selecting modality (`mri` or `eeg`)
2. Patient Pseudo ID (e.g., `01` or `sub-01`)
3. Clinical Session ID (e.g., `01` or `ses-01`)
4. Calendar date shift offset in days (e.g., `145`)
5. Input data directory (e.g., `data/dcm` or `data/eeg`)
6. Destination BIDS root directory (e.g., `bids_root`)

#### Example Run (MRI):
```text
=================================================================
  Multimodal Medical BIDS Ingestion Pipeline (MRI & EEG)
=================================================================

Select Modality ---> ['mri' for DICOM | 'eeg' for EDF]: mri
Enter Patient Pseudo ID (e.g., 01 or sub-01): 01
Enter Clinical Session ID (e.g., 01 or ses-01): 01
Enter Date Shift Offset in Days (e.g., 145): 145
Enter Path to Raw DICOM Directory: data/dcm
Enter Destination BIDS Root Directory: bids_root

[INFO] Initializing DICOM De-Identification for sub-01...
[INFO] Converting 20 DICOM slices to BIDS NIfTI...
[INFO] NIfTI conversion complete: bids_root/sub-01/ses-01/anat

Execution Report:
  • Status: SUCCESS
  • Processed Files: 20
  • Sourcedata Directory: bids_root/sourcedata/sub-01/ses-01/anat
  • NIfTI Directory: bids_root/sub-01/ses-01/anat
```

#### Example Run (EEG):
```text
=================================================================
  Multimodal Medical BIDS Ingestion Pipeline (MRI & EEG)
=================================================================

Select Modality ---> ['mri' for DICOM | 'eeg' for EDF]: eeg
Enter Patient Pseudo ID (e.g., 01 or sub-01): 01
Enter Clinical Session ID (e.g., 01 or ses-01): 01
Enter Date Shift Offset in Days (e.g., 145): 145
Enter Path to Raw EEG Directory: data/eeg
Enter Destination BIDS Root Directory: bids_root

[INFO] Initializing EEG De-Identification for sub-01...

Execution Report:
  • Status: SUCCESS
  • Processed Files: 2
```

---

### Programmatic API

You can import and integrate the pipelines directly into your own scripts or workflows:

#### Processing DICOM MRI:
```python
from pathlib import Path
from DICOM.batch_anonymization import process_dicom_bids_pipeline

result = process_dicom_bids_pipeline(
    source_dir=Path("data/dcm"),
    bids_root=Path("bids_root"),
    subject_id="sub-01",
    session_id="ses-01",
    shift_days=145
)
print(result)
```

#### Processing EEG:
```python
from pathlib import Path
from EEG.batch_anonymization import process_eeg_bids_pipeline

result = process_eeg_bids_pipeline(
    source_dir=Path("data/eeg"),
    bids_root=Path("bids_root"),
    subject_id="sub-01",
    session_id="ses-01",
    shift_days=145
)
print(result)
```

---

## 📋 De-Identification Rules Reference

The table below outlines the primary DICOM attributes handled by `MedicalDicomAnonymizer`:

| DICOM Tag / Attribute | Action Taken | Rationale |
| :--- | :--- | :--- |
| `PatientName`, `PatientID` | Replaced with `pseudo_patient_id` | Direct patient identifier |
| `PatientBirthDate` | Cleared (`""`) | Safe Harbor birth date protection |
| `AccessionNumber`, `StudyID` | Cleared (`""`) | Internal hospital tracking numbers |
| `InstitutionName`, `InstitutionAddress` | Cleared (`""`) | Geographic location protection |
| `ReferringPhysicianName`, `OperatorsName` | Cleared (`""`) | Healthcare provider identity |
| `StudyDate`, `SeriesDate`, `AcquisitionDate` | Shifted by `- shift_days` | Calendar date obfuscation |
| `StudyTime`, `SeriesTime`, `AcquisitionTime` | Cleared (`""`) | Timestamp tracking protection |
| `StudyInstanceUID`, `SeriesInstanceUID` | Deterministically re-mapped | Cryptographic pseudonymization |
| `SOPInstanceUID` | Re-generated with project prefix | Preservation of DICOM hierarchy |
| `Private Tags (group % 2 != 0)` | Removed completely | May contain unindexed PHI |
| `StudyDescription` | Sanitized to research protocol name | May contain clinical notes / names |
| `BurnedInAnnotation` | Verified to be `"NO"` | Prevents burned-in patient text |

---

## 📚 References

1. **Appelhoff, S., Sanderson, M., Brooks, T., et al.** (2019). *MNE-BIDS: Organizing electrophysiological data into the BIDS format and facilitating their analysis.* Journal of Open Source Software, 4(44), 1896. [doi:10.21105/joss.01896](https://doi.org/10.21105/joss.01896)
2. **Pernet, C. R., Appelhoff, S., Gorgolewski, K. J., et al.** (2019). *EEG-BIDS, an extension to the brain imaging data structure for electroencephalography.* Scientific Data, 6, 103. [doi:10.1038/s41597-019-0104-8](https://doi.org/10.1038/s41597-019-0104-8)
3. **Gorgolewski, K. J., et al.** (2016). *The brain imaging data structure, a format for organizing and describing outputs of neuroimaging experiments.* Scientific Data, 3, 160044. [doi:10.1038/sdata.2016.44](https://doi.org/10.1038/sdata.2016.44)
4. **DICOM Standards Committee.** (2023). *DICOM PS 3.15: Security and System Management Profiles (Annex E - Attribute Confidentiality Profiles).* National Electrical Manufacturers Association (NEMA).
5. **U.S. Department of Health and Human Services (HHS).** *Guidance Regarding Methods for De-identification of Protected Health Information in Accordance with the Health Insurance Portability and Accountability Act (HIPAA) Privacy Rule (45 CFR § 164.514).*

---

## 📄 License
This project is open-source under the MIT License.
