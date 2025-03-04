import os
import shutil
import zipfile
import json
import sqlite3
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QThread

class BackupWorker(QThread):
    """Worker thread for backup operations"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, operation, source_path, target_path, parent=None):
        super().__init__(parent)
        self.operation = operation  # 'backup', 'restore', 'export'
        self.source_path = source_path
        self.target_path = target_path
    
    def run(self):
        try:
            if self.operation == 'backup':
                self._create_backup()
            elif self.operation == 'restore':
                self._restore_backup()
            elif self.operation == 'export':
                self._export_data()
            
            self.finished.emit(True, "تمت العملية بنجاح")
        except Exception as e:
            self.finished.emit(False, str(e))
    
    def _create_backup(self):
        """Create a backup of the database"""
        self.progress.emit(10, "جاري إنشاء نسخة احتياطية...")
        
        # Create a zip file
        with zipfile.ZipFile(self.target_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add database file
            self.progress.emit(30, "جاري إضافة قاعدة البيانات...")
            zipf.write(self.source_path, os.path.basename(self.source_path))
            
            # Add metadata
            self.progress.emit(60, "جاري إضافة البيانات الوصفية...")
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0',
                'description': 'نسخة احتياطية لقاعدة بيانات نظام إدارة الموظفين'
            }
            
            # Write metadata to a temporary file
            temp_meta_path = os.path.join(os.path.dirname(self.target_path), 'metadata.json')
            with open(temp_meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)
            
            # Add metadata file to zip
            zipf.write(temp_meta_path, 'metadata.json')
            
            # Remove temporary file
            os.remove(temp_meta_path)
        
        self.progress.emit(100, "تم إنشاء النسخة الاحتياطية بنجاح")
    
    def _restore_backup(self):
        """Restore a backup"""
        self.progress.emit(10, "جاري التحقق من النسخة الاحتياطية...")
        
        # Extract the backup
        temp_dir = os.path.join(os.path.dirname(self.source_path), 'temp_restore')
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(self.source_path, 'r') as zipf:
                self.progress.emit(30, "جاري استخراج النسخة الاحتياطية...")
                zipf.extractall(temp_dir)
            
            # Verify metadata
            self.progress.emit(50, "جاري التحقق من البيانات الوصفية...")
            meta_path = os.path.join(temp_dir, 'metadata.json')
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Check version compatibility
                if metadata.get('version') != '1.0':
                    raise ValueError("إصدار النسخة الاحتياطية غير متوافق")
            
            # Find database file
            db_files = [f for f in os.listdir(temp_dir) if f.endswith('.db')]
            if not db_files:
                raise FileNotFoundError("لم يتم العثور على ملف قاعدة البيانات في النسخة الاحتياطية")
            
            # Copy database file to target
            self.progress.emit(70, "جاري استعادة قاعدة البيانات...")
            source_db = os.path.join(temp_dir, db_files[0])
            
            # Close any open connections to the target database
            # This is a dummy connection to ensure the file is closed properly
            try:
                conn = sqlite3.connect(self.target_path)
                conn.close()
            except:
                pass
            
            # Copy the database file
            shutil.copy2(source_db, self.target_path)
            
            # Clean up
            self.progress.emit(90, "جاري تنظيف الملفات المؤقتة...")
            shutil.rmtree(temp_dir)
            
            self.progress.emit(100, "تمت استعادة النسخة الاحتياطية بنجاح")
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise e
    
    def _export_data(self):
        """Export data to Excel or CSV"""
        self.progress.emit(10, "جاري الاتصال بقاعدة البيانات...")
        
        # Connect to the database
        conn = sqlite3.connect(self.source_path)
        
        # Get list of tables
        self.progress.emit(20, "جاري استخراج قائمة الجداول...")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Create Excel writer
        self.progress.emit(30, "جاري إنشاء ملف التصدير...")
        
        if self.target_path.endswith('.xlsx'):
            # Export to Excel with multiple sheets
            writer = pd.ExcelWriter(self.target_path, engine='xlsxwriter')
            
            # Export each table
            total_tables = len(tables)
            for i, (table_name,) in enumerate(tables):
                progress = 30 + int(60 * (i / total_tables))
                self.progress.emit(progress, f"جاري تصدير جدول {table_name}...")
                
                # Skip sqlite internal tables
                if table_name.startswith('sqlite_'):
                    continue
                
                # Read table into DataFrame
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                
                # Write to Excel
                df.to_excel(writer, sheet_name=table_name, index=False)
            
            # Save Excel file
            self.progress.emit(90, "جاري حفظ ملف التصدير...")
            writer.save()
        
        elif self.target_path.endswith('.csv'):
            # Export to CSV (single table or all tables in separate files)
            if len(tables) == 1 or '_' in os.path.basename(self.target_path):
                # Single table export
                table_name = tables[0][0]
                if '_' in os.path.basename(self.target_path):
                    # Extract table name from filename
                    table_name = os.path.basename(self.target_path).split('_')[0]
                
                self.progress.emit(50, f"جاري تصدير جدول {table_name}...")
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                df.to_csv(self.target_path, index=False)
            else:
                # Multiple tables, export to directory
                dir_path = os.path.dirname(self.target_path)
                base_name = os.path.basename(self.target_path).replace('.csv', '')
                
                total_tables = len(tables)
                for i, (table_name,) in enumerate(tables):
                    progress = 30 + int(60 * (i / total_tables))
                    self.progress.emit(progress, f"جاري تصدير جدول {table_name}...")
                    
                    # Skip sqlite internal tables
                    if table_name.startswith('sqlite_'):
                        continue
                    
                    # Read table into DataFrame
                    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                    
                    # Write to CSV
                    csv_path = os.path.join(dir_path, f"{base_name}_{table_name}.csv")
                    df.to_csv(csv_path, index=False)
        
        # Close connection
        conn.close()
        
        self.progress.emit(100, "تم تصدير البيانات بنجاح")


class BackupManager(QObject):
    """Manager for backup, restore, and export operations"""
    
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.worker = None
    
    def create_backup(self, parent_widget=None):
        """Create a backup of the database"""
        if parent_widget is None:
            parent_widget = QApplication.activeWindow()
        
        # Get backup file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"employee_backup_{timestamp}.zip"
        backup_path, _ = QFileDialog.getSaveFileName(
            parent_widget,
            "حفظ النسخة الاحتياطية",
            os.path.join(os.path.dirname(self.db_path), default_name),
            "Zip Files (*.zip)"
        )
        
        if not backup_path:
            return False, "تم إلغاء العملية"
        
        # Create progress dialog
        from PyQt5.QtWidgets import QProgressDialog
        progress = QProgressDialog("جاري إنشاء نسخة احتياطية...", "إلغاء", 0, 100, parent_widget)
        progress.setWindowTitle("إنشاء نسخة احتياطية")
        progress.setMinimumDuration(0)
        progress.setWindowModality(2)  # Application Modal
        
        # Create worker thread
        self.worker = BackupWorker('backup', self.db_path, backup_path)
        self.worker.progress.connect(lambda value, text: progress.setLabelText(f"{text} ({value}%)") or progress.setValue(value))
        self.worker.finished.connect(lambda success, message: self._handle_operation_finished(success, message, progress))
        
        # Start worker
        self.worker.start()
        
        # Show progress dialog
        progress.exec_()
        
        return True, "تم إنشاء النسخة الاحتياطية بنجاح"
    
    def restore_backup(self, parent_widget=None):
        """Restore a backup"""
        if parent_widget is None:
            parent_widget = QApplication.activeWindow()
        
        # Get backup file path
        backup_path, _ = QFileDialog.getOpenFileName(
            parent_widget,
            "اختر ملف النسخة الاحتياطية",
            os.path.dirname(self.db_path),
            "Zip Files (*.zip)"
        )
        
        if not backup_path:
            return False, "تم إلغاء العملية"
        
        # Confirm restore
        reply = QMessageBox.question(
            parent_widget,
            "تأكيد استعادة النسخة الاحتياطية",
            "سيتم استبدال قاعدة البيانات الحالية بالنسخة الاحتياطية. هل أنت متأكد من المتابعة؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return False, "تم إلغاء العملية"
        
        # Create progress dialog
        from PyQt5.QtWidgets import QProgressDialog
        progress = QProgressDialog("جاري استعادة النسخة الاحتياطية...", "إلغاء", 0, 100, parent_widget)
        progress.setWindowTitle("استعادة نسخة احتياطية")
        progress.setMinimumDuration(0)
        progress.setWindowModality(2)  # Application Modal
        
        # Create worker thread
        self.worker = BackupWorker('restore', backup_path, self.db_path)
        self.worker.progress.connect(lambda value, text: progress.setLabelText(f"{text} ({value}%)") or progress.setValue(value))
        self.worker.finished.connect(lambda success, message: self._handle_operation_finished(success, message, progress))
        
        # Start worker
        self.worker.start()
        
        # Show progress dialog
        progress.exec_()
        
        return True, "تمت استعادة النسخة الاحتياطية بنجاح"
    
    def export_data(self, parent_widget=None, table_name=None):
        """Export data to Excel or CSV"""
        if parent_widget is None:
            parent_widget = QApplication.activeWindow()
        
        # Get export file path
        file_filter = "Excel Files (*.xlsx);;CSV Files (*.csv)"
        if table_name:
            default_name = f"{table_name}_{datetime.now().strftime('%Y%m%d')}"
        else:
            default_name = f"employee_export_{datetime.now().strftime('%Y%m%d')}"
            
        export_path, selected_filter = QFileDialog.getSaveFileName(
            parent_widget,
            "تصدير البيانات",
            os.path.join(os.path.dirname(self.db_path), default_name),
            file_filter
        )
        
        if not export_path:
            return False, "تم إلغاء العملية"
        
        # Add extension if not present
        if selected_filter == "Excel Files (*.xlsx)" and not export_path.endswith('.xlsx'):
            export_path += '.xlsx'
        elif selected_filter == "CSV Files (*.csv)" and not export_path.endswith('.csv'):
            export_path += '.csv'
        
        # Create progress dialog
        from PyQt5.QtWidgets import QProgressDialog
        progress = QProgressDialog("جاري تصدير البيانات...", "إلغاء", 0, 100, parent_widget)
        progress.setWindowTitle("تصدير البيانات")
        progress.setMinimumDuration(0)
        progress.setWindowModality(2)  # Application Modal
        
        # Create worker thread
        self.worker = BackupWorker('export', self.db_path, export_path)
        self.worker.progress.connect(lambda value, text: progress.setLabelText(f"{text} ({value}%)") or progress.setValue(value))
        self.worker.finished.connect(lambda success, message: self._handle_operation_finished(success, message, progress))
        
        # Start worker
        self.worker.start()
        
        # Show progress dialog
        progress.exec_()
        
        return True, "تم تصدير البيانات بنجاح"
    
    def _handle_operation_finished(self, success, message, progress_dialog):
        """Handle operation finished signal"""
        # Close progress dialog
        progress_dialog.close()
        
        # Show result message
        if success:
            QMessageBox.information(QApplication.activeWindow(), "نجاح", message)
        else:
            QMessageBox.critical(QApplication.activeWindow(), "خطأ", f"حدث خطأ: {message}")
