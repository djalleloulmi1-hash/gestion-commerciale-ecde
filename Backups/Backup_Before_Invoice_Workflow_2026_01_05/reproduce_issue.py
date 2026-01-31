def reproduce():
    # Scenario from Screenshot
    qty = 150.0
    price_init = 319.33
    remise_percent = 7.0
    
    price_net = price_init * (1 - (remise_percent / 100))
    # price_net is roughly 296.9769
    
    ht_raw = qty * price_net # 44546.535
    tva_rate = 0.19
    tva_raw = ht_raw * tva_rate # 8463.84165
    ttc_raw = ht_raw + tva_raw # 53010.37665
    
    # What the UI displays (f-string .2f)
    print(f"HT Raw: {ht_raw}")
    print(f"Display HT: {ht_raw:.2f}")
    
    print(f"TVA Raw: {tva_raw}")
    print(f"Display TVA: {tva_raw:.2f}")
    
    print(f"TTC Raw: {ttc_raw}")
    print(f"Display TTC: {ttc_raw:.2f}")
    
    # Check consistency
    disp_ht = float(f"{ht_raw:.2f}")
    disp_tva = float(f"{tva_raw:.2f}")
    disp_ttc = float(f"{ttc_raw:.2f}")
    
    computed_ttc = disp_ht + disp_tva
    
    print(f"Sum of Displayed HT + TVA: {computed_ttc:.2f}")
    print(f"Difference: {abs(disp_ttc - computed_ttc):.2f}")
    
    if abs(disp_ttc - computed_ttc) > 0.001:
        print("FAIL: Visual Mismatch Detected")
    else:
        print("PASS: Visually Consistent")

if __name__ == "__main__":
    reproduce()
