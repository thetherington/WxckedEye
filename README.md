## WxckedEye

# SwXtch WxckedEye Dashboard Metrics Collector

The purpose of this script module is to collect the WxckedEye dashboard api metrics from the SwXtch cloud transport system.

The data collection module has the below distinct abilities and features:

1. Collects total metric counters
2. Collects agent metric counters
3. Collects replicator metric counters

## Minimum Requirements:

-   inSITE Version 11 and service pack 2
-   Python3 (_already installed on inSITE machine_)
-   Python3 Requests library (_already installed on inSITE machine_)
-   python3-dateutil (sudo apt-get install python3-dateutil)
-   Quantiphy Python Package (If using the PTP Timing Metrics from WxckedEye)
    -   pip install quantiphy
    -   pip install quanitiphy==2.10 (For inSITE Servers on Ubuntu 16)

## Installation:

Installation of the API collection module requires copying the below script into the poller modules folder:

1. Copy **WxckedEye.py** script to the poller python modules folder:

    ```
     cp scripts/WxckedEye.py /opt/evertz/insite/parasite/applications/pll-1/data/python/modules
    ```

2. Restart the poller application

## Configuration:

To configure a poller to use the module start a new python poller configuration outlined below

1. Click the create a custom poller from the poller application settings page
2. Enter a Name, Summary and Description information
3. Enter the host value in the _Hosts_ tab
4. From the _Input_ tab change the _Type_ to **Python**
5. From the _Input_ tab change the _Metric Set Name_ field to **swxtch**
6. Select the _Script_ tab, then paste the contents of **scripts/poller_config.py** into the script panel.
7. Save changes, then restart the poller program.

## Sample Output

```
{
   "l_pktcounters_nic2mcatotal": 313922,
   "l_pktcounters_nic2mcamc": 336743,
   "l_pktcounters_mca2nictotal": 329269,
   "l_pktcounters_mca2nicmc": 337535,
   "l_pktcounters_mca2nicigmp": 450849,
   "l_pktcounters_mca2nicdrops": 395667,
   "l_pktcounters_nic2mcadrops": 426963,
   "l_pktcounters_mca2knidrops": 350917,
   "l_pktcounters_kni2mcadrops": 360818,
   "l_pktcounters_mcapktdrops": 344067,
   "l_pktcounters_mcabigpktdrops": 349137,
   "l_bytecounters_nic2mcatotal": 409877,
   "l_bytecounters_nic2mcamc": 381385,
   "l_bytecounters_mca2nictotal": 458335,
   "l_bytecounters_mca2nicmc": 324917,
   "l_latencies_count": 0,
   "l_latencies_sum": 0,
   "l_info_timestamp": 1657216501229158000,
   "s_info_softwareversion": "v1.7.4.draft",
   "s_info_xnicversion": 2,
   "s_agent": "Agent-1"
}

{
   "s_groupip": "239.0.0.251",
   "l_bytescount": 360766,
   "s_lastupdate": "2023-04-05T18:53:51.884Z",
   "s_srcip": "2.2.2.2",
   "i_srcport": 0,
   "i_protocoltype": 0,
   "i_numberofdestinations": 0,
   "l_bitrate": 42597
}
```
