# import necessaries
import mne
from EEG.standardize_label import standardize_label

def cleaned_annotations(raw: mne.io.BaseRaw) -> mne.io.BaseRaw:
    # extract events from the raw
    old_annotations = raw.annotations
    
    # return raw if annotations was empty
    if old_annotations is None or len(old_annotations) == 0:
        return raw
    
    # temporary list
    tmp_onset = []
    tmp_duration = []
    tmp_description = []
    
    # navigation 
    for old_onset, old_duration, old_description in zip(old_annotations.onset, old_annotations.duration, old_annotations.description):
        
        # standardize label 
        label = standardize_label(old_description)
        
        # Filtering: if the result wasn't None, save items to the new
        if label is not None:
            tmp_onset.append(old_onset)
            tmp_duration.append(old_duration)
            tmp_description.append(label)
    
    # create a new standard fresh annotations object and keep the original time
    new_annotations = mne.Annotations(
        onset=tmp_onset,
        duration=tmp_duration,
        description=tmp_description,
        orig_time=old_annotations.orig_time
    )
    # set the created annotations to the raw signal
    raw.set_annotations(new_annotations)
    
    # return raw with 
    return raw