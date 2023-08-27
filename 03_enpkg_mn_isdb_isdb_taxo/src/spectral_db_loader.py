from matchms.importing import load_from_mgf
from matchms.filtering import default_filters
from matchms.exporting import save_as_mgf


def load_spectral_db(path_to_db):
    """Load and clean metadata from a .mgf spectral database

    Args:
        path_to_db (str): Path to the .mgf file

    Returns:
        list: List of matchms spectra object
    """    
    
    print('''
    Cleaning the spectral database metadata fields
    ''')  
    spectrums_db = list(load_from_mgf(path_to_db))
    spectrums_db = [default_filters(s) for s in spectrums_db]
    print(f'''
    A total of {len(spectrums_db)} clean spectra were found in the spectral library
    ''')
    return spectrums_db

def load_clean_spectral_db(path_to_db):
    """Load and clean metadata from a .mgf spectral database

    Args:
        path_to_db (str): Path to the .mgf file

    Returns:
        list: List of matchms spectra object
    """    
    
    print('''
    Cleaning the spectral database metadata fields
    ''')  
    spectrums_db = list(load_from_mgf(path_to_db))
    print(f'''
    A total of {len(spectrums_db)} clean spectra were found in the spectral library
    ''')
    return spectrums_db


def save_spectral_db(spectrums_db, output_path):
    """Save a clean spectral db as .mgf from a matchms object

    Args:
        spectrums_db (var): cleaned spectrums_db (e.g. output of load_spectral_db())
        output_path (str): path to output

    Returns:
        list: List of matchms spectra object
    """    
    
    print('''
    Saving the spectral database
    ''')  
    save_as_mgf(spectrums_db, output_path)

    print(f'''
    A total of {len(spectrums_db)} clean spectra were found in the spectral library and saved as {output_path}
    ''')