# import necessaries
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any
from DICOM.dicom_anonymizer import MedicalDicomAnonymizer

def convert_dicom_to_bids_nifti(
    dicom_dir: Path,
    bids_root: Path,
    subject_id: str,
    session_id: str,
    acq_label: str = "T1w",
)->Path:
    """Converts de-identified DICOM slices in sourcedata into BIDS-compliant NIfTI."""

    # check if dcm2niix is installed in system
    if not shutil.which("dcm2niix"):
        raise FileNotFoundError(
            "dcm2niix executable was not found in PATH. "
            "Please install it via 'pip install dcm2niix' or add dcm2niix to system PATH."
        )
    # Normalize BIDS entity prefixes
    clean_sub = f"sub-{subject_id.replace('sub-','')}"
    clean_ses = f"ses-{session_id.replace('ses-','')}"

    # Destination in BIDS root: bids_root/sub-01-ses-01/anat/
    anat_output_dir = bids_root / clean_sub / clean_ses / "anat"
    anat_output_dir.mkdir(parents=True, exist_ok=True)

    # BIDS naming format: sub-01_ses-01_T1w
    file_prefix = f"{clean_sub}_{clean_ses}_{acq_label}"
    
    cmd = [
        "dcm2niix",
        "-b", "y", # Create BIDS JSON sidecar (.json)
        "-z", "y", # Compress output to .nii.gz
        "-f", file_prefix, # Filename template
        "-o", str(anat_output_dir), # Output directory
        str(dicom_dir) # Input DICOM directory (from sorcedata)
    ]

    subprocess.run(cmd, check=True)
    return anat_output_dir
    

def process_dicom_bids_pipeline(
    source_dir: Path,
    bids_root: Path,
    subject_id: str,
    session_id: str,
    shift_days: int,
) -> Dict[str, Any]:
    """DICOM BIDS Ingestion & De-Identification Pipeline."""
    # Normalize BIDS entity prefixes
    clean_sub = f"sub-{subject_id.replace('sub-', '')}"
    clean_ses = f"ses-{session_id.replace('ses-', '')}"
    # 1. define sourcedata
    target_anat_dir = bids_root / "sourcedata" / clean_sub / clean_ses / "anat"
    target_anat_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Filtering DICOM files/ sorting
    raw_files = sorted(list(source_dir.glob("*.dcm")) + list(source_dir.glob("*.DCM"))) 
    if not raw_files:
        return {
            "status": "Failed",
            "processed_count": 0,
            "error": f"No DICOM (.dcm) files found in {source_dir}"
        }
    
    # 3. Build an instance of MedicalDicomAnonymizer
    anonymizer = MedicalDicomAnonymizer(shift_days=shift_days)
    total_processed = 0

    # 4. Process slices sequentially and name them
    for index, file_path in enumerate(raw_files, start=1):
        output_file_name = f"{clean_sub}_{clean_ses}_slice-{index:04d}.dcm"
        target_file_path = target_anat_dir / output_file_name
        
        try:
            anonymizer.process_file(
                input_path=str(file_path),
                output_path=str(target_file_path),
                pseudo_patient_id=clean_sub
            )
            total_processed += 1
        except Exception as error:
            print(f"Warning: Corrupted slice skipped [{file_path.name}]: {error}")
    
    if total_processed == 0:
        return {
            "status" : "FAILED",
            "processed_count" : total_processed,
            "error" : "All DICOM slices failed during de-identification."
        }

    # 5. Convert de-identified DICOM slices to BIDS NIfTI!
    nifti_dir = None
    if total_processed > 0:
        try:
            print(f"[INFO] Converting {total_processed} DICOM slices to BIDS NIfTI...")
            nifti_dir = convert_dicom_to_bids_nifti(
                dicom_dir=target_anat_dir,
                bids_root=bids_root,
                subject_id=clean_sub,
                session_id=clean_ses,
                acq_label="T1w"
            )
            print(f"[INFO] NIfTI conversion complete: {nifti_dir}")
        except Exception as err:
            print(f"[Warning] NIfTI conversion failed: {err}")
            
    return{
        "status": "SUCCESS",
        "processed_count": total_processed,
        "sourcedata_directory": target_anat_dir,
        "nifti_directory": nifti_dir
    }