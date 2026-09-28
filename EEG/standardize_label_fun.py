def standardize_label(raw_text: str):
    # remove white space at the end and start then, change to lower char
    text = raw_text.strip().lower()
    
    # remove device text
    if text.startswith("detections") or text.startswith("annotation"):
        return None
    
    # Bilateral tonic 
    if "tonic" in text and ("bil" in text or "bilateral" in text):
        return "seizure_bilateral_tonic"
    
    # Generalized tonic (G tonic)
    if "tonic" in text and text.startswith("g"):
        return "seizure_generalized_tonic"
    
    # myoclonic hand seizure
    if "myoclonic" in text:
        return "seizure_focal_myoclonic" 
    
    # unspecified seizures
    if text == "sz":
        return "seizure_unspecified"
    
    # Lob Frontal Slowing
    if "frontal" in text and "slow" in text:
        return"eeg_slowing_frontal_left"
    
    # fast wave bilateral (GPFA / Max BIF)
    if "bif" in text or "fast" in text:
        return "eeg_fast_activity_generalized"
    
    # else
    return "clinical_marker_other"