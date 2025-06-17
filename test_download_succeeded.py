#!/usr/bin/env python3
"""
Test script for download_succeeded_videos.py functionality
"""

import json
import tempfile
from pathlib import Path
from download_succeeded_videos import VideoDownloader

def create_test_polling_results():
    """Create test polling results with various task scenarios"""
    test_data = {
        "polling_stats": {
            "total_tasks": 3,
            "succeeded": 2,
            "failed": 1,
            "cancelled": 0,
            "still_running": 0,
            "poll_count": 5,
            "start_time": "2025-01-01T10:00:00.000000",
            "end_time": "2025-01-01T10:05:00.000000"
        },
        "task_results": [
            {
                "task_id": "test-task-001",
                "image_path": "test_images/sample1.png",
                "prompt": "beautiful sunset over mountains",
                "target_filename_stub": "sunset_mountains_video",
                "timestamp": "2025-01-01T10:00:00.000000",
                "status": "PENDING",
                "final_status": "SUCCEEDED",
                "completion_time": "2025-01-01T10:02:30.000000",
                "video_url": "https://example.com/video1.mp4",
                "seed": 12345,
                "cluster_id": 1,
                "theme": "nature"
            },
            {
                "task_id": "test-task-002",
                "image_path": "test_images/sample2.png",
                "prompt": "urban cityscape at night",
                "target_filename_stub": "city_night_video",
                "timestamp": "2025-01-01T10:01:00.000000",
                "status": "PENDING",
                "final_status": "SUCCEEDED",
                "completion_time": "2025-01-01T10:04:15.000000",
                "video_url": "https://example.com/video2.mp4"
                # Note: no seed, cluster_id, or theme - testing missing fields
            },
            {
                "task_id": "test-task-003",
                "image_path": "test_images/sample3.png",
                "prompt": "forest in autumn",
                "target_filename_stub": "autumn_forest_video",
                "timestamp": "2025-01-01T10:01:30.000000",
                "status": "PENDING",
                "final_status": "FAILED",
                "completion_time": "2025-01-01T10:03:00.000000",
                "failure_reason": "Content policy violation"
                # Note: FAILED task - should be ignored
            }
        ],
        "generated_at": "2025-01-01T10:05:00.000000"
    }
    
    return test_data

def test_get_succeeded_tasks():
    """Test extraction of SUCCEEDED tasks"""
    print("Testing get_succeeded_tasks...")
    
    downloader = VideoDownloader()
    test_data = create_test_polling_results()
    
    succeeded_tasks = downloader.get_succeeded_tasks(test_data)
    
    # Should find 2 SUCCEEDED tasks
    assert len(succeeded_tasks) == 2, f"Expected 2 SUCCEEDED tasks, got {len(succeeded_tasks)}"
    
    # Check task IDs
    task_ids = [task['task_id'] for task in succeeded_tasks]
    expected_ids = ['test-task-001', 'test-task-002']
    assert task_ids == expected_ids, f"Expected {expected_ids}, got {task_ids}"
    
    print("✅ get_succeeded_tasks test passed")

def test_filename_stub_generation():
    """Test filename stub generation"""
    print("Testing filename stub generation...")
    
    downloader = VideoDownloader()
    
    # Test with target_filename_stub
    task1 = {'target_filename_stub': 'custom_name', 'task_id': 'abc123'}
    stub1 = downloader.generate_filename_stub(task1)
    assert stub1 == 'custom_name', f"Expected 'custom_name', got '{stub1}'"
    
    # Test without target_filename_stub
    task2 = {'task_id': 'def456789'}
    stub2 = downloader.generate_filename_stub(task2)
    assert stub2 == 'video_def45678', f"Expected 'video_def45678', got '{stub2}'"
    
    # Test with empty target_filename_stub
    task3 = {'target_filename_stub': '', 'task_id': 'ghi789'}
    stub3 = downloader.generate_filename_stub(task3)
    assert stub3 == 'video_ghi789', f"Expected 'video_ghi789', got '{stub3}'"
    
    print("✅ filename stub generation test passed")

def test_metadata_creation():
    """Test metadata JSON creation"""
    print("Testing metadata creation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        downloader = VideoDownloader(output_dir=temp_path)
        
        # Create a test video file
        test_video_path = temp_path / "test_video.mp4"
        test_video_path.write_bytes(b"fake video content")
        
        # Test task with all fields
        task = {
            'task_id': 'test-123',
            'image_path': 'input/test.png',
            'prompt': 'test prompt',
            'seed': 42,
            'target_filename_stub': 'test_video',
            'final_status': 'SUCCEEDED',
            'completion_time': '2025-01-01T10:00:00.000000',
            'video_url': 'https://example.com/video.mp4',
            'status': 'PENDING',
            'timestamp': '2025-01-01T09:00:00.000000',
            'cluster_id': 5,
            'theme': 'nature'
        }
        
        metadata_path = temp_path / "test_video.json"
        success = downloader.create_metadata_json(task, test_video_path, metadata_path)
        
        assert success, "Metadata creation should succeed"
        assert metadata_path.exists(), "Metadata file should exist"
        
        # Verify metadata content
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert metadata['video_file'] == 'test_video.mp4'
        assert metadata['input_path'] == 'input/test.png'
        assert metadata['prompt'] == 'test prompt'
        assert metadata['seed'] == 42
        assert metadata['runway_task_json']['task_id'] == 'test-123'
        assert metadata['runway_task_json']['cluster_id'] == 5
        assert metadata['runway_task_json']['theme'] == 'nature'
        assert metadata['file_info']['size_bytes'] == len(b"fake video content")
        
    print("✅ metadata creation test passed")

def test_polling_results_loading():
    """Test loading polling results from file"""
    print("Testing polling results loading...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        downloader = VideoDownloader(output_dir=temp_path)
        
        # Create test polling results file
        test_data = create_test_polling_results()
        results_file = temp_path / "test_results.json"
        
        with open(results_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load and verify
        loaded_data = downloader.load_polling_results(results_file)
        
        assert loaded_data == test_data, "Loaded data should match original"
        assert len(loaded_data['task_results']) == 3, "Should have 3 task results"
        
    print("✅ polling results loading test passed")

def main():
    """Run all tests"""
    print("🧪 Running download_succeeded_videos.py tests...\n")
    
    try:
        test_get_succeeded_tasks()
        test_filename_stub_generation()
        test_metadata_creation()
        test_polling_results_loading()
        
        print("\n🎉 All tests passed!")
        print("✅ The download_succeeded_videos.py script is working correctly")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

