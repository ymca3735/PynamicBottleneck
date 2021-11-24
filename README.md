# PynamicBottleneck
Dynamic bottleneck detector for Python.

Before you get started. you should read the paper below.
> Toosinezhad, Zahra, et al. "Detecting System-Level Behavior Leading To Dynamic Bottlenecks." 2020 2nd International Conference on Process Mining (ICPM). IEEE, 2020.
>
> https://ieeexplore.ieee.org/abstract/document/9230102

## Dependency
* pandas
* numpy
* matplotlib

## Installation

## Usage
The package includes one class **PynamicBottleneck** and several methods.

### class PynamicBottleneck Structure:
**PynamicBottleneck.__init__(_self, case_lv_)**   
>  Initialize PydynamicBottleneck object. It takes 1 parameter.   
>    
>**Parameter : case_lv : pandas.DataFrame**   
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
>Case-level event log. The log **must** contain following 3 columns: case id, activity id, timestamp.
>
>So, the case-level event log should be like
>|Case ID|Activity ID|Timestamp|
>|------|---|---|
>|0|Eat bacon|2021-11-24 07:24|
>|0|Go to work|2021-11-24 08:30|
>|0|Come back home|2021-11-24 18:13|
>|1|Eat concrete powder|2021-11-25 07:20|
>|1|Goodbye, world!|2021-11-25 08:01|
>|...|...|...|

**PynamicBottleneck.transform(_self, blockage_threshold=2, highload_threshold=75, time_origin=None_)**
>Transform case-level event log and returns segment-level event log.   
>
>**Parameter : blockage_threshold : _scalar_**   
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
> Event is determined as delay if its modified z-score exceeds this value. Default is 2.   
> 
>**highload_threshold : _scalar_**   
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
> Percentile to determine high-load event. It must be between 0 and 100. Default is 75.   
> 
>**time_origin : _datetime-like, str, int, float_**   
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
>Start timestamp of the first bin.   
>
>**bin_length : _datetime-like, str, int, float_**   
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
>Length to bin segment-level events.   
>
