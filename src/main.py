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
    MAX_SCIENCE_IMAGES_PER_FILTER = 20  # Limite de imagens de ciência a processar por filtro

    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"

    fits_files = find_fits_files(data_dir)

    if MAX_IMAGES is not None and len(fits_files) == 0:
        print(f"\n❌ Nenhum arquivo FITS encontrado em {data_dir}")
        return

    if MAX_IMAGES is not None and len(fits_files) > MAX_IMAGES:
        fits_files = fits_files[:MAX_IMAGES]

    # output_dir = align_images.process(fits_files)
    output_dir = Path("/media/giuliano/Disco D/DDTE/output/aligned")

    print(f"Output directory: {output_dir}")

    # Filtros disponíveis
    filters = ['ZTF_r']

    all_events = []

    # Processar cada filtro separadamente
    for filter_name in filters:
        filter_dir = output_dir / filter_name

        if not filter_dir.exists():
            print(f"\n⚠️  Diretório {filter_dir} não existe, pulando filtro {filter_name}")
            continue

        print(f"\n{'='*60}")
        print(f"PROCESSANDO FILTRO: {filter_name}")
        print(f"{'='*60}")

        # Encontrar imagens deste filtro
        filter_images = sorted(filter_dir.glob('*.fits'))

        if len(filter_images) == 0:
            print(f"⚠️  Nenhuma imagem encontrada para o filtro {filter_name}")
            continue

        print(f"Encontradas {len(filter_images)} imagens no filtro {filter_name}")

        # Criar imagem de referência combinada apenas com imagens deste filtro
        print(f"\nCriando imagem de referência combinada para {filter_name}...")
        try:
            median_combined = combine_images.process(filter_dir, max_images=20)
            reference_file = filter_dir / f"median_combined_{filter_name}.fits"
            median_combined.write(reference_file, overwrite=True)
            print(f"✓ Referência combinada salva em: {reference_file}")
        except Exception as e:
            print(f"❌ Erro ao criar referência combinada: {e}")
            continue

        # Processar cada imagem de ciência deste filtro
        print(f"\nProcessando imagens de ciência do filtro {filter_name}...")
        loop_count = 0

        for fits_file in filter_images:
            # Pular a própria imagem de referência combinada
            if 'median_combined' in fits_file.name:
                continue

            print(f"\n[{loop_count + 1}] Processando {fits_file.name}")

            try:
                science_image = CCDData.read(fits_file, unit=u.adu)
                print(f"  EXPTIME: {science_image.header.get('EXPTIME', 'N/A')}")

                events = detect_events.process(median_combined, science_image)

                # Adicionar informação do filtro aos eventos
                for event in events:
                    event['filter'] = filter_name
                    event['science_image'] = fits_file.name

                all_events.extend(events)
                print(f"  ✓ Encontrados {len(events)} eventos nesta imagem")

                # Limpar imagem da memória após processar
                del science_image

                # Forçar garbage collection a cada 10 imagens
                loop_count += 1
                if loop_count % 10 == 0:
                    gc.collect()

                if loop_count >= MAX_SCIENCE_IMAGES_PER_FILTER:
                    print(f"  ⚠️  Limite de {MAX_SCIENCE_IMAGES_PER_FILTER} imagens atingido para este filtro")
                    break

            except Exception as e:
                print(f"  ❌ Erro ao processar {fits_file.name}: {e}")
                continue

        # Limpar referência combinada da memória após processar todas as imagens do filtro
        del median_combined
        gc.collect()

        print(f"\n✓ Filtro {filter_name} processado: {loop_count} imagens, {len([e for e in all_events if e.get('filter') == filter_name])} eventos totais")

    # Resumo final
    print(f"\n{'='*60}")
    print(f"RESUMO FINAL")
    print(f"{'='*60}")
    print(f"Total de eventos encontrados: {len(all_events)}")

    # Estatísticas por filtro
    for filter_name in filters:
        filter_events = [e for e in all_events if e.get('filter') == filter_name]
        print(f"  {filter_name}: {len(filter_events)} eventos")

    # Ordenar todos os eventos por SNR (maior primeiro)
    all_events.sort(key=lambda x: x.get('snr', 0), reverse=True)

    print(f"\nTop 10 eventos (por SNR):")
    for i, event in enumerate(all_events[:10], 1):
        print(f"  {i}. SNR={event.get('snr', 0):.2f}, Filter={event.get('filter', 'N/A')}, "
              f"RA={event.get('ra', 0):.6f}, DEC={event.get('dec', 0):.6f}")

if __name__ == "__main__":
    main()