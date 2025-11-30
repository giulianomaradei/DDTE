from ccdproc import CCDData, Combiner
import astropy.units as u
from pathlib import Path
import gc

def process(files_dir, max_images=None):
    """
    Combina imagens FITS de um diretório específico usando median combine.

    Args:
        files_dir: Diretório contendo as imagens FITS a serem combinadas
        max_images: Número máximo de imagens a carregar (None para todas)

    Returns:
        CCDData: Imagem combinada usando median
    """
    print(f"Combining images in {files_dir}")

    # Convert to Path object if it isn't already
    files_dir = Path(files_dir)

    # Find all FITS files
    fits_files = sorted(files_dir.glob('*.fits'))

    if len(fits_files) == 0:
        raise ValueError(f"No FITS files found in {files_dir}")

    print(f"Found {len(fits_files)} FITS files")

    # Limitar número de imagens se especificado
    if max_images is not None and len(fits_files) > max_images:
        fits_files = fits_files[:max_images]
        print(f"Limiting to {max_images} images")

    # Load all FITS files as CCDData objects
    # Pass unit='adu' to handle invalid BUNIT header values like "Data Value"
    # ADU (Analog-to-Digital Units) is the standard unit for CCD data
    ccd_list = []
    for fits_file in fits_files:
        ccd = CCDData.read(fits_file, unit=u.adu)
        ccd_list.append(ccd)
        print(f"  ✓ Loaded {fits_file.name}")

    c = Combiner(ccd_list)
    print(f"\nUsing sigma-clipped median...")
    c.sigma_clipping()

    print(f"\nCombining {len(ccd_list)} images using median...")
    median_combined = c.median_combine()
    print("✓ Combination complete")

    # Limpar lista de imagens da memória após combinação
    del ccd_list, c
    gc.collect()

    return median_combined
