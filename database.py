import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import DB

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketDatabase:
    def __init__(self):
        """Initialize database connection and create tables if they don't exist."""
        # Ensure the directory exists
        os.makedirs(os.path.dirname(DB['path']), exist_ok=True)
        
        self.db_path = DB['path']
        self._create_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _create_tables(self):
        """Create necessary database tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    item_name TEXT,
                    quality INTEGER NOT NULL,
                    avg_item_count REAL NOT NULL,
                    avg_price REAL NOT NULL,
                    data_points INTEGER NOT NULL,
                    last_updated TIMESTAMP NOT NULL,
                    UNIQUE(location, item_id, quality)
                )
            """)
            
            # Create indices for common queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_location_stats 
                ON history_stats(location, avg_item_count, avg_price)
            """)
    
    def insert_or_update_history_stats(self, stats: List[Dict[str, Any]]):
        """
        Insert or update historical statistics in the database.
        
        Args:
            stats: List of dictionaries containing aggregated statistics:
                  {
                      'location': str,
                      'item_id': str,
                      'quality': int,
                      'avg_item_count': float,
                      'avg_price': float,
                      'data_points': int
                  }
        """
        with self._get_connection() as conn:
            for stat in stats:
                try:
                    conn.execute("""
                        INSERT INTO history_stats 
                        (location, item_id, item_name, quality, avg_item_count, avg_price, data_points, last_updated)
                        VALUES (:location, :item_id, :item_name, :quality, :avg_item_count, :avg_price, :data_points, :last_updated)
                        ON CONFLICT(location, item_id, quality) DO UPDATE SET
                            item_name = :item_name,
                            avg_item_count = :avg_item_count,
                            avg_price = :avg_price,
                            data_points = :data_points,
                            last_updated = :last_updated
                    """, {
                        **stat,
                        'last_updated': datetime.utcnow().isoformat()
                    })
                except sqlite3.Error as e:
                    logger.error(f"Error inserting/updating stats for {stat['item_id']}: {e}")
    
    def query_top_items(self, location: str, limit: int = 50, min_data_points: Optional[int] = None,
                     min_volume: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Query top items for a given location based on market activity (volume * price).
        
        Args:
            location: The city/location to query for
            limit: Maximum number of items to return
            min_data_points: Minimum number of data points required (defaults to config value)
            min_volume: Minimum average daily volume required
        
        Returns:
            List of dictionaries containing item statistics, sorted by market activity
        """
        if min_data_points is None:
            min_data_points = DB['min_data_points']
            
        # Build the WHERE clause dynamically based on filters
        where_clauses = ["location = ?"]
        params = [location]
        
        if min_data_points:
            where_clauses.append("data_points >= ?")
            params.append(min_data_points)
            
        if min_volume:
            where_clauses.append("avg_item_count >= ?")
            params.append(min_volume)
            
        where_clause = " AND ".join(where_clauses)
            
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT 
                    location,
                    item_name,
                    item_id,
                    quality,
                    avg_item_count,
                    avg_price,
                    data_points,
                    last_updated,
                    (avg_item_count * avg_price) as market_value
                FROM history_stats
                WHERE {where_clause}
                ORDER BY market_value DESC
                {f'LIMIT {limit}' if limit else ''}
            """, params)
            
            results = []
            for row in cursor.fetchall():
                item_data = dict(row)
                # Add calculated fields
                item_data['market_value'] = item_data['avg_item_count'] * item_data['avg_price']
                results.append(item_data)
                
            return results
    
    def get_item_stats(self, item_id: str, quality: int, location: str) -> Optional[Dict[str, Any]]:
        """
        Get historical statistics for a specific item.
        
        Args:
            item_id: The unique item identifier
            quality: Item quality level
            location: The city/location
            
        Returns:
            Dictionary containing item statistics or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT *
                FROM history_stats
                WHERE item_id = ? AND quality = ? AND location = ?
            """, (item_id, quality, location))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_stale_items(self, max_age_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get items that haven't been updated recently.
        
        Args:
            max_age_hours: Maximum age in hours before an item is considered stale
            
        Returns:
            List of dictionaries containing stale item information
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT *
                FROM history_stats
                WHERE datetime(last_updated) < datetime('now', ?)
                ORDER BY last_updated ASC
            """, (f'-{max_age_hours} hours',))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_data(self, max_age_days: Optional[int] = None):
        """
        Remove data older than the specified age.
        
        Args:
            max_age_days: Maximum age in days before data is removed (defaults to config value)
        """
        if max_age_days is None:
            max_age_days = DB['max_history_days']
            
        with self._get_connection() as conn:
            conn.execute("""
                DELETE FROM history_stats
                WHERE datetime(last_updated) < datetime('now', ?)
            """, (f'-{max_age_days} days',)) 