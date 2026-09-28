from DICOM.dicom_anonymizer import MedicalDicomAnonymizer
from pathlib import Path

def run_batch_anonymization() -> None:
    # ۱. دریافت ورودی‌ها به‌صورت تفکیک‌شده و شفاف
    input_dir_str = input("Enter the path of the raw DICOM directory: ").strip()
    pseudo_patient_id = input("Enter the pseudo patient ID (e.g., sub-001): ").strip()

    input_path = Path(input_dir_str)
    if not input_path.is_dir():
        print(f"Error: Directory '{input_dir_str}' does not exist.")
        return

    # ۲. ایجاد پوشه خروجی خارج از ساختار درونی داده‌های خام جهت پیشگیری از تداخل
    # Retuan a WindowsPath('Name_anonymized)
    # Path: C:/HospitalData/Patient_Velayati
    # علت معماری این کار؟
    # ا نمی‌خواهیم داده‌های گمنام‌شده درون همان پوشه اطلاعات محرمانه ریخته شوند
    # این کار ریسک مخلوط شدن فایل‌های خام و خروجی را از بین می‌برد.
    
    # این دستور یک پله به عقب برمی‌گردد و پوشه مادر (والد) را مشخص می‌کند. input_path.parent => C:/HospitalData
    # این دستور صرفاً نام پوشه نهایی را بدون بقیه مسیر استخراج می‌کند. input_path.name => Patient_Velayati
    # در اینجا عملگر تقسیم معادل Join
    # معادل تابع قدیمی os.path.join

    # current directory
    # output_path = input_path.parent / f"{input_path.name}_anonymized"
    
    # parent directory at Github.Project folder
    output_path = p = Path().cwd().resolve().parents[0] / f"{input_path.name}_anonymized"
    # output_path = input_path.parent / f"{input_path.name}_anonymized"
    # یک پوشه جدید در کنار پوشه خام اولیه تعریف می‌شود:
    # C:/HospitalData/Patient_Velayati_anonymized
    
    # creates parent folders, ignores if already exists
    # parents=True: Creates intermediate parent directories if they don't exist yet.
    # exist_ok=True: Prevents Python from throwing a FileExistsError if the directory already exists.
    output_path.mkdir(parents=True, exist_ok=True)

    # ۳. فیلتر امن فایل‌های دارای پسوند دایکام
    # gets only pattern files
    dicom_patterns = ["*.dcm"]
    raw_files = []
    for pattern in dicom_patterns:
        raw_files.extend(input_path.glob(pattern))
    
    # مرتب‌سازی الفبایی/عددی جهت حفظ توالی زمانی و فضایی اسلایس‌ها
    raw_files = sorted(raw_files)

    if not raw_files:
        print("No valid DICOM files found in the specified directory.")
        return

    # ۴. مقداردهی اولیه شیء گمنام‌ساز خارج از حلقه جهت نگهداری وضعیت UIDها
    anonymizer = MedicalDicomAnonymizer(shift_days=145)

    print(f"Starting de-identification for subject: {pseudo_patient_id}...")

    total_processed = 0
    for index, file_path in enumerate(raw_files, start=1):
        # نام‌گذاری خروجی: شناسه ثابت بیمار + شماره توالی اسلایس
        # index in 4 digit like 0001, 0002, etc.
        # sub-001_slice-0001.dcm
        output_file_name = f"{pseudo_patient_id}_slice-{index:04d}.dcm"
        # آدرس کامل فیزیکی برای ذخیره فایل روی هارد دیسک
        target_file_path = output_path / output_file_name
        # C:/HospitalData/Patient_Velayati_anonymized/sub-001_slice-0001.dcm
        try:
            # ارسال شناسه ثابت بیمار برای تمام اسلایس‌های متعلق به این اسکن
            anonymizer.process_file(
                input_path=str(file_path), # ۱. این فایل واقعی و خام را از دیسک بخوان
                output_path=str(target_file_path), # آدرس کامل فیزیکی روی هارد
                pseudo_patient_id=pseudo_patient_id
            )
            total_processed += 1
        except Exception as error:
            print(f"Failed to process {file_path.name}: {error}")

    print(f"\nSuccessfully processed and standardized {total_processed} files in: {output_path}")