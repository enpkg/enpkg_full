from pyteomics import mzml

def extract_injection_mode(mzml_file):
    injection_mode = None
    with mzml.read(mzml_file) as reader:
        for spectrum in reader:
            # Check if injection mode is available in spectrum metadata
            if 'positive scan' in spectrum:
                injection_mode = "pos"
                break
            elif 'negative scan' in spectrum:
                injection_mode = "neg"
                break
    return injection_mode

# Replace 'your_file.mzML' with the path to your .mzML file
mzml_file = '202404101527_EB_dbgi_001189_01_01.mzML'
injection_mode = extract_injection_mode(mzml_file)
print("Injection mode:", injection_mode)