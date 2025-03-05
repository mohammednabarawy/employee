#!/usr/bin/env python
"""
Performance Monitor for Employee Management System
This script monitors system performance during stress testing.
"""

import os
import sys
import time
import psutil
import threading
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QLabel, QHBoxLayout, QTabWidget, 
                            QMessageBox, QGridLayout)
from PyQt5.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class PerformanceMonitor:
    """Monitor system and application performance"""
    
    def __init__(self, db_file="employee.db"):
        self.db_file = db_file
        self.monitoring = False
        self.start_time = None
        self.cpu_usage = []
        self.memory_usage = []
        self.disk_io = []
        self.db_queries = []
        self.timestamps = []
        
        # Create log file
        self.log_file = "performance_log.txt"
        with open(self.log_file, 'w') as f:
            f.write(f"Performance Monitoring Started at {datetime.now()}\n")
            f.write("="*80 + "\n\n")
            f.write("Timestamp,CPU Usage (%),Memory Usage (MB),Disk Read (MB/s),Disk Write (MB/s),DB Queries/s\n")
    
    def start_monitoring(self):
        """Start monitoring performance"""
        if not self.monitoring:
            self.monitoring = True
            self.start_time = time.time()
            self.cpu_usage = []
            self.memory_usage = []
            self.disk_io = []
            self.db_queries = []
            self.timestamps = []
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring performance"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        prev_disk_io = psutil.disk_io_counters()
        prev_time = time.time()
        prev_queries = self._get_db_query_count()
        
        while self.monitoring:
            # Get current time
            current_time = time.time()
            elapsed = current_time - self.start_time
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent()
            
            # Get memory usage
            memory_info = psutil.Process(os.getpid()).memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # Get disk I/O
            disk_io_current = psutil.disk_io_counters()
            io_time_diff = current_time - prev_time
            
            read_mb_s = (disk_io_current.read_bytes - prev_disk_io.read_bytes) / io_time_diff / (1024 * 1024)
            write_mb_s = (disk_io_current.write_bytes - prev_disk_io.write_bytes) / io_time_diff / (1024 * 1024)
            
            # Get database query count
            current_queries = self._get_db_query_count()
            queries_per_second = (current_queries - prev_queries) / io_time_diff
            
            # Update previous values
            prev_disk_io = disk_io_current
            prev_time = current_time
            prev_queries = current_queries
            
            # Store data
            self.timestamps.append(elapsed)
            self.cpu_usage.append(cpu_percent)
            self.memory_usage.append(memory_mb)
            self.disk_io.append((read_mb_s, write_mb_s))
            self.db_queries.append(queries_per_second)
            
            # Log data
            with open(self.log_file, 'a') as f:
                f.write(f"{datetime.now()},{cpu_percent},{memory_mb},{read_mb_s},{write_mb_s},{queries_per_second}\n")
            
            # Sleep for a bit
            time.sleep(1.0)
    
    def _get_db_query_count(self):
        """Get the number of queries executed in the database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get statistics from sqlite_stat1 table
            cursor.execute("SELECT COUNT(*) FROM sqlite_master")
            result = cursor.fetchone()[0]
            
            conn.close()
            return result
        except Exception:
            return 0
    
    def generate_report(self, output_file="performance_report.html"):
        """Generate a performance report"""
        if not self.timestamps:
            return False, "No performance data available"
        
        # Calculate average values
        avg_cpu = sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
        avg_memory = sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0
        avg_read = sum(read for read, _ in self.disk_io) / len(self.disk_io) if self.disk_io else 0
        avg_write = sum(write for _, write in self.disk_io) / len(self.disk_io) if self.disk_io else 0
        avg_queries = sum(self.db_queries) / len(self.db_queries) if self.db_queries else 0
        
        # Calculate peak values
        peak_cpu = max(self.cpu_usage) if self.cpu_usage else 0
        peak_memory = max(self.memory_usage) if self.memory_usage else 0
        peak_read = max(read for read, _ in self.disk_io) if self.disk_io else 0
        peak_write = max(write for _, write in self.disk_io) if self.disk_io else 0
        peak_queries = max(self.db_queries) if self.db_queries else 0
        
        # Generate HTML report
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .chart {{ width: 100%; height: 300px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>Performance Report</h1>
            <p>Generated on {datetime.now()}</p>
            
            <h2>Summary</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Average</th>
                    <th>Peak</th>
                </tr>
                <tr>
                    <td>CPU Usage</td>
                    <td>{avg_cpu:.2f}%</td>
                    <td>{peak_cpu:.2f}%</td>
                </tr>
                <tr>
                    <td>Memory Usage</td>
                    <td>{avg_memory:.2f} MB</td>
                    <td>{peak_memory:.2f} MB</td>
                </tr>
                <tr>
                    <td>Disk Read</td>
                    <td>{avg_read:.2f} MB/s</td>
                    <td>{peak_read:.2f} MB/s</td>
                </tr>
                <tr>
                    <td>Disk Write</td>
                    <td>{avg_write:.2f} MB/s</td>
                    <td>{peak_write:.2f} MB/s</td>
                </tr>
                <tr>
                    <td>Database Queries</td>
                    <td>{avg_queries:.2f} queries/s</td>
                    <td>{peak_queries:.2f} queries/s</td>
                </tr>
            </table>
            
            <h2>Recommendations</h2>
            <ul>
        """
        
        # Add recommendations based on performance data
        if peak_cpu > 80:
            html += "<li>CPU usage is high. Consider optimizing CPU-intensive operations.</li>"
        
        if peak_memory > 500:
            html += "<li>Memory usage is high. Check for memory leaks or optimize memory-intensive operations.</li>"
        
        if peak_read > 50 or peak_write > 50:
            html += "<li>Disk I/O is high. Consider optimizing database queries or reducing disk operations.</li>"
        
        if peak_queries > 100:
            html += "<li>Database query rate is high. Consider implementing caching or optimizing queries.</li>"
        
        html += """
            </ul>
            
            <h2>Raw Data</h2>
            <p>See the performance_log.txt file for raw performance data.</p>
        </body>
        </html>
        """
        
        # Write HTML report to file
        with open(output_file, 'w') as f:
            f.write(html)
        
        return True, f"Performance report generated: {output_file}"

class PerformanceChart(FigureCanvas):
    """Performance chart widget"""
    
    def __init__(self, monitor, chart_type):
        self.monitor = monitor
        self.chart_type = chart_type
        
        # Create figure and axis
        self.fig, self.ax = plt.subplots(figsize=(5, 3), dpi=100)
        super().__init__(self.fig)
        
        # Set up plot
        self.setup_plot()
        
        # Set up animation
        self.anim = FuncAnimation(self.fig, self.update_plot, interval=1000, blit=False)
    
    def setup_plot(self):
        """Set up the plot"""
        self.ax.set_xlabel('Time (s)')
        
        if self.chart_type == 'cpu':
            self.ax.set_ylabel('CPU Usage (%)')
            self.ax.set_title('CPU Usage')
            self.line, = self.ax.plot([], [], 'b-')
            self.ax.set_ylim(0, 100)
        
        elif self.chart_type == 'memory':
            self.ax.set_ylabel('Memory Usage (MB)')
            self.ax.set_title('Memory Usage')
            self.line, = self.ax.plot([], [], 'g-')
            self.ax.set_ylim(0, 500)
        
        elif self.chart_type == 'disk':
            self.ax.set_ylabel('Disk I/O (MB/s)')
            self.ax.set_title('Disk I/O')
            self.read_line, = self.ax.plot([], [], 'r-', label='Read')
            self.write_line, = self.ax.plot([], [], 'm-', label='Write')
            self.ax.legend()
            self.ax.set_ylim(0, 50)
        
        elif self.chart_type == 'queries':
            self.ax.set_ylabel('Queries/s')
            self.ax.set_title('Database Queries')
            self.line, = self.ax.plot([], [], 'c-')
            self.ax.set_ylim(0, 100)
        
        self.ax.set_xlim(0, 60)
        self.ax.grid(True)
        self.fig.tight_layout()
    
    def update_plot(self, frame):
        """Update the plot with new data"""
        if not self.monitor.timestamps:
            return
        
        # Update x-axis limit if needed
        max_time = max(self.monitor.timestamps) if self.monitor.timestamps else 0
        if max_time > self.ax.get_xlim()[1]:
            self.ax.set_xlim(0, max_time + 10)
        
        if self.chart_type == 'cpu':
            self.line.set_data(self.monitor.timestamps, self.monitor.cpu_usage)
            
            # Update y-axis limit if needed
            max_cpu = max(self.monitor.cpu_usage) if self.monitor.cpu_usage else 0
            if max_cpu > self.ax.get_ylim()[1] * 0.8:
                self.ax.set_ylim(0, max_cpu * 1.2)
        
        elif self.chart_type == 'memory':
            self.line.set_data(self.monitor.timestamps, self.monitor.memory_usage)
            
            # Update y-axis limit if needed
            max_memory = max(self.monitor.memory_usage) if self.monitor.memory_usage else 0
            if max_memory > self.ax.get_ylim()[1] * 0.8:
                self.ax.set_ylim(0, max_memory * 1.2)
        
        elif self.chart_type == 'disk':
            read_values = [read for read, _ in self.monitor.disk_io]
            write_values = [write for _, write in self.monitor.disk_io]
            
            self.read_line.set_data(self.monitor.timestamps, read_values)
            self.write_line.set_data(self.monitor.timestamps, write_values)
            
            # Update y-axis limit if needed
            max_io = max(max(read_values) if read_values else 0, 
                        max(write_values) if write_values else 0)
            if max_io > self.ax.get_ylim()[1] * 0.8:
                self.ax.set_ylim(0, max_io * 1.2)
        
        elif self.chart_type == 'queries':
            self.line.set_data(self.monitor.timestamps, self.monitor.db_queries)
            
            # Update y-axis limit if needed
            max_queries = max(self.monitor.db_queries) if self.monitor.db_queries else 0
            if max_queries > self.ax.get_ylim()[1] * 0.8:
                self.ax.set_ylim(0, max_queries * 1.2)
        
        self.fig.canvas.draw_idle()

class PerformanceMonitorUI(QMainWindow):
    """UI for performance monitor"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Employee System Performance Monitor")
        self.setGeometry(100, 100, 1000, 600)
        
        # Create performance monitor
        self.monitor = PerformanceMonitor()
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("Performance Monitor")
        header_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        main_layout.addWidget(header_label)
        
        # Description
        description_label = QLabel(
            "This tool monitors system and application performance during stress testing. "
            "It tracks CPU usage, memory usage, disk I/O, and database query rate."
        )
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)
        
        # Charts
        charts_layout = QGridLayout()
        
        # CPU usage chart
        self.cpu_chart = PerformanceChart(self.monitor, 'cpu')
        charts_layout.addWidget(self.cpu_chart, 0, 0)
        
        # Memory usage chart
        self.memory_chart = PerformanceChart(self.monitor, 'memory')
        charts_layout.addWidget(self.memory_chart, 0, 1)
        
        # Disk I/O chart
        self.disk_chart = PerformanceChart(self.monitor, 'disk')
        charts_layout.addWidget(self.disk_chart, 1, 0)
        
        # Database queries chart
        self.queries_chart = PerformanceChart(self.monitor, 'queries')
        charts_layout.addWidget(self.queries_chart, 1, 1)
        
        main_layout.addLayout(charts_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Monitoring")
        self.start_button.clicked.connect(self.start_monitoring)
        
        self.stop_button = QPushButton("Stop Monitoring")
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)
        
        self.report_button = QPushButton("Generate Report")
        self.report_button.clicked.connect(self.generate_report)
        self.report_button.setEnabled(False)
        
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.report_button)
        button_layout.addWidget(exit_button)
        
        main_layout.addLayout(button_layout)
        
        # Set main layout
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.monitor.start_monitoring()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.report_button.setEnabled(False)
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitor.stop_monitoring()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.report_button.setEnabled(True)
    
    def generate_report(self):
        """Generate performance report"""
        success, message = self.monitor.generate_report()
        
        if success:
            QMessageBox.information(self, "Report Generated", message)
        else:
            QMessageBox.warning(self, "Report Generation Failed", message)
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.monitor.stop_monitoring()
        event.accept()

def run_performance_monitor():
    """Run the performance monitor UI"""
    app = QApplication(sys.argv)
    window = PerformanceMonitorUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_performance_monitor()
