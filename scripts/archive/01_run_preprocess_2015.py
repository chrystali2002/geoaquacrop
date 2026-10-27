# run_preprocess_2015.py

import geoaquacrop as gac

gac.preprocess.run(
    domain_shape_path=(
        "/mnt/scratch/olusegu3/geoaquacrop/"
        "story2012/story_county_wgs84.geojson"
    ),
    start_year=2015,
    end_year=2015,
    api_token="dd2dd460-ff2a-44f7-9f2b-4f02e6c9ea20",   #from cdsgmailact
    cell_resolution=0.05,
    workingdirectory=(
        "/mnt/scratch/olusegu3/geoaquacrop/story2015"
    )
)
