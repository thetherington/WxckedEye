import argparse
from ipaddress import IPv4Address
import json

import requests
import urllib3
from dateutil import parser

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()


class WxckedEye:
    def __init__(self, host, port=80, proto="http"):
        self.host = host
        self.proto = proto
        self.port = port
        self.api = "api/wxckedeye/v1/dashboard"
        self.time_sync_api = "api/wxckedeye/v1/prepareTimeSync"

        self.store = {}

    def fetch(self, url=None):
        if not url:
            url = "{proto}://{host}:{port}/{api}".format(
                proto=self.proto, host=self.host, port=self.port, api=self.api
            )

        resp = requests.get(url, verify=False, timeout=10)
        resp.close()

        data = json.loads(resp.text)

        return data

    def collect(self):
        data = self.fetch()

        documents = []

        self.store["sources"] = {}
        self.store["destinations"] = {}
        self.store["slaves"] = {}

        if "xnicTotals" in data.keys():
            doc = self.parseXnic(data["xnicTotals"])
            documents.append(doc)

        if "xnics" in data.keys():
            for agent, value in data["xnics"].items():
                doc = self.parseXnic(value, agent)
                documents.append(doc)

        if "replTotals" in data.keys():
            docs = self.parseReplTotals(data["replTotals"])
            documents.extend(docs)

            if (
                "rxMulticastGroups" in data["replTotals"].keys()
                and len(data["replTotals"]["rxMulticastGroups"]) > 0
            ):
                docs = self.parseRxMulticastGroups(
                    data["replTotals"]["rxMulticastGroups"]
                )
                documents.extend(docs)

        documents.append(self.parseTopLevel(data))
        
        
        url = "{proto}://{host}:{port}/{api}".format(
            proto=self.proto, host=self.host, port=self.port, api=self.time_sync_api
        )
        
        data = self.fetch(url)
        
        if isinstance(data, dict):
            docs = self.parseTimeSyncInfo(data)
            documents.extend(docs)


        return documents

    def parseXnic(self, xnicdef, agent=None):
        fields = {}

        for key in ["PktCounters", "ByteCounters", "Latencies"]:
            for k, v in xnicdef[key].items():
                # parse buckets later
                if k.lower() != "buckets":
                    # prevent anything bigger than a long from being used
                    if v < 9223372036854775807:
                        fields.update(
                            {
                                "l_{metricset}_{metric}".format(
                                    metricset=key.lower(), metric=k.lower()
                                ): v
                            }
                        )

        # treat objects found in TxMulticastGroups as "sources"
        # store the source group into the self.store keyed as the groupIp value
        if xnicdef.get("TxMulticastGroups"):
            for txGroup in xnicdef.get("TxMulticastGroups"):
                if IPv4Address(txGroup.get("groupIp")).is_multicast:
                    txGroup.update({"agent": agent})
                    self.store["sources"].update({txGroup.get("groupIp"): txGroup})

        # treat objects found in RxMulticastGroups as "destinations"
        # store the agent into the self.store keyed as the groupIp value
        if xnicdef.get("RxMulticastGroups"):
            for rxGroup in xnicdef.get("RxMulticastGroups"):
                if IPv4Address(rxGroup.get("groupIp")).is_multicast:
                    if rxGroup.get("groupIp") in self.store["destinations"].keys():
                        self.store["destinations"][rxGroup.get("groupIp")].append(agent)
                    else:
                        self.store["destinations"].update(
                            {rxGroup.get("groupIp"): [agent]}
                        )

        if "NumConnections" in xnicdef.keys():
            fields.update({"l_info_numconnections": xnicdef.get("NumConnections")})

        if "XnicMode" in xnicdef.keys():
            fields.update({"s_info_xnicmode": xnicdef.get("XnicMode")})

        fields.update(
            {
                "l_info_timestamp": xnicdef.get("Timestamp"),
                "s_info_softwareversion": xnicdef.get("SoftwareVersion"),
                "s_info_xnicversion": xnicdef.get("XnicVersion"),
            }
        )

        document = {}

        if agent:
            fields.update({"s_agent": agent})
            document.update({"fields": fields, "host": self.host, "name": "agent"})

        else:
            document.update({"fields": fields, "host": self.host, "name": "totals"})

        return document

    def parseReplTotals(self, replTotalDef):
        documents = []

        fields = {}

        fields.update(
            {
                "l_{}".format(k): replTotalDef.get(k)
                for k in [
                    "sequence",
                    "rxCount",
                    "txCount",
                    "rxBytes",
                    "txBytes",
                    "rxBridgeBytes",
                    "timestamp",
                    "dropsByByteLimit",
                    "dropsByCountLimit",
                    "rxMeshPktCount",
                    "rxMeshBytes",
                    "txMeshPktCount",
                    "txMeshBytes",
                    "rxUnicastPktCount",
                    "rxUnicastBytes",
                    "txUnicastPktCount",
                    "txUnicastBytes",
                ]
            }
        )

        document = {
            "fields": fields,
            "host": self.host,
            "name": "repltotals_info",
        }

        documents.append(document)

        return documents

    def parseTopLevel(self, data):
        fields = {}

        fields.update(
            {
                "s_{}".format(k): data.get(k)
                for k in [
                    "hostName",
                    "subscriptionId",
                    "hostName",
                    "replStatus",
                    "ipAddr",
                    "cloud",
                    "swxtchName",
                    "remfVersion",
                ]
            }
        )

        fields.update(
            {
                "i_numcores": data.get("numCores"),
                "b_authorized": data.get("authorized"),
            }
        )

        document = {
            "fields": fields,
            "host": self.host,
            "name": "top_info",
        }

        return document

    def parseRxMulticastGroups(self, rxMulticastGroups):
        documents = []

        for group in rxMulticastGroups:
            fields = {
                "s_groupip": group.get("groupIp"),
                "l_pktscount": group.get("pktsCount"),
                "l_bytescount": group.get("bytesCount"),
                "s_lastupdate": group.get("lastUpdate"),
                "s_srcip": group.get("srcIp"),
                "i_srcport": group.get("srcPort"),
                "i_protocoltype": group.get("protocolType"),
                "i_numberofdestinations": group.get("numberOfDestinations"),
                "b_multicast": IPv4Address(group.get("groupIp")).is_multicast,
                "i_num_destinations": 0,
            }

            # calculate bitrate if previous data is in self.store
            # otherwise just set the bitrate to be zero
            if group["groupIp"] in self.store.keys():
                group_prev = self.store[group["groupIp"]]

                new_bytes = group["bytesCount"] - group_prev["bytesCount"]
                dt_prev = parser.parse(group_prev["lastUpdate"])
                dt_new = parser.parse(group["lastUpdate"])
                dt_diff = dt_new - dt_prev

                if new_bytes != 0:
                    byte_rate = new_bytes / int(dt_diff.total_seconds())
                    bit_rate = int(byte_rate * 8)
                    fields.update({"l_bitrate": bit_rate})

                else:
                    fields.update({"l_bitrate": 0})

                self.store[group["groupIp"]].update(group)

            else:
                self.store.update({group["groupIp"]: group})
                fields.update({"l_bitrate": 0})

            # Check if the groupIp is multicast.  If it is, then start finding
            # the egress (source) and ingest (destinations[])
            if IPv4Address(group.get("groupIp")).is_multicast:
                if self.store["sources"].get(group.get("groupIp")):
                    fields.update(
                        {
                            "s_source": self.store["sources"][group.get("groupIp")].get(
                                "agent"
                            )
                        }
                    )

                if self.store["destinations"].get(group.get("groupIp")):
                    fields.update(
                        {
                            "as_destinations": self.store["destinations"][
                                group.get("groupIp")
                            ],
                            "i_num_destinations": len(
                                self.store["destinations"][group.get("groupIp")]
                            ),
                        }
                    )

            document = {
                "fields": fields,
                "host": self.host,
                "name": "repltotals_multicastgroups",
            }

            documents.append(document)

        return documents

    def parseTimeSyncInfo(self, timesyncinfo):
        from quantiphy import Quantity
        
        documents = []

        if "master" in timesyncinfo.keys():
            fields = {
                "s_name": timesyncinfo["master"].get("name"),
                "s_displayname": timesyncinfo["master"].get("displayname"),
                "s_type": timesyncinfo["master"].get("type"),
            }

            document = {
                "fields": fields,
                "host": self.host,
                "name": "timesyncmaster",
            }

            documents.append(document)

        if "slaves" in timesyncinfo.keys() and len(timesyncinfo["slaves"]) > 0:
            for slave in timesyncinfo["slaves"]:
                
                try:
                    rootoffset = Quantity(slave.get("rootoffset"), units="s", scale=0.000000001)
                except Exception:
                    rootoffset = Quantity(0, units="s", scale=0.000000001)
                
                try:
                    localoffset = Quantity(slave.get("localoffset"), units="s", scale=0.000000001)
                except Exception:
                    localoffset = Quantity(0, units="s", scale=0.000000001)
                
                fields = {
                    "s_name": slave.get("name"),
                    "b_xnicpresent": slave.get("xnicPresent"),
                    "b_timebeatpresent": slave.get("timebeatPresent") if slave.get("timebeatPresent") else False,
                    "d_localoffset_ms": round(slave.get("localoffset") / 1000000, 5) if slave.get("localoffset") else None,
                    "d_rootoffset_ms": round(slave.get("rootoffset") / 1000000, 5) if slave.get("rootoffset") else None,
                    "d_localoffset_us": round(slave.get("localoffset") / 1000, 3) if slave.get("localoffset") else None,
                    "d_rootoffset_us": round(slave.get("rootoffset") / 1000, 3) if slave.get("rootoffset") else None,
                    "s_rootoffset": rootoffset.render(),
                    "s_localoffset": localoffset.render()
                }

                self.store["slaves"].update({slave.get("name"): fields})

                document = {
                    "fields": fields,
                    "host": self.host,
                    "name": "timesyncslave",
                }

                documents.append(document)

        return documents


def main():
    args_parser = argparse.ArgumentParser(description="wXcked Eye API Poller Program")

    args_parser.add_argument(
        "-host",
        "--swxtch-host",
        required=False,
        type=str,
        metavar="<ip>",
        default="localhost",
        help="Swxtch IP Address (default localhost)",
    )

    args_parser.add_argument(
        "-port",
        "--swxtch-port",
        required=False,
        type=int,
        metavar="<port>",
        default=3000,
        help="Swxtch Port (default 3000)",
    )

    args_parser.add_argument(
        "-proto",
        "--swxtch-protocol",
        required=False,
        type=str,
        metavar="<http or https>",
        default="http",
        help="Swxtch Protocol (default http)",
    )

    args_parser.add_argument(
        "-d",
        "--dump",
        required=False,
        default=False,
        action="store_true",
        help="Dump the response payload to a file",
    )

    args_parser.add_argument(
        "-w",
        "--watch",
        required=False,
        default=False,
        action="store_true",
        help="Re-run the collection",
    )

    args = args_parser.parse_args()

    collector = WxckedEye(
        host=args.swxtch_host, port=args.swxtch_port, proto=args.swxtch_protocol
    )

    if args.dump:
        resp = collector.fetch()

        with open("data.json", "w", encoding="UTF-8") as f:
            json.dump(resp, f, indent=4)

    elif args.watch:
        input_quit = False

        while input_quit != "q":
            docs = collector.collect()

            print(json.dumps(docs, indent=1))

            input_quit = input("\nType q to quit or just hit enter: ")

    else:
        docs = collector.collect()

        print(json.dumps(docs, indent=1))


if __name__ == "__main__":
    main()
