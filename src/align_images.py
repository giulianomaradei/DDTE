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
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import os


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


def align_images(fits_files, output_dir):
    """
    Alinhar todas as imagens para a primeira como referência

    Parameters
    ----------
    fits_files : list
        Lista de caminhos para arquivos FITS
    output_dir : Path
        Diretório para salvar imagens alinhadas
    """

    if len(fits_files) == 0:
        print("❌ Nenhum arquivo FITS encontrado!")
        return

    print(f"\n{'='*60}")
    print(f"ALINHAMENTO DE IMAGENS")
    print(f"{'='*60}")
    print(f"Total de imagens: {len(fits_files)}")

    # Criar diretório de saída
    output_dir.mkdir(exist_ok=True, parents=True)

    # Carregar imagem de referência (primeira)
    print(f"\n📍 Usando como referência: {Path(fits_files[0]).name}")
    ref_data, ref_wcs, ref_header = load_fits_image(fits_files[0])
    ref_shape = ref_data.shape

    print(f"   Dimensões: {ref_shape}")
    print(f"   Centro (RA, Dec): ", end="")
    center_ra, center_dec = ref_wcs.all_pix2world(ref_shape[1]//2, ref_shape[0]//2, 0)
    print(f"({center_ra:.6f}°, {center_dec:.6f}°)")

    # Salvar referência (cópia)
    ref_output = output_dir / "0_reference.fits"
    fits.writeto(ref_output, ref_data, ref_header, overwrite=True)
    print(f"   ✓ Salva em: {ref_output}")

    # Lista para visualização depois
    aligned_images = [ref_data]
    footprints = [np.ones_like(ref_data, dtype=float)]  # footprint de referência = 1.0
    filenames = [Path(fits_files[0]).name]

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
            output_file = output_dir / f"{i}_aligned_{filename}"

            # Atualizar header com informações
            new_header = ref_header.copy()
            new_header['COMMENT'] = f'Aligned from {filename}'
            new_header['ALIGNED'] = True
            new_header['COVERAGE'] = (coverage, 'Percentage of valid pixels')

            fits.writeto(output_file, aligned, new_header, overwrite=True)
            print(f"   ✓ Salva em: {output_file}")

            # Guardar para visualização
            aligned_images.append(aligned)
            footprints.append(footprint)
            filenames.append(filename)

        except Exception as e:
            print(f"   ❌ ERRO: {e}")
            continue

    print(f"\n{'='*60}")
    print(f"✓ Alinhamento completo!")
    print(f"  Imagens alinhadas salvas em: {output_dir}")
    print(f"{'='*60}")

    return aligned_images, footprints, filenames


def visualize_alignment(aligned_images, footprints, filenames, output_dir):
    """
    Criar visualizações para comparar as imagens alinhadas
    """

    n_images = len(aligned_images)

    if n_images == 0:
        return

    print(f"\n{'='*60}")
    print("CRIANDO VISUALIZAÇÕES...")
    print(f"{'='*60}")

    # Criar subplots mostrando cada imagem
    n_cols = min(3, n_images)
    n_rows = (n_images + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 5*n_rows))

    if n_images == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    # Calcular percentis para normalização consistente
    all_valid_data = np.concatenate([
        img[~np.isnan(img)].flatten() for img in aligned_images
    ])
    vmin, vmax = np.percentile(all_valid_data, [1, 99])

    print(f"Intervalo de visualização: [{vmin:.2f}, {vmax:.2f}]")

    for i, (img, fp, fname) in enumerate(zip(aligned_images, footprints, filenames)):
        ax = axes[i]

        # Mostrar imagem
        im = ax.imshow(img, origin='lower', cmap='gray', vmin=vmin, vmax=vmax)

        # Destacar bordas sem dados (footprint)
        mask_display = np.ma.masked_where(fp, np.ones_like(img))
        ax.imshow(mask_display, origin='lower', cmap='Reds', alpha=0.3)

        # Título
        ax.set_title(f"{i}: {fname[:40]}\nCobertura: {np.sum(fp)/fp.size*100:.1f}%",
                     fontsize=8)
        ax.axis('off')

    # Esconder axes extras
    for i in range(n_images, len(axes)):
        axes[i].axis('off')

    plt.tight_layout()

    # Salvar visualização
    viz_file = output_dir / "alignment_visualization.png"
    plt.savefig(viz_file, dpi=150, bbox_inches='tight')
    print(f"✓ Visualização salva: {viz_file}")

    # Criar visualização dos footprints
    fig2, axes2 = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 5*n_rows))

    if n_images == 1:
        axes2 = np.array([axes2])
    axes2 = axes2.flatten()

    for i, (fp, fname) in enumerate(zip(footprints, filenames)):
        ax = axes2[i]

        # Mostrar footprint
        ax.imshow(fp, origin='lower', cmap='viridis', vmin=0, vmax=1)
        ax.set_title(f"{i}: {fname[:40]}\nÁrea válida: {np.sum(fp)/fp.size*100:.1f}%",
                     fontsize=8)
        ax.axis('off')

    # Esconder axes extras
    for i in range(n_images, len(axes2)):
        axes2[i].axis('off')

    plt.tight_layout()

    # Salvar visualização de footprints
    fp_file = output_dir / "footprints_visualization.png"
    plt.savefig(fp_file, dpi=150, bbox_inches='tight')
    print(f"✓ Footprints salvos: {fp_file}")

    # Criar visualização da sobreposição (comum a todas)
    if n_images > 1:
        print("\nCalculando área de sobreposição comum...")

        # Área comum = AND de todos os footprints (converter para boolean)
        common_area = (footprints[0] > 0).astype(bool)
        for fp in footprints[1:]:
            common_area = common_area & (fp > 0).astype(bool)

        coverage_common = np.sum(common_area) / common_area.size * 100
        print(f"  Área comum a TODAS as imagens: {coverage_common:.1f}%")

        fig3, ax3 = plt.subplots(1, 1, figsize=(8, 8))
        ax3.imshow(common_area, origin='lower', cmap='RdYlGn', vmin=0, vmax=1)
        ax3.set_title(f"Área de Sobreposição Comum\n{coverage_common:.1f}% da imagem de referência",
                      fontsize=12)
        ax3.axis('off')

        overlap_file = output_dir / "common_overlap.png"
        plt.savefig(overlap_file, dpi=150, bbox_inches='tight')
        print(f"✓ Sobreposição salva: {overlap_file}")

    print(f"\n{'='*60}")
    print("✓ Visualizações criadas!")
    print(f"{'='*60}")


def main():
    """Função principal"""

    # ============================================
    # CONFIGURAÇÃO: Limitar número de imagens
    # ============================================
    MAX_IMAGES = 20  # None para processar todas

    # Diretórios
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    output_dir = project_root / "output" / "aligned"

    print(f"\n{'='*60}")
    print("ALINHAMENTO DE IMAGENS FITS")
    print(f"{'='*60}")
    print(f"Diretório de dados: {data_dir}")
    print(f"Diretório de saída: {output_dir}")

    # Encontrar arquivos FITS
    print(f"\nProcurando arquivos FITS...")
    fits_files = find_fits_files(data_dir)

    if len(fits_files) == 0:
        print(f"\n❌ Nenhum arquivo FITS encontrado em {data_dir}")
        print("\nColoque arquivos .fits na pasta 'data' e execute novamente.")
        return

    print(f"✓ Encontrados {len(fits_files)} arquivo(s) FITS")

    # Limitar número de imagens se configurado
    if MAX_IMAGES is not None and len(fits_files) > MAX_IMAGES:
        print(f"⚠ Limitando para {MAX_IMAGES} imagens (configurado em MAX_IMAGES)")
        fits_files = fits_files[:MAX_IMAGES]

    # Alinhar imagens
    aligned_images, footprints, filenames = align_images(fits_files, output_dir)

    # Criar visualizações
    if len(aligned_images) > 0:
        visualize_alignment(aligned_images, footprints, filenames, output_dir)

    print(f"\n{'='*60}")
    print("CONCLUÍDO! 🎉")
    print(f"{'='*60}")
    print(f"\nVerifique os resultados em: {output_dir}")
    print(f"  - Imagens alinhadas: *_aligned_*.fits")
    print(f"  - Visualizações: *.png")


if __name__ == "__main__":
    main()

