import json

from WxckedEye import WxckedEye
from insite_plugin import InsitePlugin


class Plugin(InsitePlugin):
    def can_group(self):
        return False

    def fetch(self, hosts):
        time_sync_enable = False
        
        try:
            self.collector

        except Exception:
            self.collector = WxckedEye(host=hosts[-1], port=3000, proto="http", timing_api=time_sync_enable)

        return json.dumps(self.collector.collect())
