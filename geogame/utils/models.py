from dataclasses import dataclass


@dataclass
class CityInDb:
    geoname_id: str
    name: str
    ascii_name: str
    alternate_names: str
    feature_class: str
    feature_code: str
    country_code: str
    country_name_en: str
    country_code_2: str
    admin1_code: str
    admin2_code: str
    admin3_code: str
    admin4_code: str
    population: int
    elevation: int
    digital_elevation_model: str
    timezone: str
    timezone_general: str
    modification_date: str
    label_en: str
    coordinates: str
