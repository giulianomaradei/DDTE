import astropy.stats as s
from scipy import ndimage
import numpy as np
import astropy.wcs as wcs
from astropy.io import fits


#multi line comment

"""
1. difference → Matriz com diferenças (science - reference)
   ↓
2. threshold → Valor de corte (5 × desvio padrão)
   ↓
3. significant_mask → Pixels que mudaram muito (True/False)
   ↓
4. labeled → Agrupa pixels True que estão juntos
   ↓
5. Para cada grupo:
   - Calcular área (quantos pixels)
   - Filtrar se área < min_area
   ↓
6. Calcular propriedades:
   - Centroide (onde está)
   - Fluxo (quanto brilhou)
   - SNR (quão confiável)
   ↓
7. Filtrar:
   - SNR >= min_snr?
   - Não está na borda?
   ↓
8. Se passou todos os filtros → É um evento! 🎉
   ↓
9. Guardar na lista de eventos
   ↓
10. Ordenar por SNR (melhores primeiro)
"""

def process(reference_image, science_image):
    THRESHOLD_MULTIPLIER = 5
    MIN_AREA = 10
    MIN_SNR = 10
    BORDER_SIZE = 100

    science_wcs = wcs.WCS(science_image.header)

    reference_image_data = reference_image.data
    science_image_data = science_image.data

    difference = science_image_data - reference_image_data

    # wrute the difference image to a fits file
    fits.writeto("difference.fits", difference, science_image.header, overwrite=True)

    # Filtrar NaNs antes de calcular estatísticas
    valid_difference = difference[~np.isnan(difference)]
    if len(valid_difference) == 0:
        print("Error: All pixels are NaN in difference image")
        return []

    mean, median, deviation = s.sigma_clipped_stats(valid_difference)

    print(f"Mean: {mean}, Median: {median}, Deviation: {deviation}")

    # limit for the difference
    threshold = deviation * THRESHOLD_MULTIPLIER

    print(f"Threshold: {threshold}")


    positive_mask = difference > threshold
    negative_mask = difference < -threshold
    significant_mask = positive_mask | negative_mask

    # breaking the significant_mask into groups so we can compare them separately (each group is a potential event)
    labeled_mask, num_features = ndimage.label(significant_mask)

    events = []
    for i in range(1, num_features + 1):
        feature_mask = labeled_mask == i
        area = np.sum(feature_mask)

        if area < MIN_AREA:
            continue

        # calculating the centroid of the possible event
        centroid = ndimage.center_of_mass(feature_mask)

        # Create a valid mask that excludes NaN values in difference
        # This is important because reprojected images may have NaN pixels
        # outside the original coverage area
        valid_mask = feature_mask & ~np.isnan(difference)

        # Check if we have any valid pixels
        valid_area = np.sum(valid_mask)
        if valid_area < MIN_AREA:
            print(f"Skipping feature {i}: not enough valid pixels ({valid_area} < {MIN_AREA})")
            continue

        # flux is how mutch the event data changed compared to the reference data
        # Only sum over valid (non-NaN) pixels
        flux = np.sum(difference[valid_mask])
        print(f"Flux: {flux}")

        # Check for NaN or invalid flux
        if np.isnan(flux) or np.isinf(flux):
            print(f"Skipping feature {i}: invalid flux ({flux})")
            continue

        # Calcular o ruído como o desvio padrão dos pixels válidos na região do evento
        # ou usar o desvio padrão global já calculado
        noise = deviation  # ou np.std(difference[valid_mask])
        snr = flux / (noise * np.sqrt(valid_area))  # SNR considerando a área

        # Check for NaN or invalid SNR
        if np.isnan(snr) or np.isinf(snr):
            print(f"Skipping feature {i}: invalid SNR ({snr})")
            continue

        print(f"SNR: {snr}")

        if snr < MIN_SNR:
            print(f"Skipping feature {i}: SNR is too low ({snr} < {MIN_SNR})")
            continue

        # not in the border
        if centroid[0] < BORDER_SIZE or centroid[0] > reference_image_data.shape[0] - BORDER_SIZE or centroid[1] < BORDER_SIZE or centroid[1] > reference_image_data.shape[1] - BORDER_SIZE:
            print(f"Skipping feature {i}: centroid is in the border ({centroid})")
            continue

        # converting the centroid to ra and dec
        ra, dec = science_wcs.pixel_to_world_values(centroid[1], centroid[0])

        # it's a event
        print(f"Event found at {centroid} with flux {flux} and SNR {snr}")
        events.append({
            "centroid": centroid,
            "flux": flux,
            "snr": snr,
            "ra": ra,
            "dec": dec,
            "area": valid_area
        })

    print(f"Found {len(events)} events")

    # Ordenar eventos por SNR (maior primeiro)
    events.sort(key=lambda x: x['snr'], reverse=True)

    return events