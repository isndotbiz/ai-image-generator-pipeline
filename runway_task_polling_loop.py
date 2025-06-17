#!/usr/bin/env python3
"""
RunwayML Task Polling Loop

Implements a queue-driven polling loop that:
- Every 8-10 seconds calls client.tasks.retrieve(task_id)
- Prints status
- On SUCCEEDED, extracts task.output[0] (URL)
- On FAILED, logs failure_reason and continues
- Stops polling when all tasks in the batch are terminal or after a global timeout (e.g. 10 min)

Usage:
    python runway_task_polling_loop.py [--task-queue-file path/to/task_queue.json] [--timeout 600]
"""

import os
import sys
import json
import time
import argparse
import random
from datetime import datetime
from pathlib import Path
from runwayml import RunwayML

class RunwayTaskPoller:
    def __init__(self, api_key=None, poll_interval_range=(8, 10), global_timeout=600):
        self.api_key = api_key or os.getenv('RUNWAYML_API_SECRET')
        if not self.api_key:
            raise ValueError("RUNWAYML_API_SECRET environment variable not set")
        self.client = RunwayML(api_key=self.api_key)
        self.poll_interval_range = poll_interval_range
        self.global_timeout = global_timeout
        self.terminal_states = {'SUCCEEDED', 'FAILED', 'CANCELLED'}
        self.stats = {
            'total_tasks': 0,
            'succeeded': 0,
            'failed': 0,
            'cancelled': 0,
            'still_running': 0,
            'poll_count': 0,
            'start_time': None,
            'end_time': None
        }
    
    def load_task_queue(self, queue_file_path):
        queue_path = Path(queue_file_path)
        if not queue_path.exists():
            raise FileNotFoundError(f"Task queue file not found: {queue_file_path}")
        
        with open(queue_path, 'r') as f:
            task_queue = json.load(f)
        
        valid_tasks = [task for task in task_queue if task.get('task_id')]
        print(f"📋 Loaded {len(valid_tasks)} valid tasks from {queue_file_path}")
        return valid_tasks
    
    def get_next_poll_interval(self):
        return random.uniform(*self.poll_interval_range)
    
    def poll_task_status(self, task_id):
        try:
            task = self.client.tasks.retrieve(task_id)
            return task
        except Exception as e:
            print(f"⚠️ Error retrieving task {task_id}: {e}")
            return None

    def process_task_result(self, task, task_info):
        task_info = task_info.copy()
        task_info['final_status'] = task.status
        task_info['completion_time'] = datetime.now().isoformat()
        
        if task.status == 'SUCCEEDED':
            if hasattr(task, 'output') and task.output and len(task.output) > 0:
                video_url = task.output[0]
                task_info['video_url'] = video_url
                print(f"✅ Task {task.id} SUCCEEDED")
                print(f"   📹 Video URL: {video_url}")
                self.stats['succeeded'] += 1
            else:
                print(f"⚠️ Task {task.id} SUCCEEDED but no output URL found")
                task_info['error'] = "No output URL in successful task"
        
        elif task.status == 'FAILED':
            failure_reason = getattr(task, 'failure_reason', 'Unknown error')
            task_info['failure_reason'] = failure_reason
            print(f"❌ Task {task.id} FAILED")
            print(f"   🚫 Reason: {failure_reason}")
            self.stats['failed'] += 1
        
        elif task.status == 'CANCELLED':
            print(f"🚫 Task {task.id} CANCELLED")
            self.stats['cancelled'] += 1
        
        return task_info
    
    def save_results(self, results, output_file=None):
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"runway_polling_results_{timestamp}.json"
        
        results_data = {
            'polling_stats': self.stats,
            'task_results': results,
            'generated_at': datetime.now().isoformat()
        }
        
        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"💾 Results saved to: {output_file}")
    
    def poll_task_queue(self, task_queue, save_results=True, output_file=None):
        print(f"🚀 Starting polling loop for {len(task_queue)} tasks")
        print(f"⏱️ Poll interval: {self.poll_interval_range[0]}-{self.poll_interval_range[1]}s")
        print(f"⏰ Global timeout: {self.global_timeout}s ({self.global_timeout/60:.1f} minutes)")
        print("=" * 70)
        
        self.stats['total_tasks'] = len(task_queue)
        self.stats['start_time'] = datetime.now().isoformat()
        start_time = time.time()
        active_tasks = task_queue.copy()
        completed_tasks = []
        
        try:
            while active_tasks and (time.time() - start_time) < self.global_timeout:
                self.stats['poll_count'] += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                elapsed = time.time() - start_time
                
                print(f"\n🔄 Poll #{self.stats['poll_count']} at {current_time} (elapsed: {elapsed:.1f}s)")
                print(f"📊 Active tasks: {len(active_tasks)}, Completed: {len(completed_tasks)}")
                
                newly_completed = []
                
                for task_info in active_tasks:
                    task_id = task_info['task_id']
                    print(f"\n  🔍 Checking {task_id}...")
                    
                    task = self.poll_task_status(task_id)
                    
                    if task is None:
                        print(f"    ⚠️ Failed to retrieve task status")
                        continue
                    
                    print(f"    📋 Status: {task.status}")
                    
                    if task.status in self.terminal_states:
                        completed_task_info = self.process_task_result(task, task_info)
                        newly_completed.append(completed_task_info)
                    else:
                        print(f"    ⏳ Still running...")
                
                if newly_completed:
                    for completed_task in newly_completed:
                        active_tasks.remove(next(
                            task for task in active_tasks 
                            if task['task_id'] == completed_task['task_id']
                        ))
                        completed_tasks.append(completed_task)
                
                if not active_tasks:
                    print(f"\n🎉 All tasks completed!")
                    break
                
                if active_tasks:  
                    wait_time = self.get_next_poll_interval()
                    print(f"\n⏸️ Waiting {wait_time:.1f}s before next poll...")
                    time.sleep(wait_time)
            
            self.stats['end_time'] = datetime.now().isoformat()
            total_elapsed = time.time() - start_time
            
            if active_tasks:
                print(f"\n⏰ Global timeout reached after {total_elapsed:.1f}s")
                print(f"⚠️ {len(active_tasks)} tasks still running:")
                for task in active_tasks:
                    print(f"  - {task['task_id']}")
                self.stats['still_running'] = len(active_tasks)
            
            self.print_final_stats(total_elapsed)
            
            if save_results:
                all_results = completed_tasks + active_tasks 
                self.save_results(all_results, output_file)
            
            return completed_tasks
            
        except KeyboardInterrupt:
            print(f"\n⏹️ Polling interrupted by user")
            self.stats['end_time'] = datetime.now().isoformat()
            
            if save_results:
                all_results = completed_tasks + active_tasks
                self.save_results(all_results, output_file)
            
            return completed_tasks
    
    def print_final_stats(self, total_elapsed):
        print(f"\n{'=' * 70}")
        print(f"📊 FINAL POLLING STATISTICS")
        print(f"{'=' * 70}")
        print(f"⏱️ Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
        print(f"🔄 Total polls: {self.stats['poll_count']}")
        print(f"📋 Total tasks: {self.stats['total_tasks']}")
        print(f"✅ Succeeded: {self.stats['succeeded']}")
        print(f"❌ Failed: {self.stats['failed']}")
        print(f"🚫 Cancelled: {self.stats['cancelled']}")
        print(f"⏳ Still running: {self.stats['still_running']}")
        
        if self.stats['total_tasks'] > 0:
            success_rate = (self.stats['succeeded'] / self.stats['total_tasks']) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")
        
        if self.stats['poll_count'] > 0:
            avg_poll_interval = total_elapsed / self.stats['poll_count']
            print(f"⚡ Avg poll interval: {avg_poll_interval:.1f}s")

def find_latest_task_queue_file(directory="video_outputs"):
    queue_dir = Path(directory)
    if not queue_dir.exists():
        return None
    
    queue_files = list(queue_dir.glob("task_queue_*.json"))
    
    if not queue_files:
        return None
    
    return max(queue_files, key=lambda f: f.stat().st_mtime)

def main():
    parser = argparse.ArgumentParser(
        description="Poll RunwayML tasks until completion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runway_task_polling_loop.py
  python runway_task_polling_loop.py --task-queue-file video_outputs/task_queue_20240101_120000.json
  python runway_task_polling_loop.py --timeout 1200 --poll-min 5 --poll-max 15
        """
    )
    
    parser.add_argument(
        "--task-queue-file",
        help="Path to task queue JSON file (default: find latest in video_outputs/)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Global timeout in seconds (default: 600 = 10 minutes)"
    )
    
    parser.add_argument(
        "--poll-min",
        type=int,
        default=8,
        help="Minimum polling interval in seconds (default: 8)"
    )
    
    parser.add_argument(
        "--poll-max",
        type=int,
        default=10,
        help="Maximum polling interval in seconds (default: 10)"
    )
    
    parser.add_argument(
        "--output-file",
        help="Output file for results (default: auto-generated)"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to file"
    )
    
    args = parser.parse_args()
    
    if args.poll_min >= args.poll_max:
        print("❌ Error: --poll-min must be less than --poll-max")
        sys.exit(1)
    
    if args.task_queue_file:
        queue_file = args.task_queue_file
    else:
        queue_file = find_latest_task_queue_file()
        if not queue_file:
            print("❌ No task queue file found in video_outputs/")
            print("Please specify --task-queue-file or create tasks first")
            sys.exit(1)
        print(f"📁 Using latest task queue file: {queue_file}")
    
    if not os.getenv('RUNWAYML_API_SECRET'):
        print("❌ RUNWAYML_API_SECRET environment variable not set")
        print("Please set your Runway API key: export RUNWAYML_API_SECRET='your_key_here'")
        sys.exit(1)
    
    try:
        poller = RunwayTaskPoller(
            poll_interval_range=(args.poll_min, args.poll_max),
            global_timeout=args.timeout
        )
        
        task_queue = poller.load_task_queue(queue_file)
        
        if not task_queue:
            print("❌ No valid tasks found in queue file")
            sys.exit(1)
        
        completed_tasks = poller.poll_task_queue(
            task_queue,
            save_results=not args.no_save,
            output_file=args.output_file
        )
        
        print(f"\n🏁 Polling completed with {len(completed_tasks)} finished tasks")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

