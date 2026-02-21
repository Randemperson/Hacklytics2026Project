# Housing Data — Provenance & Sources

## About `housing_data.csv`

`housing_data.csv` is a **synthetic dataset** created for this project.
The listings, agent names, phone numbers, and email addresses are entirely
**fictitious**. No real rental listings, real landlords, or real people are
represented.

The data was hand-crafted to reflect realistic affordable-housing patterns in
the **Atlanta, GA metro area**:
- Rent levels match approximate 2024 market rates for affordable/subsidized
  units in Atlanta and surrounding suburbs.
- Neighbourhood names, ZIP codes, and street names are real Atlanta locations.
- Agent languages reflect the demographic diversity of each neighborhood
  (e.g. Buford Highway corridor → Chinese/Vietnamese/Spanish; Decatur →
  Somali/Amharic; Norcross → Hindi/Gujarati).
- All phone numbers use the `555` exchange (US fictional-number convention).
- All email addresses use fictitious domains (e.g. `atlantarealty.com` is
  used as a placeholder, not the real website).

## Why Not Use Real Data?

Real affordable-housing APIs typically require:
- Registration or API keys
- Acceptance of terms that restrict redistribution
- Careful handling of personally identifiable information (PII)

Synthetic data removes those barriers so the AI features can be demonstrated
immediately without any sign-ups or legal concerns.

## How to Replace the Dataset with Real Data

The AI engine reads any CSV file that follows the same column schema. To use
real data:

1. Obtain a dataset from one of the sources listed below.
2. Rename / add columns to match the schema (see the README's schema table).
3. Set the environment variable `DATA_PATH` to point to your file, **or**
   simply replace `data/housing_data.csv` in place.
4. Re-run the app — no code changes required.

```bash
# Option A: replace the file
cp /path/to/your/real_listings.csv data/housing_data.csv
python app.py

# Option B: point the app at a different file via the HousingAI constructor
python -c "
from src.housing_ai import HousingAI
ai = HousingAI(data_path='/path/to/your/real_listings.csv')
print(ai.get_cities())
"
```

## Public Data Sources

### Federal / National

| Source | URL | Format | Notes |
|--------|-----|--------|-------|
| HUD Fair Market Rents | https://www.huduser.gov/portal/datasets/fmr.html | Excel / CSV | Annual FMR by metro area and bedroom count |
| HUD LIHTC Database | https://lihtc.huduser.gov | CSV download | Every LIHTC-funded property in the US |
| HUD Multifamily Housing | https://www.hud.gov/program_offices/housing/mfh/exp/mfhdiscl | CSV | HUD-assisted multifamily properties |
| National Housing Preservation Database | https://preservationdatabase.org | API / CSV | Subsidised housing at risk of conversion |
| USDA Multi-Family Housing | https://www.rd.usda.gov/programs-services/multi-family-housing-programs | Web | Rural affordable housing |

### Georgia / Atlanta

| Source | URL | Notes |
|--------|-----|-------|
| Atlanta Housing Authority | https://atlantahousing.org | Public housing and Housing Choice Voucher program |
| Georgia DCA Housing Search | https://www.dca.ga.gov/safe-affordable-housing | State-level affordable housing locator |
| Georgia DCA LIHTC List | https://www.dca.ga.gov/safe-affordable-housing/rental-housing-development/programs/low-income-housing-tax-credits | Georgia LIHTC property list |
| City of Atlanta AHA Waitlist | https://www.atlantahousing.org/residents/apply-for-housing/ | Waitlist status and open enrollment |

### Rental Listing Aggregators (API / Data Exports)

| Source | URL | Notes |
|--------|-----|-------|
| Zillow Research Data | https://www.zillow.com/research/data | Free public CSV downloads (rent indices, inventory) |
| Realtor.com API | https://www.realtor.com/api | Requires free API key |
| RentCafe | https://www.rentcafe.com | Scraped data; check Terms of Service |
| Craigslist Housing | https://atlanta.craigslist.org/search/apa | Public listings; web scraping only (check ToS) |

### Geocoding & Neighbourhood Context

| Source | URL | Notes |
|--------|-----|-------|
| US Census Geocoder | https://geocoding.geo.census.gov | Free address → lat/lon |
| OpenStreetMap Nominatim | https://nominatim.openstreetmap.org | Free geocoding API |
| Atlanta Regional Commission | https://opendata.atlantaregional.com | Regional GIS and demographics |

## Extending the Dataset

The more listings you add, the better the AI recommendations become. When
adding your own data consider including:

- **`languages_spoken`** — this field drives the multilingual agent-matching
  feature. If agents speak multiple languages, separate them with commas
  (e.g. `"English,Spanish,Amharic"`).
- **`income_limit_percent_ami`** — the AMI % cap enables income-based
  filtering. Use the HUD Fair Market Rent / AMI tables for your metro area.
- **`accessibility_features`** — values like `Wheelchair ramp`, `Elevator`,
  `Visual alarms` enable the accessibility filter.
- **Latitude / longitude** — used for future map-view features. You can
  batch-geocode addresses with the US Census Geocoder (free, no key needed).
