import align_images
import combine_images
import glob
from pathlib import Path

def find_fits_files(data_dir):
    """Encontrar todos os arquivos FITS no diretório"""
    patterns = ['**/*.fits', '**/*.fit', '**/*.fts']
    fits_files = []

    for pattern in patterns:
        fits_files.extend(glob.glob(str(data_dir / pattern), recursive=True))

    return sorted(fits_files)

def main():
    MAX_IMAGES = 3  # None para processar todas

    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"

    fits_files = find_fits_files(data_dir)

    if MAX_IMAGES is not None and len(fits_files) == 0:
        print(f"\n❌ Nenhum arquivo FITS encontrado em {data_dir}")
        return

    if len(fits_files) > MAX_IMAGES:
        fits_files = fits_files[:MAX_IMAGES]

    output_dir = align_images.process(fits_files)

    print(f"Output directory: {output_dir}")

    avg_combined = combine_images.process(output_dir)

    avg_combined.write(output_dir / "avg_combined.fits")


if __name__ == "__main__":
    main()