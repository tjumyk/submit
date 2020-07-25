from typing import Optional

import geoip2.database
from geoip2.errors import AddressNotFoundError


class IPTool:
    _geo_country_db = None
    _is_behind_proxy = False

    @classmethod
    def init_app(cls, app):
        cls._is_behind_proxy = app.config['SITE'].get('behind_proxy')
        geo_ip_config = app.config.get('GEOIP')
        if geo_ip_config:
            country_db_path = geo_ip_config.get('country')
            if country_db_path:
                cls._geo_country_db = geoip2.database.Reader(country_db_path)

    @classmethod
    def get_ip_country(cls, ip_addr: str) -> Optional[str]:
        if cls._geo_country_db is None:
            return None
        try:
            country = cls._geo_country_db.country(ip_addr)
            if country:
                return country.country.iso_code
        except AddressNotFoundError:
            pass
        return None

    @classmethod
    def get_client_ip(cls, request) -> str:
        if cls._is_behind_proxy:
            ip = request.environ.get('HTTP_X_REAL_IP') or request.remote_addr
        else:
            ip = request.remote_addr
        return ip
