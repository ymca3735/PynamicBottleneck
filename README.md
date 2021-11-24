# PynamicBottleneck
Dynamic bottleneck detector for Python.

Before you get started. you should read the paper below. This code is based on :
> Toosinezhad, Zahra, et al. "Detecting System-Level Behavior Leading To Dynamic Bottlenecks." 2020 2nd International Conference on Process Mining (ICPM). IEEE, 2020.   
> https://ieeexplore.ieee.org/abstract/document/9230102

## Dependency
* pandas
* numpy
* matplotlib

## Installation
**Q.** _How do I install this?_   
**A.** _Yes._   

## Usage
The package includes one class **PynamicBottleneck** and several methods.
Actually, there is 1 method. More methods coming in soon.

### class PynamicBottleneck Structure:
**PynamicBottleneck.__init__(_self, case_lv_)**   
>  Initialize PydynamicBottleneck object. It takes 1 parameter.   
>    
>**Parameter : case_lv : pandas.DataFrame**   
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
>Case-level event log. The log **must** contain following 3 columns: case id, activity id, timestamp.
>
>The case-level event log should be like
>|Case ID|Activity ID|Timestamp|
>|---|---|---|
>|0|Eat bacon|2021-11-24 07:24|
>|0|Go to work|2021-11-24 08:30|
>|0|Come back home|2021-11-24 18:13|
>|1|Eat concrete powder|2021-11-25 07:20|
>|1|Goodbye, world!|2021-11-25 08:01|
>|...|...|...|   
>
　   
**PynamicBottleneck.transform(_self, time_origin=None, bin_length=None_)**
>Transform case-level event log and returns segment-level event log.   
>
>**Parameter : time_origin : _datetime-like, str, int, float_**   
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
>Start timestamp of the first bin. If _**None**_, it is set to the earliest start timestamp   
>
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
>**bin_length : _scalar_**   
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
>Length to bin segment-level events. Unit is second.   
>
> Returned segment-level event log will be like
>|Case ID|Souce|Target|Start Timestamp|End Timestamp|Worktime|Modified z-Score|Bin|
>|---|---|---|---|---|---|---|---|
>|0|Eat bacon|Go to work|2021-11-24 07:24|2021-11-24 08:30|3960|1.54|0|
>|0|Go to work|Come back home|2021-11-24 08:30|2021-11-24 18:13|34980|1.05|0|
>|1|Eat concrete powder|Goodbye, world!|2021-11-25 07:20|2021-11-25 08:01|2460|2.04|4|
>|...|...|...|...|...|...|...|...|   
>
> where 'Worktime' is timedelta between 'Start Timestamp' and 'End Timestamp'.   
> 
　   
**PynamicBottleneck.detect_blockage(_self, threshold=2_)**   
> Detect blockage event over each segment level. Every event that exceeds **_threshold_** is a delay, and more than 2 consecutive delays is a blockage. Returns dictionary with (**_Source_**, **_Target_**) as key and blockage lists, containing indices as value.   
>
> **Parameter : threshold : _scalar_**   
> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
> Event is determined as delay if its modified z-score exceeds this value. Default is 2.   
> 
　   
**PynamicBottleneck.detect_highload(_self, threshold=75_)**   
> Detect high load event over each segment level. A bin is determined as high load bin if the size of it exceeds **_threshold_** th percentile of bin sizes in the segment level. Returns dictionary with (**_Source_**, **_Target_**) as key and blockage lists containing indices as value.   
>   
> **Parameter : threshold : _scalar_**   
> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
> Percentile to determine high-load event. It must be between 0 and 100. Default is 75.   
>   
　   
**PynamicBottleneck.viz(_self, act_order, blockage=None, highload=None, line_color='lightsteelblue', line_weight=1, blockage_facecolor='r', highload_facecolor='b', blockage_alpha=0.2, highload_alpha=0.2, dpi=100, figsize=(16, 9), title='Dynamic Bottlenecks : Blockage & High Load'_)**   
> Detect high load event over each segment level. A bin is determined as high load bin if the size of it exceeds **_threshold_** th percentile of bin sizes in the segment level. Returns dictionary with (**_Source_**, **_Target_**) as key and blockage lists containing indices as value.   
>
> **Parameter : act_order : _1d array-like_**   
> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
> 


## Example
```python
from PynamicBottleneck import *


case_lv = pd.read_csv(
    'data/case_level_event_log.csv',
    encoding='utf-8-sig',
    converters={
        'Timestamp': pd.Timestamp
    },
)

pbn = PynamicBottleneck(case_lv, 'Case', 'Activity', 'Timestamp')

# transform case level log to segment level log
pbn.transform(bin_length=86400)

# get blockage events
bl = pbn.detect_blockage(2)

# get high load events
hl = pbn.detect_highload(75)

# visualize
pbn.viz(acts, highload=hl, blockage=bl)
```
