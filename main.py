import pandas as pd
import numpy as np
import xlwings as xw
from util import print_progress
from collections import defaultdict

import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import patches as patches


class PynamicBottleneck(object):
    def __init__(self, case_lv, case_col_name, activity_col_name, timestamp_col_name):
        self.case_lv = case_lv
        self.seg_lv = None
        self.sys_lv = None

    def transform(self, time_origin=None, bin_length=None):
        seg_lv = pd.DataFrame(
            columns=['Case', 'Source', 'Target', 'Start Timestamp', 'End Timestamp', 'Timedelta', 'Worktime',
                     'Segment Path', 'MZ Score'])
        sub_row = pd.Series(dtype=object, index=seg_lv.columns)
        for case in self.case_lv['Case'].unique():
            trace = self.case_lv[self.case_lv['Case'] == case]

            segments = [trace[i:i + 2] for i in range(0, len(trace) - 1)]
            for segment in segments:
                sub_row['Case'] = case
                sub_row['Source'] = segment.iloc[0]['Activity']
                sub_row['Target'] = segment.iloc[1]['Activity']
                sub_row['Start Timestamp'] = segment.iloc[0]['Timestamp']
                sub_row['End Timestamp'] = segment.iloc[1]['Timestamp']
                sub_row['Timedelta'] = (segment.iloc[1]['Timestamp'] - segment.iloc[0]['Timestamp']) / np.timedelta64(1, 'm')
                sub_row['Worktime'] = get_worktime(segment.iloc[0]['Timestamp'], segment.iloc[1]['Timestamp'])
                sub_row['Segment Path'] = segment.iloc[0]['Activity'] + ' - ' + segment.iloc[1]['Activity']

                seg_lv = seg_lv.append(sub_row, ignore_index=True)

        # get segment paths
        segment_paths = list(seg_lv.groupby(['Source', 'Target']).groups.keys())

        # get modified z-score
        for sp in segment_paths:
            sp_idx = (seg_lv['Source'] == sp[0]) & (seg_lv['Target'] == sp[1])
            seg_lv.at[sp_idx, 'MZ Score'] = get_modified_z_score(seg_lv.loc[sp_idx]['Worktime'])

        # bin segments
        if time_origin is None:
            time_origin = min(seg_lv['Start Timestamp'])
        else:
            time_origin = pd.Timestamp(time_origin)

        for i, row in seg_lv.iterrows():
            time_diff = (row['Start Timestamp'] - time_origin).total_seconds()
            seg_lv.at[i, 'Bin'] = time_diff // bin_length

        self.seg_lv = seg_lv
        return seg_lv

    def detect_blockage(self, threshold):
        segment_paths = list(self.seg_lv.groupby(['Source', 'Target']).groups.keys())
        blockage_groups = defaultdict(list)

        for sp in segment_paths:
            segments = self.seg_lv[(self.seg_lv['Source']==sp[0])&(self.seg_lv['Target']==sp[1])].sort_values(by='Start Timestamp')
            blockage_group = []
            for s_i, segment in segments.iterrows():
                if segment['MZ Score'] > threshold:
                    blockage_group.append(s_i)
                else:
                    if len(blockage_group) <= 1:
                        pass
                    else:
                        blockage_groups[sp].append(blockage_group)
                    blockage_group = []
        return dict(blockage_groups)

    def detect_highload(self, threshold=75):
        segment_paths = list(self.seg_lv.groupby(['Source', 'Target']).groups.keys())
        highload_groups = defaultdict(list)

        for sp in segment_paths:
            segments = self.seg_lv[(self.seg_lv['Source']==sp[0])&(self.seg_lv['Target']==sp[1])].sort_values(by='Start Timestamp')
            bins = segments.groupby('Bin').size()
            bin_size_threshold = np.percentile(bins, threshold)
            for b in bins.index[bins > bin_size_threshold]:
                highload_groups[sp].append(segments.index[segments['Bin']==b])
        return dict(highload_groups)

    def viz(
            self,
            act_order, blockage=None, highload=None,
            line_color='lightsteelblue',
            line_weight=1,
            blockage_facecolor='r',
            highload_facecolor='b',
            blockage_alpha=0.2,
            highload_alpha=0.2,
            dpi=100,
            figsize=(16, 9),
            title='Dynamic Bottlenecks : Blockage & High Load'
        ):
        fig, ax = plt.subplots(dpi=dpi, figsize=figsize)
        ax.spines['right'].set_color('none')
        ax.spines['top'].set_color('none')
        ax.spines['bottom'].set_color('none')
        ax.set_title(title)

        for act in act_order:
            time_min = min(self.seg_lv['Start Timestamp'])
            time_max = max(self.seg_lv['End Timestamp'])
            time_diff = time_max - time_min
            ax.arrow(
                time_min, act_order.index(act),
                pd.to_datetime(0) + time_diff * 1.05, 0,
                color='lightgrey', ls=':', head_width=0.25, width=0.01, head_length=0.5
            )

        # draw blockage group and process flow
        segment_paths = list(self.seg_lv.groupby(['Source', 'Target']).groups.keys())
        for s_i, sp in enumerate(segment_paths):
            segments = self.seg_lv[(self.seg_lv['Source']==sp[0])&(self.seg_lv['Target']==sp[1])].sort_values(by='Start Timestamp')

            # draw process flow
            for i, segment in segments.iterrows():
                ax.plot(
                    [segment['Start Timestamp'], segment['End Timestamp']],
                    [act_order.index(segment['Source']), act_order.index(segment['Target'])],
                    c=line_color,
                    lw=line_weight
                )

            # draw blockage group
            if blockage is not None and sp in blockage:
                for b_i, bl in enumerate(blockage[sp]):
                    time_max = max(segments.loc[bl]['End Timestamp'])
                    time_min = min(segments.loc[bl]['Start Timestamp'])
                    time_diff = time_max - time_min
                    ax.add_patch(
                        patches.Rectangle(
                            (time_min, act_order.index(segment['Target'])),
                            time_diff,
                            1,
                            color=blockage_facecolor,
                            alpha=blockage_alpha,
                            label='Blockage' if b_i == 0 and s_i == 0 else None
                        )
                    )
            else:
                pass

            # draw high load group
            if highload is not None and sp in highload:
                for h_i, hl in enumerate(highload[sp]):
                    time_max = max(segments.loc[hl]['End Timestamp'])
                    time_min = min(segments.loc[hl]['Start Timestamp'])
                    time_diff = time_max - time_min
                    ax.add_patch(
                        patches.Rectangle(
                            (time_min, act_order.index(segment['Target'])),
                            time_diff,
                            1,
                            color=highload_facecolor,
                            alpha=highload_alpha,
                            label='High Load' if h_i == 0 and s_i == 0 else None
                        )
                    )
            else:
                pass

        ax.xaxis.set_major_formatter(
            lambda x, pos: (pd.Timestamp(0) + pd.Timedelta(x, unit='day')).strftime('%m/%d')
        )

        ax.set_yticks(range(0, len(act_order)), labels=act_order, )
        ax.tick_params(axis='y', which='major', labelsize=20)

        ax.legend(loc='lower center', ncol=2, bbox_to_anchor=(0.5, -0.075))

        fig.tight_layout()
        fig.show()


def xl_to_df(file_path):
    book = xw.Book(file_path)
    df = book.sheets(1).used_range.options(pd.DataFrame).value
    df = df.reset_index()
    return df


def get_worktime(from_datetime, to_datetime):
    from_datetime = pd.to_datetime(from_datetime)
    to_datetime = pd.to_datetime(to_datetime)
    worktime = 0

    # 인사정보 업무일 기준 휴일(Sep 2021 ~ Oct 2021)
    holidays = [
        '2021-09-20', '2021-09-21', '2021-09-22', '2021-09-23', '2021-09-24',
        '2021-10-04', '2021-10-11', '2021-10-27'
    ]
    holidays = list(map(pd.to_datetime, holidays))

    # 주말 및 공휴일 제외
    bdr = pd.bdate_range(from_datetime, to_datetime, freq='C', holidays=holidays, normalize=True)
    bdr_exclude = bdr.copy()
    if len(bdr_exclude) >= 1 and from_datetime.date() == bdr_exclude[0].date():
        bdr_exclude = bdr_exclude[1:]
    if len(bdr_exclude) >= 1 and to_datetime.date() == bdr_exclude[-1].date():
        bdr_exclude = bdr_exclude[:-1]

    # 하루 8시간 근무
    worktime += len(bdr_exclude) * 8 * 60
    # 월요일(팀생산회의) 30분 감산
    worktime -= list(map(pd.Timestamp.weekday, bdr_exclude)).count(0) * 30

    from_time = from_datetime.time()
    to_time = to_datetime.time()

    if from_datetime.date() == to_datetime.date():
        worktime_adjustment = (to_datetime - from_datetime).total_seconds() / 60
        if from_time.hour < 12 and 12 < to_time.hour:
            worktime_adjustment -= 60
            if from_datetime.weekday == 0 and to_time.hour * 60 + to_time.minute >= 810:
                worktime_adjustment -= 30
    else:
        ### 시작일의 근무시간
        if from_time.hour < 8:
            # 8시 전이면 그날 8시간 근무
            fromdate_worktime = 8 * 60
        elif from_time.hour < 12:
            # 8시~12시 전이면 시작시간부터 5시까지 근무, 점심시간 제외
            fromdate_worktime = (17 - from_time.hour) * 60 - from_time.minute
        elif from_time.hour == 12:
            # 12시(점심시간) 이면 오후 4시간 근무
            fromdate_worktime = 4 * 60
        elif from_time.hour < 17:
            # 12시~17시 전이면 시작시간부터 5시까지 근무
            fromdate_worktime = (17 - from_time.hour) * 60 - from_time.minute
        elif from_time.hour >= 17:
            # 17시 이후면 0시간 근무
            fromdate_worktime = 0

        # 월요일이면 팀생산회의 시간 제외
        if from_datetime.weekday() == 0 and from_time.hour <= 12:
            fromdate_worktime -= 30

        ### 종료일의 근무시간
        if to_time.hour < 8:
            # 8시 전이면 0시간 근무
            todate_worktime = 0
        elif to_time.hour < 12:
            # 8시~12시 전이면 8시부터 완료시간까지 근무
            todate_worktime = (to_time.hour - 8) * 60 + to_time.minute
        elif to_time.hour == 12:
            # 12시(점심시간) 이면 오전 4시간 근무
            todate_worktime = 4 * 60
        else:
            # 12시 이후면 8시부터 완료시간까지 근무, 점심시간 제외
            todate_worktime = (to_time.hour - 9) * 60 + to_time.minute

        # 월요일이면 팀생산회의 시간 제외
        if from_datetime.weekday() == 0 and (to_time.hour * 60 + to_time.minute) >= 810:
            todate_worktime -= 30
        worktime_adjustment = min(fromdate_worktime + todate_worktime, (to_datetime - from_datetime).total_seconds() / 60)

    worktime += worktime_adjustment
    return worktime

def get_modified_z_score(series):
    series = np.array(series)
    m = np.median(series)
    diff_m = np.median(np.abs(series - m))
    return 0.6745 * (series - m) / diff_m


data = xl_to_df('data/tact.xlsx')
act_names = ['FU', 'SW', 'LF', 'LW', 'RP']

# case level events
new_data = pd.DataFrame()

total = len(data)
for d_i, d in data.iterrows():
    if isinstance(d['Ship'], float):
        data.at[d_i, 'Ship'] = str(int(d['Ship']))
    for act in act_names:
        if d[act + ' Start'] is not pd.NaT and d[act + ' Complete'] is not pd.NaT:
            sub_row = pd.Series(dtype=object)
            sub_row['Case'] = int(d_i)
            sub_row['Activity'] = act
            sub_row['Start Timestamp'] = d[act + ' Start']
            sub_row['End Timestamp'] = d[act + ' Complete']
            sub_row['Time Elapsed'] = (d[act + ' Complete'] - d[act + ' Start']) / np.timedelta64(1, 'm')
            new_data = new_data.append(sub_row, ignore_index=True)
    print_progress(d_i + 1, total)

new_data['Case'] = new_data['Case'].astype(int)
new_data['Time Elapsed'] = list(map(get_worktime, new_data['Start Timestamp'], new_data['End Timestamp']))
new_data.to_csv('data/event_log.csv', encoding='utf-8-sig', index=None)

# frag
event_log = pd.read_csv('data/event_log.csv', encoding='utf-8-sig')

case_lv = pd.DataFrame()
sub_row = pd.Series(dtype=object, index=['Case', 'Activity', 'Timestamp'])
for case in event_log['Case'].unique():
    trace = event_log[event_log['Case'] == case]
    for e_i, event in trace.iterrows():
        sub_row_1 = sub_row.copy()
        sub_row_1['Case'] = event['Case']
        sub_row_1['Activity'] = event['Activity'] + ' Start'
        sub_row_1['Timestamp'] = event['Start Timestamp']

        sub_row_2 = sub_row_1.copy()
        sub_row_2['Activity'] = event['Activity'] + ' End'
        sub_row_2['Timestamp'] = event['End Timestamp']

        case_lv = case_lv.append([sub_row_1, sub_row_2])

case_lv = case_lv.reset_index(drop=True)
case_lv.to_csv('data/case_level_event_log.csv', encoding='utf-8-sig', index=None)


# segment level events
case_lv = pd.read_csv(
    'data/case_level_event_log.csv',
    encoding='utf-8-sig',
    converters={
        'Timestamp': pd.Timestamp
    },
)

pbn = PynamicBottleneck(case_lv, 'Case', 'Activity', 'Timestamp')

pbn.transform(bin_length=86400)

bl = pbn.detect_blockage(2)
hl = pbn.detect_highload(75)

acts = [
    'RP End', 'RP Start', 'LW End', 'LW Start',
    'LF End', 'LF Start', 'SW End', 'SW Start',
    'FU End', 'FU Start'
]

pbn.viz(acts, highload=hl, blockage=bl)

('SW End', 'LW Start') in bl
