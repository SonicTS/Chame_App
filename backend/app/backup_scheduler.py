#!/usr/bin/env python3
# backup_scheduler.py
# Automated backup scheduler for the Chame database

import os
import sys
import schedule
import time
import datetime
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_backup import create_scheduled_backup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_daily_backup():
    """Create a daily backup"""
    try:
        logger.info("Starting daily backup...")
        result = create_scheduled_backup("daily")
        
        if result['success']:
            logger.info(f"Daily backup completed: {result['message']}")
        else:
            logger.error(f"Daily backup failed: {result['message']}")
            
    except Exception as e:
        logger.error(f"Daily backup error: {e}")

def create_weekly_backup():
    """Create a weekly backup"""
    try:
        logger.info("Starting weekly backup...")
        result = create_scheduled_backup("weekly")
        
        if result['success']:
            logger.info(f"Weekly backup completed: {result['message']}")
        else:
            logger.error(f"Weekly backup failed: {result['message']}")
            
    except Exception as e:
        logger.error(f"Weekly backup error: {e}")

def cleanup_old_backups():
    """Clean up old backups"""
    try:
        logger.info("Starting backup cleanup...")
        from services.database_backup import DatabaseBackupManager
        
        manager = DatabaseBackupManager()
        result = manager.cleanup_old_backups(daily_keep=7, weekly_keep=4)
        
        if result['success']:
            logger.info(f"Backup cleanup completed: {result['message']}")
        else:
            logger.error(f"Backup cleanup failed: {result['message']}")
            
    except Exception as e:
        logger.error(f"Backup cleanup error: {e}")

def setup_scheduler():
    """Setup the backup scheduler"""
    logger.info("Setting up backup scheduler...")
    
    # Schedule daily backups at 2 AM
    schedule.every().day.at("02:00").do(create_daily_backup)
    
    # Schedule weekly backups on Sunday at 3 AM
    schedule.every().sunday.at("03:00").do(create_weekly_backup)
    
    # Schedule cleanup on the first day of each month at 4 AM
    schedule.every().month.do(cleanup_old_backups)
    
    logger.info("Backup scheduler configured:")
    logger.info("  - Daily backups: Every day at 2:00 AM")
    logger.info("  - Weekly backups: Every Sunday at 3:00 AM")
    logger.info("  - Cleanup: First day of each month at 4:00 AM")

def run_scheduler():
    """Run the backup scheduler"""
    logger.info("Starting backup scheduler...")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Backup scheduler stopped by user")
    except Exception as e:
        logger.error(f"Backup scheduler error: {e}")

def run_test_backup():
    """Run a test backup to verify everything works"""
    logger.info("Running test backup...")
    
    try:
        result = create_scheduled_backup("manual")
        
        if result['success']:
            logger.info(f"Test backup successful: {result['message']}")
            return True
        else:
            logger.error(f"Test backup failed: {result['message']}")
            return False
            
    except Exception as e:
        logger.error(f"Test backup error: {e}")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Chame Database Backup Scheduler')
    parser.add_argument('--test', action='store_true', 
                       help='Run a test backup and exit')
    parser.add_argument('--run-once', choices=['daily', 'weekly', 'cleanup'], 
                       help='Run a specific backup task once and exit')
    parser.add_argument('--daemon', action='store_true', 
                       help='Run as a daemon (default behavior)')
    
    args = parser.parse_args()
    
    if args.test:
        success = run_test_backup()
        sys.exit(0 if success else 1)
    
    elif args.run_once:
        if args.run_once == 'daily':
            create_daily_backup()
        elif args.run_once == 'weekly':
            create_weekly_backup()
        elif args.run_once == 'cleanup':
            cleanup_old_backups()
        sys.exit(0)
    
    else:
        # Default behavior: run as scheduler daemon
        setup_scheduler()
        run_scheduler()

if __name__ == '__main__':
    main()
