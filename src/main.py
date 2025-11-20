import align_images
import combine_images
import detect_events
import glob
from pathlib import Path
from ccdproc import CCDData
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS
import gc

def find_fits_files(data_dir):
    """Encontrar todos os arquivos FITS no diretório"""
    patterns = ['**/*.fits', '**/*.fit', '**/*.fts']
    fits_files = []

    for pattern in patterns:
        fits_files.extend(glob.glob(str(data_dir / pattern), recursive=True))

    return sorted(fits_files)

def main():
    MAX_IMAGES = None # None para processar todas

    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"

    fits_files = find_fits_files(data_dir)

    if MAX_IMAGES is not None and len(fits_files) == 0:
        print(f"\n❌ Nenhum arquivo FITS encontrado em {data_dir}")
        return

    if MAX_IMAGES is not None and len(fits_files) > MAX_IMAGES:
        fits_files = fits_files[:MAX_IMAGES]

    output_dir = align_images.process(fits_files)
    # output_dir = Path("/media/giuliano/Disco D/DDTE/output/aligned")

    print(f"Output directory: {output_dir}")

    # median_combined = combine_images.process(output_dir)
    # median_combined.write(output_dir / "median_combined.fits", overwrite=True)


    aligned_images = find_fits_files(output_dir)
    # remove median_combined.fits from aligned_images
    aligned_images.remove(str(output_dir / "median_combined.fits"))

    # Sort by modification time (most recent first)
    aligned_images.sort(key=lambda f: Path(f).stat().st_mtime, reverse=True)

    median_combined = CCDData.read(output_dir / "median_combined.fits", unit=u.adu)
    loopCount = 0
    for fits_file in aligned_images:
        print(f"Processing {fits_file}")
        science_image = CCDData.read(fits_file, unit=u.adu)
        events = detect_events.process(median_combined, science_image)
        print(events)

        # Limpar imagem da memória após processar
        del science_image

        # Forçar garbage collection a cada 10 imagens
        loopCount += 1
        if loopCount % 10 == 0:
            gc.collect()

        if loopCount > 50:
            break

    print(f"Found {len(events)} events")
    print(events)
    exit()

if __name__ == "__main__":
    main()