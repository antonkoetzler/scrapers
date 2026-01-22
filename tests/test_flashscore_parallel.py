"""Unit tests for FlashScore parallel scraping functions.

Tests the parallel league scraping and odds fetching functionality.
"""
import sys
import time
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Optional

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestFetchOddsWithRetry(unittest.TestCase):
    """Tests for fetch_odds_with_retry function."""
    
    @patch('sports_data.flashscore.fetch_match_odds')
    def test_fetch_odds_success_first_try(self, mock_fetch_odds):
        """Test successful odds fetch on first attempt."""
        from sports_data.flashscore import fetch_odds_with_retry
        
        mock_odds = [{'market_name': '1X2', 'odds_value': 1.5}]
        mock_fetch_odds.return_value = mock_odds
        
        event_id, result = fetch_odds_with_retry("test123")
        
        self.assertEqual(event_id, "test123")
        self.assertEqual(result, mock_odds)
        mock_fetch_odds.assert_called_once_with("test123")
    
    @patch('sports_data.flashscore.fetch_match_odds')
    @patch('time.sleep')
    def test_fetch_odds_retry_on_failure(self, mock_sleep, mock_fetch_odds):
        """Test retry logic on initial failure."""
        from sports_data.flashscore import fetch_odds_with_retry
        
        mock_odds = [{'market_name': '1X2', 'odds_value': 1.5}]
        # Fail first 2 attempts, succeed on 3rd
        mock_fetch_odds.side_effect = [None, None, mock_odds]
        
        event_id, result = fetch_odds_with_retry("test123", max_retries=3)
        
        self.assertEqual(event_id, "test123")
        self.assertEqual(result, mock_odds)
        self.assertEqual(mock_fetch_odds.call_count, 3)
        # Exponential backoff: 1s, 2s
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)
    
    @patch('sports_data.flashscore.fetch_match_odds')
    @patch('time.sleep')
    def test_fetch_odds_all_retries_fail(self, mock_sleep, mock_fetch_odds):
        """Test when all retry attempts fail."""
        from sports_data.flashscore import fetch_odds_with_retry
        
        mock_fetch_odds.return_value = None
        
        event_id, result = fetch_odds_with_retry("test123", max_retries=3)
        
        self.assertEqual(event_id, "test123")
        self.assertIsNone(result)
        self.assertEqual(mock_fetch_odds.call_count, 3)


class TestFetchOddsBatch(unittest.TestCase):
    """Tests for fetch_odds_batch function."""
    
    @patch('sports_data.flashscore.fetch_odds_with_retry')
    def test_batch_empty_list(self, mock_fetch_retry):
        """Test with empty event_ids list."""
        from sports_data.flashscore import fetch_odds_batch
        
        result = fetch_odds_batch([])
        
        self.assertEqual(result, {})
        mock_fetch_retry.assert_not_called()
    
    @patch('sports_data.flashscore.fetch_odds_with_retry')
    def test_batch_single_event(self, mock_fetch_retry):
        """Test with single event_id."""
        from sports_data.flashscore import fetch_odds_batch
        
        mock_odds = [{'market_name': '1X2', 'odds_value': 1.5}]
        mock_fetch_retry.return_value = ("event1", mock_odds)
        
        result = fetch_odds_batch(["event1"], max_workers=1)
        
        self.assertEqual(result, {"event1": mock_odds})
    
    @patch('sports_data.flashscore.fetch_odds_with_retry')
    def test_batch_multiple_events(self, mock_fetch_retry):
        """Test with multiple event_ids."""
        from sports_data.flashscore import fetch_odds_batch
        
        # Setup mock to return different odds for each event
        def mock_fetch(event_id):
            return (event_id, [{'odds_value': float(event_id[-1])}])
        
        mock_fetch_retry.side_effect = mock_fetch
        
        event_ids = ["event1", "event2", "event3"]
        result = fetch_odds_batch(event_ids, max_workers=3)
        
        self.assertEqual(len(result), 3)
        for eid in event_ids:
            self.assertIn(eid, result)
            self.assertIsNotNone(result[eid])
    
    @patch('sports_data.flashscore.fetch_odds_with_retry')
    def test_batch_handles_failures(self, mock_fetch_retry):
        """Test batch handling when some events fail."""
        from sports_data.flashscore import fetch_odds_batch
        
        # Event 2 fails
        def mock_fetch(event_id):
            if event_id == "event2":
                return (event_id, None)
            return (event_id, [{'odds_value': 1.5}])
        
        mock_fetch_retry.side_effect = mock_fetch
        
        event_ids = ["event1", "event2", "event3"]
        result = fetch_odds_batch(event_ids, max_workers=3)
        
        self.assertEqual(len(result), 3)
        self.assertIsNotNone(result["event1"])
        self.assertIsNone(result["event2"])  # Failed
        self.assertIsNotNone(result["event3"])
    
    @patch('sports_data.flashscore.fetch_odds_with_retry')
    def test_batch_respects_max_workers(self, mock_fetch_retry):
        """Test that max_workers limits concurrency."""
        from sports_data.flashscore import fetch_odds_batch
        
        concurrent_count = [0]
        max_concurrent = [0]
        lock = threading.Lock()
        
        def mock_fetch(event_id):
            with lock:
                concurrent_count[0] += 1
                if concurrent_count[0] > max_concurrent[0]:
                    max_concurrent[0] = concurrent_count[0]
            time.sleep(0.01)  # Simulate work
            with lock:
                concurrent_count[0] -= 1
            return (event_id, [{'odds_value': 1.5}])
        
        mock_fetch_retry.side_effect = mock_fetch
        
        # 10 events with max 3 workers
        event_ids = [f"event{i}" for i in range(10)]
        result = fetch_odds_batch(event_ids, max_workers=3)
        
        self.assertEqual(len(result), 10)
        self.assertLessEqual(max_concurrent[0], 3)


class TestSetupPageResourceBlocking(unittest.TestCase):
    """Tests for _setup_page_resource_blocking function."""
    
    def test_resource_blocking_routes_created(self):
        """Test that resource blocking routes are set up correctly."""
        from sports_data.flashscore import _setup_page_resource_blocking
        
        mock_page = Mock()
        _setup_page_resource_blocking(mock_page)
        
        # Should set up routes for images, fonts, media, and analytics
        self.assertGreaterEqual(mock_page.route.call_count, 7)
        
        # Verify some of the patterns
        route_calls = [str(call) for call in mock_page.route.call_args_list]
        patterns_found = 0
        expected_patterns = ['png', 'woff', 'mp4', 'analytics', 'gtm.js']
        for pattern in expected_patterns:
            if any(pattern in call for call in route_calls):
                patterns_found += 1
        self.assertGreaterEqual(patterns_found, 3)


class TestSafeLog(unittest.TestCase):
    """Tests for thread-safe logging."""
    
    @patch('sports_data.flashscore.TUI')
    def test_safe_log_info(self, mock_tui):
        """Test thread-safe info logging."""
        from sports_data.flashscore import _safe_log
        
        _safe_log("info", "Test message")
        mock_tui.info.assert_called_once_with("Test message")
    
    @patch('sports_data.flashscore.TUI')
    def test_safe_log_error(self, mock_tui):
        """Test thread-safe error logging."""
        from sports_data.flashscore import _safe_log
        
        _safe_log("error", "Error message")
        mock_tui.error.assert_called_once_with("Error message")
    
    @patch('sports_data.flashscore.TUI')
    def test_safe_log_concurrent(self, mock_tui):
        """Test that concurrent logging doesn't cause issues."""
        from sports_data.flashscore import _safe_log
        
        threads = []
        for i in range(10):
            t = threading.Thread(target=_safe_log, args=("info", f"Message {i}"))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        self.assertEqual(mock_tui.info.call_count, 10)


class TestFetchMatchOdds(unittest.TestCase):
    """Tests for fetch_match_odds function."""
    
    @patch('requests.get')
    def test_fetch_odds_success(self, mock_get):
        """Test successful odds fetch."""
        from sports_data.flashscore import fetch_match_odds
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'findOddsByEventId': {
                    'markets': [
                        {
                            'name': '1X2',
                            'marketType': 'main',
                            'outcomes': [
                                {
                                    'name': 'Home',
                                    'bookmakerOdds': [
                                        {
                                            'bookmaker': {'id': 1, 'name': 'Bet365'},
                                            'odds': 1.5
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        }
        mock_get.return_value = mock_response
        
        result = fetch_match_odds("test123")
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['market_name'], '1X2')
        self.assertEqual(result[0]['odds_value'], 1.5)
    
    @patch('requests.get')
    def test_fetch_odds_rate_limited(self, mock_get):
        """Test handling of 429 rate limit response."""
        from sports_data.flashscore import fetch_match_odds
        
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        result = fetch_match_odds("test123")
        
        self.assertIsNone(result)
    
    @patch('requests.get')
    def test_fetch_odds_server_error(self, mock_get):
        """Test handling of server error."""
        from sports_data.flashscore import fetch_match_odds
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = fetch_match_odds("test123")
        
        self.assertIsNone(result)
    
    @patch('requests.get')
    def test_fetch_odds_network_error(self, mock_get):
        """Test handling of network error."""
        from sports_data.flashscore import fetch_match_odds
        
        mock_get.side_effect = Exception("Connection error")
        
        result = fetch_match_odds("test123")
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
