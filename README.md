# osrs_info

**Lightweight, dependency-minimal OSRS Hiscores + GE Price Decoder.**

`osrs_info` provides:

- 📊 **Hiscores API decoding** (skills, clues, bosses, PvP)
- 💰 **Grand Exchange price lookups** using the OSRS Wiki price API
- 🧹 **Tradeable-only item filtering** (no corrupted/charged/seasonal junk)
- 🔎 **Smart item searching** (substring + optional fuzzy matching)
- 🧩 A unified high-level interface: `Decoder`

Perfect for bots, dashboards, game integrations, analytics scripts, and automation.

---

## 🚀 Installation

### Core package (no fuzzy search)
```bash
pip install osrs_info

# With fuzzy item search (RapidFuzz)

pip install "osrs_info[fuzzy]"
