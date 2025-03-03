from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtCore import Qt

def create_pie_chart(title, data):
    series = QPieSeries()
    for label, value in data.items():
        slice = series.append(label, value)
        slice.setLabelVisible(True)
    
    chart = QChart()
    chart.addSeries(series)
    chart.setTitle(title)
    chart.setAnimationOptions(QChart.SeriesAnimations)
    return QChartView(chart)

def create_bar_chart(title, categories, values, color=QColor('#3498db')):
    series = QBarSeries()
    bar_set = QBarSet('')
    bar_set.setColor(color)
    for val in values:
        bar_set.append(val)
    series.append(bar_set)

    chart = QChart()
    chart.addSeries(series)
    chart.setTitle(title)
    
    axis_x = QBarCategoryAxis()
    axis_x.append(categories)
    chart.addAxis(axis_x, Qt.AlignBottom)
    series.attachAxis(axis_x)
    
    chart.setAnimationOptions(QChart.SeriesAnimations)
    chart.legend().setVisible(False)
    
    chart_view = QChartView(chart)
    chart_view.setRenderHint(QPainter.Antialiasing)
    return chart_view
