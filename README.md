# BIDS Medical Multimodal Dataset (_EEG/MRI Anonymizer_)

In medical images such as `MRI`, and electrophysiological  signal such as `EEG`, according to `HIPAA Safe Hurbor (45 CFR § 164.514)` and `DICOM PS 3.15`, we have to apply some rules on their data which comes from organization.

The BIDS standard for structural/functional neuroimaging (MRI/CT) strictly requires images in NIfTI format (.nii or .nii.gz) accompanied by a JSON sidecar file (.json)

Under the BIDS-EEG extension (

Pernet et al., 2019
), EDF (.edf), BrainVision (.vhdr), BDF (.bdf), and EEGLAB (.set) are officially accepted first-class formats directly in the BIDS root.
mne_bids.write_raw_bids() handles complete BIDS export:
When writing the EEG data, mne_bids sanitizes the binary header, applies the date shift (shift_days), and writes:
bids_root/sub-01/ses-01/eeg/sub-01_ses-01_task-ltm_run-01_eeg.edf
Corresponding sidecars: *_channels.tsv, *_eeg.json, *_events.tsv, and *_scans.tsv.
Because the de-identified .edf file with its sidecars is already 100% BIDS-compliant, no secondary conversion format (like NIfTI) is needed.

References
----------
Appelhoff, S., Sanderson, M., Brooks, T., Vliet, M., Quentin, R., Holdgraf, C., Chaumon, M., Mikulan, E., Tavabi, K., Höchenberger, R., Welke, D., Brunner, C., Rockhill, A., Larson, E., Gramfort, A. and Jas, M. (2019). MNE-BIDS: Organizing electrophysiological data into the BIDS format and facilitating their analysis. Journal of Open Source Software 4: (1896).https://doi.org/10.21105/joss.01896

Pernet, C. R., Appelhoff, S., Gorgolewski, K. J., Flandin, G., Phillips, C., Delorme, A., Oostenveld, R. (2019). EEG-BIDS, an extension to the brain imaging data structure for electroencephalography. Scientific Data, 6, 103.https://doi.org/10.1038/s41597-019-0104-8

