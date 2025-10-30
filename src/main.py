#!/usr/bin/env python3
"""
Script simples para verificar se uma imagem FITS tem WCS
"""

from astropy.io import fits
from astropy.wcs import WCS

# Caminho para sua imagem FITS
fits_file = "data/sci/2023/0726/348762/ztf_20230726348762_000796_zg_c11_o_q1_sciimg.fits"

print(f"Verificando: {fits_file}\n")

# Abrir arquivo
hdu = fits.open(fits_file)[0]
header = hdu.header

# Tentar criar WCS
wcs = WCS(header)

# Verificar se tem WCS
if wcs.has_celestial:
    print("✓ TEM WCS!\n")
    print(wcs)

    # Exemplo: converter pixel do centro para coordenadas
    if hdu.data is not None:
        center_x = hdu.data.shape[1] // 2
        center_y = hdu.data.shape[0] // 2
        ra, dec = wcs.all_pix2world(center_x, center_y, 0)
        print(f"\nCentro da imagem:")
        print(f"  Pixel: ({center_x}, {center_y})")
        print(f"  RA: {ra:.6f}°")
        print(f"  Dec: {dec:.6f}°")
else:
    print("✗ NÃO TEM WCS")
