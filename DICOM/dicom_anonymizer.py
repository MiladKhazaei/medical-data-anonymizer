import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pydicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.uid import generate_uid, PYDICOM_IMPLEMENTATION_UID

class MedicalDicomAnonymizer:
    """
    MRI De-Identification by DICOM PS 3.15 (Annex E), HIPAA Safe Harbor
    """
    def __init__(self, shift_days: int = 145, project_prefix: str = "1.2.826.0.1.3680043.10."):
        self.shift_days = shift_days
        self.prefix = project_prefix
        
        # In-Memory tables
        self._study_uid_map: Dict[str, str] = {}
        self._series_uid_map: Dict[str, str] = {}
        self._frame_of_ref_map: Dict[str, str] = {}
        self._sop_uid_map: Dict[str, str] = {}

    def _shift_dicom_date(self, date_str: Optional[str]) -> str:
        """Date-Shifting DICOM VR: DA (YYYYMMDD)"""
        if not date_str or len(str(date_str).strip()) != 8:
            return ""
        try:
            parsed_date = datetime.strptime(str(date_str).strip(), "%Y%m%d")
            shifted_date = parsed_date - timedelta(days=self.shift_days)
            return shifted_date.strftime("%Y%m%d")
        except ValueError:
            return ""

    def _shift_dicom_datetime(self, dt_str: Optional[str]) -> str:
        """DateTime-Empty DICOM VR: DT"""
        if not dt_str:
            return ""
        raw_dt = str(dt_str).strip()
        try:
            date_part = raw_dt[:8]
            parsed_date = datetime.strptime(date_part, "%Y%m%d")
            shifted_date = parsed_date - timedelta(days=self.shift_days)
            # Keeps shifted_date without its time
            return shifted_date.strftime("%Y%m%d000000.000000")
        except ValueError:
            return ""

    """Generate unique DICOM structure elements"""
    def _get_mapped_uid(self, original_uid: Optional[str], uid_cache: Dict[str, str]) -> str:
        if not original_uid:
            return generate_uid(prefix=self.prefix)
        orig_str = str(original_uid).strip()
        if orig_str not in uid_cache:
            uid_cache[orig_str] = generate_uid(prefix=self.prefix)
        return uid_cache[orig_str]

    """Clear study description"""
    def _sanitize_study_description(self, desc: Optional[str]) -> str:
        if not desc:
            return "RESEARCH_NEURO_SCAN"
        clean_desc = str(desc).upper()
        if "EPILEPSY" in clean_desc or "BRAIN" in clean_desc:
            return "RESEARCH_NEURO_EPILEPSY"
        return "RESEARCH_NEURO_PROTOCOL"

    """Navigation sequential recursive and rewrite nested element"""
    def _remap_sequences(self, ds: Dataset) -> None:
        if "RelatedSeriesSequence" in ds and isinstance(ds.RelatedSeriesSequence, Sequence):
            for item in ds.RelatedSeriesSequence:
                if "StudyInstanceUID" in item:
                    item.StudyInstanceUID = self._get_mapped_uid(item.StudyInstanceUID, self._study_uid_map)
                if "SeriesInstanceUID" in item:
                    item.SeriesInstanceUID = self._get_mapped_uid(item.SeriesInstanceUID, self._series_uid_map)
                if "ReferencedSOPInstanceUID" in item:
                    item.ReferencedSOPInstanceUID = self._get_mapped_uid(item.ReferencedSOPInstanceUID, self._sop_uid_map)

    def process_file(self, input_path: str, output_path: str, pseudo_patient_id: str) -> None:
        """Running the De-Identification pipeline, security validation, and storing data"""
        ds: Dataset = pydicom.dcmread(input_path)

        # Checking BurnedInAnnotation to be NO
        burned_in = getattr(ds, "BurnedInAnnotation", "NO")
        if str(burned_in).strip().upper() == "YES":
            raise ValueError(f"Security Alert: Burned-in annotation detected in file {input_path}")
        ds.BurnedInAnnotation = "NO"

        # Remove Private Tags
        ds.remove_private_tags()

        # UID Hierarchy
        ds.StudyInstanceUID = self._get_mapped_uid(getattr(ds, "StudyInstanceUID", None), self._study_uid_map)
        ds.SeriesInstanceUID = self._get_mapped_uid(getattr(ds, "SeriesInstanceUID", None), self._series_uid_map)
        
        if "FrameOfReferenceUID" in ds:
            ds.FrameOfReferenceUID = self._get_mapped_uid(ds.FrameOfReferenceUID, self._frame_of_ref_map)

        # Generate unique UID
        orig_sop = getattr(ds, "SOPInstanceUID", None)
        new_sop_uid = generate_uid(prefix=self.prefix)
        if orig_sop:
            self._sop_uid_map[str(orig_sop).strip()] = new_sop_uid
            
        ds.SOPInstanceUID = new_sop_uid
        ds.file_meta.MediaStorageSOPInstanceUID = new_sop_uid

        # rewrite nested UID
        self._remap_sequences(ds)

        # Sanitizing software specifications and source entities in header metadata
        if hasattr(ds.file_meta, "SourceApplicationEntityTitle"):
            ds.file_meta.SourceApplicationEntityTitle = "RESEARCH_NODE"
        ds.file_meta.ImplementationClassUID = PYDICOM_IMPLEMENTATION_UID

        # Date-shifting on all Dates
        date_attributes: List[str] = [
            "InstanceCreationDate", "StudyDate", "SeriesDate", 
            "AcquisitionDate", "ContentDate", "PerformedProcedureStepStartDate"
        ]
        for attr in date_attributes:
            if attr in ds:
                setattr(ds, attr, self._shift_dicom_date(getattr(ds, attr)))

        # Date-Time process
        if "AcquisitionDateTime" in ds:
            ds.AcquisitionDateTime = self._shift_dicom_datetime(ds.AcquisitionDateTime)

        # Clear Times
        time_attributes: List[str] = [
            "InstanceCreationTime", "StudyTime", "SeriesTime", 
            "AcquisitionTime", "ContentTime", "PerformedProcedureStepStartTime"
        ]
        for attr in time_attributes:
            if attr in ds:
                setattr(ds, attr, "")

        # Clear PHI fields
        ds.PatientName = pseudo_patient_id
        ds.PatientID = pseudo_patient_id
        ds.PatientBirthDate = ""
        ds.AccessionNumber = ""
        ds.InstitutionName = ""
        ds.InstitutionAddress = ""
        ds.ReferringPhysicianName = ""
        ds.OperatorsName = ""
        ds.StationName = ""
        ds.InstitutionalDepartmentName = ""
        ds.DeviceSerialNumber = ""
        ds.StudyID = ""
        
        if "IssuerOfPatientID" in ds:
            ds.IssuerOfPatientID = ""
        if "PerformedProcedureStepID" in ds:
            ds.PerformedProcedureStepID = ""
        if "PerformedProcedureStepDescription" in ds:
            ds.PerformedProcedureStepDescription = ""

        # Clear description
        if "StudyDescription" in ds:
            ds.StudyDescription = self._sanitize_study_description(ds.StudyDescription)

        # Audit Trail
        ds.PatientIdentityRemoved = "YES"
        ds.DeidentificationMethod = [
            "DICOM PS 3.15 Annex E Basic Profile",
            "HIPAA Safe Harbor De-identification",
            "Deterministic UID Mapping and Date Shifting"
        ]

        # Stores de-identified file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        ds.save_as(output_path, write_like_original=False)  