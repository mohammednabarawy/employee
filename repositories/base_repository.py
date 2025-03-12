from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import sqlite3
import logging
from contextlib import contextmanager
from utils.exceptions import DatabaseOperationError, TransactionError, PayrollValidationError

class ValidationError(Exception):
    """Exception for data validation errors"""
    pass

class BaseRepository:
    """Base repository class with common database operations"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        try:
            yield
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Transaction failed: {str(e)}")
            raise TransactionError(f"Transaction failed: {str(e)}")
    
    def execute_query(
            self,
            query: str,
            params: Optional[tuple] = None,
            fetch: bool = False
        ) -> Optional[List[Dict[str, Any]]]:
        """Execute a SQL query with proper error handling"""
        try:
            cursor = self.db.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return None
            
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Database integrity error: {str(e)}")
            raise ValidationError(f"Data validation failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Database error: {str(e)}")
            raise DatabaseOperationError(f"Database operation failed: {str(e)}")
    
    def get_by_id(self, table: str, id: int) -> Optional[Dict[str, Any]]:
        """Get a record by ID"""
        query = f"SELECT * FROM {table} WHERE id = ?"
        result = self.execute_query(query, (id,), fetch=True)
        return result[0] if result else None
    
    def create(
            self,
            table: str,
            data: Dict[str, Any],
            created_by: int
        ) -> int:
        """Create a new record"""
        columns = list(data.keys()) + ['created_by', 'created_at']
        values = list(data.values()) + [created_by, datetime.now()]
        placeholders = ','.join(['?' for _ in range(len(columns))])
        
        query = f"""
            INSERT INTO {table} ({','.join(columns)})
            VALUES ({placeholders})
        """
        
        with self.transaction():
            cursor = self.db.cursor()
            cursor.execute(query, values)
            return cursor.lastrowid
    
    def update(
            self,
            table: str,
            id: int,
            data: Dict[str, Any],
            updated_by: int
        ) -> bool:
        """Update an existing record"""
        set_clause = ','.join([f"{k}=?" for k in data.keys()])
        values = list(data.values()) + [updated_by, datetime.now(), id]
        
        query = f"""
            UPDATE {table}
            SET {set_clause},
                updated_by = ?,
                updated_at = ?
            WHERE id = ?
        """
        
        with self.transaction():
            self.execute_query(query, tuple(values))
            return True
    
    def delete(self, table: str, id: int) -> bool:
        """Delete a record"""
        query = f"DELETE FROM {table} WHERE id = ?"
        
        with self.transaction():
            self.execute_query(query, (id,))
            return True
    
    def exists(self, table: str, conditions: Dict[str, Any]) -> bool:
        """Check if records exist matching the conditions"""
        where_clause = ' AND '.join([f"{k}=?" for k in conditions.keys()])
        query = f"SELECT EXISTS(SELECT 1 FROM {table} WHERE {where_clause})"
        
        result = self.execute_query(query, tuple(conditions.values()), fetch=True)
        return bool(result[0]['EXISTS(SELECT 1 FROM {table} WHERE {where_clause})'])
    
    def count(self, table: str, conditions: Optional[Dict[str, Any]] = None) -> int:
        """Count records matching the conditions"""
        query = f"SELECT COUNT(*) as count FROM {table}"
        params = None
        
        if conditions:
            where_clause = ' AND '.join([f"{k}=?" for k in conditions.keys()])
            query += f" WHERE {where_clause}"
            params = tuple(conditions.values())
        
        result = self.execute_query(query, params, fetch=True)
        return result[0]['count']
