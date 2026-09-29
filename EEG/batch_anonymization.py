from pathlib import Path
from typing import Dict, Any
import mne
import mne_bids
from EEG.cleaned_annotations import cleaned_annotations

def process_eeg_bids_pipeline(
    source_dir: Path,
    bids_root: Path,
    subject_id: str,
    session_id: str,
    shift_days: int = 145
) -> Dict[str, Any]:
    """آداپتور یکپارچه پردازش فایل‌های EDF نوار مغز و استقرار در ساختار BIDS"""
    edf_files = sorted(list(source_dir.glob("*.edf")) + list(source_dir.glob("*.EDF")))
    if not edf_files:
        return {"status": "FAILED", "processed_count": 0, "error": f"No EDF files in {source_dir}"}
    processed_count = 0
    clean_sub = subject_id.replace("sub-", "")
    clean_ses = session_id.replace("ses-", "")

    for index, edf_path in enumerate(edf_files, start=1):
        run_id = f"{index:02d}"
        
        # الف) خواندن جریان سیگنال بدون بارگذاری سنگین رم
        raw = mne.io.read_raw_edf(str(edf_path), preload=False, verbose=False)
        
        # ب) پالایش رویدادها با تابع اعتبارسنجی‌شده شما
        raw = cleaned_annotations(raw)

        # ج) تنظیم مسیر استاندارد BIDS-EEG
        bids_path = mne_bids.BIDSPath(
            subject=clean_sub,
            session=clean_ses,
            datatype="eeg",
            task="ltm",
            run=run_id,
            suffix="eeg",
            extension=".edf",
            root=bids_root
        )
        # د) گمنام‌سازی هدر باینری و انحراف تقویمی همگام
        anonymization_rules = {"daysback": shift_days, "keep_his": False}

        # هـ) صدور به فرمت BIDS
        mne_bids.write_raw_bids(
            raw=raw,
            bids_path=bids_path,
            anonymize=anonymization_rules,
            overwrite=True,
            format="auto",
            verbose=False
        )
        processed_count += 1
        
        
    return {"status": "SUCCESS", "processed_count": processed_count}