import argparse
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

        self.store = {}

    def fetch(self):
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

        return documents

    def parseXnic(self, xnicdef, agent=None):
        fields = {}

        for key in ["PktCounters", "ByteCounters", "Latencies"]:
            for k, v in xnicdef[key].items():
                # parse buckets later
                if k.lower() != "buckets":
                    fields.update(
                        {
                            "l_{metricset}_{metric}".format(
                                metricset=key.lower(), metric=k.lower()
                            ): v
                        }
                    )

        if "NumConnections" in xnicdef.keys():
            fields.update({"l_info_numconnections": xnicdef["NumConnections"]})

        if "XnicMode" in xnicdef.keys():
            fields.update({"s_info_xnicmode": xnicdef["XnicMode"]})

        fields.update(
            {
                "l_info_timestamp": xnicdef["Timestamp"],
                "s_info_softwareversion": xnicdef["SoftwareVersion"],
                "s_info_xnicversion": xnicdef["XnicVersion"],
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
                "l_{}".format(k): replTotalDef[k]
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

        fields.update(
            {
                "s_{}".format(k): replTotalDef[k]
                for k in ["host", "subscriptionId", "hostName", "replStatus"]
            }
        )

        fields.update(
            {
                "i_numcores": replTotalDef["numCores"],
                "b_authorized": replTotalDef["authorized"],
            }
        )

        document = {
            "fields": fields,
            "host": self.host,
            "name": "repltotals_info",
        }

        documents.append(document)

        return documents

    def parseRxMulticastGroups(self, rxMulticastGroups):
        documents = []

        for group in rxMulticastGroups:
            fields = {
                "s_groupip": group["groupIp"],
                "l_pktscount": group["pktsCount"],
                "l_bytescount": group["bytesCount"],
                "s_lastupdate": group["lastUpdate"],
                "s_srcip": group["srcIp"],
                "i_srcport": group["srcPort"],
                "i_protocoltype": group["protocolType"],
                "i_numberofdestinations": group["numberOfDestinations"],
            }

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

            document = {
                "fields": fields,
                "host": self.host,
                "name": "repltotals_multicastgroups",
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
