# import necesseries
from pathlib import Path
from typing import Dict, Any
import mne
import mne_bids
from DICOM.batch_anonymization import process_dicom_bids_pipeline
from EEG.batch_anonymization import process_eeg_bids_pipeline

def get_valid_modality_choice() -> str:
    """Get Inputs securely"""
    while True:
        user_input = input("\nSelect Modality ---> ['mri' for DICOM | 'eeg' for EDF]: ").strip().lower()
        if user_input in ("mri", "eeg"):
            return user_input
        print("Invalid selection. You must type exactly 'mri' or 'eeg'. Try again.")

def get_valid_directory(prompt: str) -> Path:
    """Directory Exists Validation"""
    while True:
        path_str = input(prompt).strip()
        dir_path = Path(path_str).resolve()
        if dir_path.is_dir():
            return dir_path
        print(f"Error: Directory '{dir_path}' was not found. Please provide a valid path.")

def get_valid_integer(prompt: str) -> int:
    """Getting the integer days number"""
    while True:
        val_str = input(prompt).strip()
        try:
            val = int(val_str)
            if val > 0:
                return val
            print("Value must be a positive integer.")
        except ValueError:
            print("Format Error: Please enter a valid number (e.g., 145).")



def main():
    print("=" * 65)
    print("  Multimodal Medical BIDS Ingestion Pipeline (MRI & EEG)")
    print("=" * 65)

    # Phase: 1
    modality = get_valid_modality_choice()
    
    raw_sub = input("Enter Patient Pseudo ID (e.g., 01 or sub-01): ").strip()
    clean_sub_id = f"sub-{raw_sub.replace('sub-', '')}"

    raw_ses = input("Enter Clinical Session ID (e.g., 01 or ses-01): ").strip()
    clean_ses_id = f"ses-{raw_ses.replace('ses-', '')}"

    shift_days = get_valid_integer("Enter Date Shift Offset in Days (e.g., 145): ")

    prompt_msg = f"Enter Path to Raw {'DICOM' if modality == 'mri' else 'EEG'} Directory: "
    source_dir = get_valid_directory(prompt_msg)
    bids_root = get_valid_directory("Enter Destination BIDS Root Directory: ")

    # Phase 2: Process
    if modality == "mri":
        print(f"\n[INFO] Initializing DICOM De-Identification for {clean_sub_id}...")
        result = process_dicom_bids_pipeline(
            source_dir=source_dir,
            bids_root=bids_root,
            subject_id=clean_sub_id,
            session_id=clean_ses_id,
            shift_days=shift_days
        )
    else:
        print(f"\n[INFO] Initializing EEG De-Identification for {clean_sub_id}...")
        result = process_eeg_bids_pipeline(
            source_dir=source_dir,
            bids_root=bids_root,
            subject_id=clean_sub_id,
            session_id=clean_ses_id,
            shift_days=shift_days
        )

    # Print the result
    print("\nExecution Report:")
    print(f"  • Status: {result['status']}")
    print(f"  • Processed Files: {result['processed_count']}")
    if "sourcedata_directory" in result and result["sourcedata_directory"]:
        print(f"  • Sourcedata Directory: {result['sourcedata_directory']}")
    if "nifti_directory" in result and result["nifti_directory"]:
        print(f"  • NIfTI Directory: {result['nifti_directory']}")
    if "error" in result:
        print(f"  • Error Details: {result['error']}")

if __name__ == "__main__":
    main()