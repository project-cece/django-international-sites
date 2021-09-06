import os
import requests

from django.core.management.base import BaseCommand
from django.contrib.gis.geoip2 import GeoIP2
from django.conf import settings

import tarfile

PERMALINK = "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-Country&license_key={0}&suffix=tar.gz"

class Command(BaseCommand):
    help = "Check for updates of the GeoIP2 library and download if necessary"

    def handle(self, *args, **options):
        self.cmd = __file__.split("/")[-1].replace(".py", "")

        self.stdout.write(self.style.SUCCESS('Successfully starting check for GeoIP2 library updates'))

        print(getattr(settings, "GEOIP_LICENSE",""))

        if not getattr(settings, "GEOIP_LICENSE",""):
            self.stdout.write(self.style.ERROR('Add a MaxMind GeoIP license key to settings.py: GEOIP_LICENSE'))
            return

        check = requests.head(PERMALINK.format(settings.GEOIP_LICENSE))

        latest_file = check.headers.get("Content-Disposition").split("filename=")[-1]
        print("..latest file available for download is {0}".format(latest_file))

        latest_file_dig = int(latest_file.split(".tar.gz")[0].split("_")[-1])
        
        print(check.headers)

        # Check if file in geolite directory
        dbs = 0
        download = True
        for fname in os.listdir(settings.GEOIP_PATH):
            if fname.endswith(".mmdb"):
                dbs += 1
            elif fname == latest_file:
                self.stdout.write(self.style.SUCCESS('Current GeoIP2 database tar is the latest version available ({0})'.format(fname)))
                download = False
                break

            # elif fname.endswith(".tar.gz"):
            #     fdate = fname.split("_")[-1].split(".tar.gz")[0]
            #     if fdate.isdigit():
            #         if fdate <= latest_file_dig:
            #             download = False
            #             self.stdout.write(self.style.SUCCESS('Current GeoIP2 database tar is the latest version available ({0})'.format(fname)))
            #             break
                    
        if dbs == 0:
            download = True


        if download:

            r = requests.get(PERMALINK.format(settings.GEOIP_LICENSE))
            fpath = settings.GEOIP_PATH + "/{0}".format(latest_file)

            with open(fpath, 'wb') as f:
                f.write(r.content)
                print("..latest file available for download is {0}".format(latest_file))
                self.stdout.write(self.style.SUCCESS('..Successfully downloaded latest GeoIP2 database tar to {0}'.format(settings.GEOIP_PATH + "/{0}".format(latest_file))))


            tar = tarfile.open(fpath)
            tar.extractall(settings.GEOIP_PATH ) # specify which folder to extract to
            tar.close()

        

        # {'Date': 'Thu, 26 Aug 2021 14:16:42 GMT', 'Content-Type': 'application/gzip', 'Content-Length': '3487359', 'Connection': 'keep-alive', 'CF-Ray': '684daded39b59cb1-AMS', 'Accept-Ranges': 'bytes', 'Cache-Control': 'private, max-age=0', 'Content-Disposition': 'attachment; filename=GeoLite2-Country_20210824.tar.gz', 'ETag': '"ecc8e32c1bc7b105fe13a62d4682c733"', 'Expires': 'Thu, 26 Aug 2021 14:16:42 GMT', 'Last-Modified': 'Mon, 23 Aug 2021 18:52:46 GMT', 'CF-Cache-Status': 'DYNAMIC', 'expect-ct': 'max-age=604800, report-uri="https://report-uri.cloudflare.com/cdn-cgi/beacon/expect-ct"', 'X-MaxMind-Worker': 'enabled', 'Vary': 'Accept-Encoding', 'Server': 'cloudflare'}

        # g = GeoIP2()
        # result = g.city('8.8.8.8')
        # pprint(result)
