#!/usr/bin/env python3
"""
Regression tests for the centralized logging system.

These tests ensure that:
1. Log files are created when core modules are imported
2. The logging configuration works correctly
3. Both file and console logging are functional
4. Environment variable LOG_LEVEL is respected
"""

import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestLoggingSetup(unittest.TestCase):
    """Test suite for centralized logging configuration."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test logs
        self.test_logs_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()
        os.chdir(self.test_logs_dir)
        
        # Clear any existing loggers to ensure clean state
        logging.getLogger().handlers.clear()
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_logs_dir, ignore_errors=True)
        
        # Clear environment variables
        if 'LOG_LEVEL' in os.environ:
            del os.environ['LOG_LEVEL']
    
    def test_logging_config_creates_logfile(self):
        """Test that importing logging_config creates a log file."""
        # Import logging_config module
        from logging_config import get_logger
        
        # Create a logger
        logger = get_logger("test_module")
        
        # Write a test message
        logger.info("Test log message")
        
        # Check that logs directory and pipeline.log were created
        logs_dir = Path("logs")
        self.assertTrue(logs_dir.exists(), "logs/ directory should be created")
        
        log_file = logs_dir / "pipeline.log"
        self.assertTrue(log_file.exists(), "pipeline.log should be created")
        
        # Check that the log file contains our message
        with open(log_file, 'r') as f:
            content = f.read()
            self.assertIn("Test log message", content)
            self.assertIn("test_module", content)
    
    def test_core_module_imports_create_logfile(self):
        """Test that importing core modules creates log files."""
        # Test generate.py
        try:
            import generate
            logger = generate.logger
            logger.info("Testing generate.py logging")
        except ImportError:
            self.skipTest("generate.py module not available")
        
        # Check that log file exists
        log_file = Path("logs/pipeline.log")
        self.assertTrue(log_file.exists(), "Log file should exist after importing generate.py")
        
        # Test watermark.py (if it has logging)
        try:
            # Import and test if watermark module uses logging
            import watermark
            # Watermark module doesn't use logging yet, but the test structure is here
        except ImportError:
            pass  # Module might not be available in test environment
    
    def test_log_level_environment_variable(self):
        """Test that LOG_LEVEL environment variable is respected."""
        # Set LOG_LEVEL to DEBUG
        os.environ['LOG_LEVEL'] = 'DEBUG'
        
        # Import and create logger
        from logging_config import get_logger
        logger = get_logger("debug_test")
        
        # Check that logger level is DEBUG
        self.assertEqual(logger.level, logging.DEBUG)
        
        # Test with INFO level
        os.environ['LOG_LEVEL'] = 'INFO'
        # Clear cached loggers to test fresh
        import logging_config
        logging_config._loggers.clear()
        
        logger2 = get_logger("info_test")
        self.assertEqual(logger2.level, logging.INFO)
    
    def test_rotating_file_handler_configuration(self):
        """Test that rotating file handler is configured correctly."""
        from logging_config import get_logger
        logger = get_logger("rotation_test")
        
        # Find the rotating file handler
        rotating_handler = None
        for handler in logger.handlers:
            if hasattr(handler, 'maxBytes'):
                rotating_handler = handler
                break
        
        self.assertIsNotNone(rotating_handler, "Should have a rotating file handler")
        self.assertEqual(rotating_handler.maxBytes, 10 * 1024 * 1024, "Should be 10MB max")
        self.assertEqual(rotating_handler.backupCount, 5, "Should keep 5 backup files")
    
    def test_console_and_file_handlers_present(self):
        """Test that both console and file handlers are configured."""
        from logging_config import get_logger
        logger = get_logger("handlers_test")
        
        # Should have exactly 2 handlers: file and console
        self.assertEqual(len(logger.handlers), 2, "Should have 2 handlers")
        
        # Check for StreamHandler (console) and RotatingFileHandler
        handler_types = [type(handler).__name__ for handler in logger.handlers]
        self.assertIn('StreamHandler', handler_types, "Should have console handler")
        self.assertIn('RotatingFileHandler', handler_types, "Should have file handler")
    
    def test_logger_caching(self):
        """Test that loggers are properly cached and reused."""
        from logging_config import get_logger
        
        logger1 = get_logger("cache_test")
        logger2 = get_logger("cache_test")
        
        # Should be the same instance
        self.assertIs(logger1, logger2, "Same logger name should return cached instance")
    
    def test_multiple_imports_safe(self):
        """Test that multiple imports of logging_config are safe."""
        # Import multiple times
        from logging_config import get_logger as get_logger1
        from logging_config import get_logger as get_logger2
        
        logger1 = get_logger1("multi_import_test")
        logger2 = get_logger2("multi_import_test")
        
        # Should be the same instance
        self.assertIs(logger1, logger2)
        
        # Should not have duplicate handlers
        self.assertEqual(len(logger1.handlers), 2, "Should not duplicate handlers")

if __name__ == '__main__':
    unittest.main()

