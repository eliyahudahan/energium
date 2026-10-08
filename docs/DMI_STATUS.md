# DMI API — Day 2 Status

## 2026-10-08 12:50 UTC

### Authentication — NOT REQUIRED
Source: DMI Open Data -> Authentication page
Quote: "From December 2, 2025, authentication and API keys are no longer
required to access our APIs via opendataapi.dmi.dk."
Consequence: direct access to all endpoints.

### Fair use
Rate limiting applies if abuse detected.

### Base URL
https://opendataapi.dmi.dk/v2/metObs/

### Verified endpoint (tested, working)
GET https://opendataapi.dmi.dk/v2/metObs/collections/observation/items

### Response format
GeoJSON FeatureCollection (application/geo+json)

### Response schema (from live test)
- features[].id            : UUID
- features[].geometry      : Point [lon, lat]
- features[].properties:
    - parameterId : string (e.g. "temp_dry")
    - value       : number
    - observed    : ISO8601 (UTC)
    - stationId   : string (e.g. "04224")
    - created     : ISO8601 (UTC)
- numberReturned : int
- links[].rel="next" : pagination via offset

### Open questions (Day 3)
1. Station IDs for DK1 region (need DK stations, not Greenland)
2. Filtering by parameterId (wind_speed, wind_dir)
3. Filtering by datetime range
4. Max value of `limit`
5. Separate endpoint for station list?

### Next steps (Day 3)
- Read DMI OpenAPI spec for filter syntax
- Fetch station list, filter DK1
- Test wind_speed + wind_dir for one station, one day
