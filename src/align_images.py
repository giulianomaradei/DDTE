#!/usr/bin/env python3
"""
Script para alinhar múltiplas imagens FITS usando reprojeção WCS
"""

import glob
import numpy as np
from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS
from reproject import reproject_interp
import gc


def find_fits_files(data_dir):
    """Encontrar todos os arquivos FITS no diretório"""
    patterns = ['**/*.fits', '**/*.fit', '**/*.fts']
    fits_files = []

    for pattern in patterns:
        fits_files.extend(glob.glob(str(data_dir / pattern), recursive=True))

    return sorted(fits_files)


def load_fits_image(filepath):
    """Carregar imagem FITS e seu WCS"""
    with fits.open(filepath) as hdul:
        data = hdul[0].data
        header = hdul[0].header
        wcs = WCS(header)
    return data, wcs, header


def process(fits_files):
    # Diretórios
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "output" / "aligned"
    red_filter_dir = output_dir / "ZTF_r"
    green_filter_dir = output_dir / "ZTF_g"
    infrared_filter_dir = output_dir / "ZTF_i"

    filter_type_to_dir = {
        'ZTF_r': red_filter_dir,
        'ZTF_g': green_filter_dir,
        'ZTF_i': infrared_filter_dir
    }

    print("ALINHAMENTO DE IMAGENS FITS")

    print(f"\n{'='*60}")
    print(f"ALINHAMENTO DE IMAGENS")
    print(f"{'='*60}")
    print(f"Total de imagens: {len(fits_files)}")

    # Criar diretório de saída
    output_dir.mkdir(exist_ok=True, parents=True)
    red_filter_dir.mkdir(exist_ok=True, parents=True)
    green_filter_dir.mkdir(exist_ok=True, parents=True)
    infrared_filter_dir.mkdir(exist_ok=True, parents=True)


    # Carregar imagem de referência (primeira)
    print(f"\n📍 Usando como referência: {Path(fits_files[0]).name}")
    ref_data, ref_wcs, ref_header = load_fits_image(fits_files[0])
    ref_shape = ref_data.shape

    print('BUNIT: ', ref_header['BUNIT'])


    # Salvar referência (cópia)
    ref_output = output_dir / "0_reference.fits"
    fits.writeto(ref_output, ref_data, ref_header, overwrite=True)
    print(f"   ✓ Salva em: {ref_output}")

    # Limpar referência da memória após salvar (não precisamos manter em memória)
    del ref_data

    # Reprojetar todas as outras imagens
    print(f"\n{'='*60}")
    print("REPROJETANDO IMAGENS...")
    print(f"{'='*60}")

    for i, fits_file in enumerate(fits_files[1:], start=1):
        filename = Path(fits_file).name
        print(f"\n[{i}/{len(fits_files)-1}] {filename}")

        try:
            # Carregar imagem
            data, wcs, header = load_fits_image(fits_file)
            print(f"   Dimensões originais: {data.shape}")

            # Reprojetar para o WCS de referência
            print(f"   Reprojetando...", end=" ")
            aligned, footprint = reproject_interp(
                (data, wcs),
                ref_wcs,
                shape_out=ref_shape
            )
            print("✓")

            # Calcular estatísticas
            valid_pixels = np.sum(footprint)
            total_pixels = footprint.size
            coverage = (valid_pixels / total_pixels) * 100

            print(f"   Cobertura: {coverage:.1f}% ({valid_pixels}/{total_pixels} pixels)")
            print(f"   NaNs: {np.sum(np.isnan(aligned))}")

            # Salvar imagem alinhada
            filter_type = header['FILTER']
            print(f"Filter type: {filter_type}")
            filter_dir = filter_type_to_dir[filter_type]


            output_file = filter_dir / f"{i}_aligned_{filename}"

            # Atualizar header com informações
            new_header = ref_header.copy()
            new_header['DATE-OBS'] = header.get('DATE-OBS', '')
            new_header['EXPTIME'] = header.get('EXPTIME', '')
            new_header['FILTER'] = header.get('FILTER', '')

            print('BUNIT: ', new_header['BUNIT'])

            fits.writeto(output_file, aligned, new_header, overwrite=True)
            print(f"   ✓ Salva em: {output_file}")

            # Limpar dados da memória após salvar
            del data, aligned, footprint, wcs, header, new_header

            # Forçar garbage collection a cada 10 imagens para liberar memória
            if i % 10 == 0:
                gc.collect()

        except Exception as e:
            print(f"   ❌ ERRO: {e}")
            # Garantir limpeza mesmo em caso de erro
            if 'data' in locals():
                del data
            if 'aligned' in locals():
                del aligned
            if 'footprint' in locals():
                del footprint
            continue

    print(f"\n{'='*60}")
    print(f"✓ Alinhamento completo!")
    print(f"  Imagens alinhadas salvas em: {output_dir}")
    print(f"{'='*60}")

    return output_dir