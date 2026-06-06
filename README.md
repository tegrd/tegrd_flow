# TEGRD Flow – HomeAssistant integrace

Lokální integrace pro zařízení **TEGRD Flow** (regulace přetoků fotovoltaiky). Komunikuje přímo se zařízením v lokální síti přes HTTP API – nevyžaduje cloud ani internet.

## Funkce

- Senzory:
  - SSR 1 / SSR 2 (výkon v %)
  - Přetoky aktuální i průměrné (W)
  - Maximální nastavený výkon SSR výstupů (W)
  - WiFi signál (dBm), doba běhu, verze firmware
- Binární senzory:
  - Regulace přetoků (zapnuto/vypnuto)
  - Manuální režim
  - Harmonogram aktivní
  - Spot ceny aktivní

## Instalace přes HACS (doporučeno)

1. V HomeAssistantu otevři **HACS → Integrations**
2. Klikni na ⋮ vpravo nahoře → **Custom repositories**
3. Vlož URL: `https://github.com/tegrd/tegrd_flow`
4. Kategorie: **Integration**
5. Klikni **Add** a vyhledej "TEGRD Flow" → **Install**
6. Restartuj HomeAssistant

## Manuální instalace

1. Stáhni složku `custom_components/tegrd_flow` z tohoto repa
2. Zkopíruj ji do `<config>/custom_components/tegrd_flow/` ve své HA instalaci
3. Restartuj HomeAssistant

## Nastavení

Po instalaci:

1. **Settings → Devices & Services → Add Integration**
2. Vyhledej **TEGRD Flow**
3. Zadej **IP adresu** zařízení v lokální síti (např. `192.168.1.50`)
4. Volitelně název

Integrace si automaticky dotáhne sériové číslo a vytvoří entity.

## Požadavky

- HomeAssistant 2024.1.0 nebo novější
- TEGRD Flow zařízení s firmware **0.6.6a** nebo novějším
- Zařízení musí být dostupné v lokální síti (stejná podsíť jako HA)

## Polling interval

Integrace polluje zařízení každých **10 sekund**. Lze upravit v `custom_components/tegrd_flow/const.py` → `DEFAULT_SCAN_INTERVAL`.

## Podpora

Issues: https://github.com/tegrd/tegrd_flow/issues
