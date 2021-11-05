import pandas as pd
import numpy as np

from pyecharts import options as opts
from pyecharts.charts import Line, Grid,Tab

from pyecharts.charts import Line

def generateChart(list_of_columns, df):
    print("in generateChart: list_of_columns = ", list_of_columns)
    # minimum 25 on my laptop
    legend_height = 25
    # 50 looks well on my laptop, better to be >30
    y_height_per_measurement = 300

    column_list_in_df = lambda a_list, a_df: [col for col in a_list if col in a_df.columns]
    column_in_df = lambda a_column, a_df: [a_column] if a_column in a_df.columns else None

    chart_list = []
    cur_pos = 0
    for idx in range(len(list_of_columns)):
        columns = list_of_columns[idx]
        print("configured columns = ", columns)

        columns = column_list_in_df(columns, df) if type(columns) is list else column_in_df(columns, df)
        print("columns exists in df = ", columns)

        pos_top_legend = cur_pos
        pos_top_chart = cur_pos + legend_height

        chart_height = None


        line_x = Line()

        perf_time_uniq = df['PERF_time'].unique()
        perf_time_uniq = perf_time_uniq[~pd.isnull(perf_time_uniq)]

        # check if the time stamp added by the parser
        if (perf_time_uniq.size == 1) and (perf_time_uniq[0]=='01-01 00:00:00.000'):
            # added by parser, x-axis use index instead
            line_x.add_xaxis(xaxis_data=df['index'])
        else:
            line_x.add_xaxis(xaxis_data=list(df['PERF_time']))
        if columns:
            for col in columns:
                print("col = ", col)
                # print("df[col] = ", df[col])
                if 'kbps' in col:
                    line_x.add_yaxis(
                        series_name=col,
                        y_axis=df[col],
                        is_smooth=False,
                        is_hover_animation=False,
                        linestyle_opts=opts.LineStyleOpts(width=3, opacity=1),
                        label_opts=opts.LabelOpts(is_show=False),
                        symbol='none',
                        areastyle_opts=opts.AreaStyleOpts(opacity=0.3)
                    )
                # elif 'PCI_global_index' in col:
                elif col.startswith("PCI="):
                    chart_height = 30
                    line_x.add_yaxis(
                        series_name=col,
                        y_axis=df[col],
                        is_smooth=False,
                        is_hover_animation=False,
                        linestyle_opts=opts.LineStyleOpts(width=0, opacity=1),
                        label_opts=opts.LabelOpts(is_show=False),
                        symbol='none',
                        is_step = True,
                        areastyle_opts=opts.AreaStyleOpts(opacity=1),
                    )
                elif 'FRAME_status' in col or 'Line_no_in_logfile' in col:
                    line_x.add_yaxis(
                        series_name=col,
                        y_axis=df[col],
                        is_smooth=False,
                        is_hover_animation=False,
                        linestyle_opts=opts.LineStyleOpts(width=3, opacity=1),
                        label_opts=opts.LabelOpts(is_show=False),
                        symbol='none',
                        is_step = True,
                        areastyle_opts=opts.AreaStyleOpts(opacity=1),
                    )
                else:
                    line_x.add_yaxis(
                        series_name=col,
                        y_axis=df[col],
                        is_smooth=False,
                        is_hover_animation=False,
                        linestyle_opts=opts.LineStyleOpts(width=1, opacity=1),
                        label_opts=opts.LabelOpts(is_show=False),
                        symbol='none',
                    )
        # all plots to configure except for the last one
        if idx != len(list_of_columns) - 1:
            line_x.set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(is_show=False),
                ),
            )
        else:
            line_x.set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(is_show=True,rotate=-20),
                ),
            )
        # the sequence of configuration matters...be caution when move the code around
        line_x.set_global_opts(
            legend_opts=opts.LegendOpts(
                is_show=True, pos_top=pos_top_legend, pos_left="center"
                # is_show=True,pos_left="center"
            ),
            yaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitarea_opts=opts.SplitAreaOpts(
                    is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                ),
            ),
        )

        if idx == 0:
            line_x.set_global_opts(
                datazoom_opts=[
                    # opts.DataZoomOpts(
                    #     is_show=False,
                    #     type_="inside",
                    #     xaxis_index=list(range(len(list_of_columns))),
                    #     range_start=0,
                    #     range_end=100,
                    # ),
                    opts.DataZoomOpts(
                        is_show=True,
                        xaxis_index=list(range(len(list_of_columns))),
                        type_="slider",
                        # pos_top=str(component_height * len(list_of_columns) + 50),
                        pos_bottom='0',
                        range_start=0,
                        range_end=100,
                    ),
                ],
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="cross",
                    background_color="rgba(245, 245, 245, 0.0)",
                    border_width=1,
                    border_color="#ccc",
                    textstyle_opts=opts.TextStyleOpts(color="#000", font_size=10),
                ),
                axispointer_opts=opts.AxisPointerOpts(
                    is_show=True,
                    link=[{"xAxisIndex": "all"}],
                    # label=opts.LabelOpts(background_color="#777"),
                    label=opts.LabelOpts(background_color="#f5f5f5", color="#000"),

                ),
            )

        if not chart_height:
            chart_height = y_height_per_measurement * len(columns)
        component_height = legend_height + chart_height
        cur_pos += component_height

        chart_list.append((line_x, pos_top_chart, chart_height))

    total_height = str(cur_pos + 70) + 'px'
    grid_chart = Grid(
        init_opts=opts.InitOpts(
            width="1400px",
            # height="2000px",
            height=total_height,
            animation_opts=opts.AnimationOpts(animation=False),
        )
    )

    for tup in chart_list:
        grid_chart.add(
            tup[0],
            grid_opts=opts.GridOpts(pos_left="4%", pos_right="3%",
                                    pos_top=str(tup[1]), height=tup[2])
        )

    # grid_chart.render(plot_file_name)
    return grid_chart




df = pd.read_csv("/Users/ezhou/Documents/smawave/tech_support/cases/011_APMT_longbeach/RTT/ping_172.17.18.6.csv")
df['PERF_time'] = df[df.columns[0]].apply(lambda x:x[6:])+ "_" + df[df.columns[1]].apply(lambda x:x[:-1])

y_list = ['RTT']

grid_chart = generateChart(y_list,df)
grid_chart.render('ping_rtt.html')

