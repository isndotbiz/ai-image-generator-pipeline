# Video Generation CLI Pipeline

A comprehensive CLI wrapper that orchestrates the complete video generation pipeline from image curation to final video delivery.

## Overview

The `generate_videos.py` script provides a unified interface to execute the entire video generation pipeline:

1. **Environment Validation** - Verify API keys and dependencies
2. **Image Curation** - Load and prepare images with intelligent prompts
3. **Task Creation** - Submit jobs to RunwayML for video generation
4. **Task Monitoring** - Poll task status until completion
5. **Video Download** - Retrieve and organize completed videos
6. **Batch Reporting** - Generate comprehensive metrics and reports

## Quick Start

### Basic Usage

```bash
# Generate 10 videos for Instagram
python generate_videos.py --max_videos 10 --platform ig

# Generate 5 videos for TikTok with extended timeout
python generate_videos.py --max_videos 5 --platform tt --timeout 900

# Test the pipeline without actual execution
python generate_videos.py --dry-run --platform tw
```

### Required Setup

1. **Environment Variables**:
   ```bash
   export RUNWAYML_API_SECRET="your_runway_api_key_here"
   ```

2. **Optional Smartproxy Configuration** (for enhanced reliability):
   ```bash
   export SMARTPROXY_USERNAME="your_username"
   export SMARTPROXY_PASSWORD="your_password"
   export SMARTPROXY_AUTH_TOKEN="your_auth_token"
   ```

3. **Directory Structure**:
   ```
   .
   ├── video_queue/          # PNG images ready for processing
   ├── video_outputs/        # Generated videos and reports
   └── logs/                 # Pipeline execution logs
   ```

## Command Line Options

| Option | Description | Default | Examples |
|--------|-------------|---------|----------|
| `--max_videos` | Maximum number of videos to generate | 10 | `--max_videos 5` |
| `--platform` | Target platform (ig, tt, tw) | ig | `--platform tt` |
| `--timeout` | Task polling timeout in seconds | 600 | `--timeout 900` |
| `--skip-validation` | Skip environment validation | False | `--skip-validation` |
| `--dry-run` | Show execution plan without running | False | `--dry-run` |
| `--setup-cron` | Show cron job setup instructions | - | `--setup-cron` |

### Platform Options

- **`ig`** - Instagram (16:9 format, optimized framing)
- **`tt`** - TikTok (vertical format, engagement-focused)
- **`tw`** - Twitter (horizontal format, social-optimized)

## Environment Variables

### Required

- **`RUNWAYML_API_SECRET`** - Your RunwayML API key for video generation
  - Get from: https://runwayml.com/account/api-keys
  - Used for: All video generation tasks

### Optional (Smartproxy Integration)

For enhanced reliability and geographic distribution:

- **`SMARTPROXY_USERNAME`** - Smartproxy service username
- **`SMARTPROXY_PASSWORD`** - Smartproxy service password
- **`SMARTPROXY_AUTH_TOKEN`** - Smartproxy authentication token

If configured, the pipeline will:
- Route requests through proxy for improved reliability
- Provide geographic distribution for API calls
- Enhance request success rates

## Pipeline Phases

### Phase 1: Environment Validation

```bash
🔍 Validating environment...
✓ Found required environment variable: RUNWAYML_API_SECRET
✓ Smartproxy configuration detected - enhanced reliability enabled
✓ Directory exists: video_queue
✓ Found 15 images in video queue
✅ Environment validation successful
```

**Validates:**
- Required API keys are present
- Optional Smartproxy configuration
- Directory structure exists
- Images are available in video_queue
- Platform selection is valid

### Phase 2: Image Curation

```bash
🖼️ Phase 1: Image curation and prompt generation...
  1. luxury_watch_rolex_ig_001.png -> gentle camera movement, slow zoom in, cinematic lighting, sophisticated product display...
  2. bitcoin_crypto_tt_002.png -> product showcase rotation, premium display, studio lighting, TikTok vertical engagement...
✅ Selected 10 images for video generation
```

**Process:**
- Loads PNG images from `video_queue/`
- Generates intelligent prompts based on content analysis
- Applies platform-specific optimizations
- Respects `--max_videos` limit

### Phase 3: Task Creation

```bash
🚀 Phase 2: Creating RunwayML video generation tasks...
✅ Successfully created 10 tasks
ℹ️ Task queue saved to: task_queue_20241217_140523.json
```

**Process:**
- Creates RunwayML image-to-video tasks
- Uses intelligent prompts from Phase 1
- Configures video parameters (duration, ratio, etc.)
- Saves task queue for monitoring

### Phase 4: Task Monitoring

```bash
⏳ Phase 3: Polling tasks until completion...
🔄 Poll #1 at 14:05:30 (elapsed: 8.2s)
📊 Active tasks: 10, Completed: 0
  🔍 Checking task_abc123...
    📋 Status: RUNNING
    ⏳ Still running...
✅ Polling completed: 8 succeeded, 2 failed
```

**Process:**
- Polls task status every 8-10 seconds
- Tracks completion status for all tasks
- Respects global timeout (default: 10 minutes)
- Reports detailed progress

### Phase 5: Video Download

```bash
📥 Phase 4: Downloading completed videos...
ℹ️ Found 8 succeeded tasks to download
  📥 Streaming download from: https://storage.runwayml.com/...
  ✅ Downloaded: 15.3 MB
✅ Video download stats:
  Downloaded: 8
  Already existed: 0
  Failed downloads: 0
```

**Process:**
- Downloads videos from successful tasks
- Creates metadata files for traceability
- Handles existing files gracefully
- Reports download statistics

### Phase 6: Batch Reporting

```bash
📊 Phase 5: Generating batch report and metrics...
📈 Batch Report Summary:
  Total tasks: 10
  Succeeded: 8
  Failed: 2
  Success rate: 80.0%
  Total duration: 4m 32.1s
  Videos downloaded: 8
  Total storage: 122.4 MB
```

**Process:**
- Calculates comprehensive metrics
- Generates detailed batch reports
- Provides performance analytics
- Saves results for historical tracking

## Output Files

### Generated Videos

```
video_outputs/
├── luxury_watch_rolex_ig_001.mp4      # Generated video
├── luxury_watch_rolex_ig_001.json     # Video metadata
├── bitcoin_crypto_tt_002.mp4
├── bitcoin_crypto_tt_002.json
└── video_generation_results_20241217_140523.json  # Batch report
```

### Pipeline Logs

```
logs/
├── pipeline_20241217_140523.log        # Detailed execution log
└── pipeline_state_20241217_140523.json # Final pipeline state
```

### Task Files

```
├── runway_polling_results_20241217_140523.json  # Polling results
└── task_queue_20241217_140523.json              # Original task queue
```

## Scheduling Options

### Option 1: Cron Job (Local/Server)

```bash
# Get cron setup instructions
python generate_videos.py --setup-cron

# Manual setup
crontab -e
# Add: 0 2 * * * cd /path/to/project && python generate_videos.py --max_videos 10 --platform ig >> logs/nightly_pipeline.log 2>&1
```

**Benefits:**
- Runs on your local machine or server
- Full control over execution environment
- Direct access to generated content

### Option 2: GitHub Actions (Cloud)

The repository includes `.github/workflows/nightly-video-generation.yml` for automated cloud execution.

**Setup:**

1. **Configure Repository Secrets:**
   ```
   Settings → Secrets and variables → Actions → New repository secret
   ```
   
   Add these secrets:
   - `RUNWAYML_API_SECRET`
   - `SMARTPROXY_USERNAME` (optional)
   - `SMARTPROXY_PASSWORD` (optional)
   - `SMARTPROXY_AUTH_TOKEN` (optional)

2. **Populate Video Queue:**
   ```bash
   # Add PNG images to video_queue/ directory
   git add video_queue/*.png
   git commit -m "Add images for video generation"
   git push
   ```

3. **Workflow Features:**
   - Runs nightly at 2 AM UTC
   - Manual trigger with custom parameters
   - Artifact upload (videos, logs, reports)
   - Comprehensive error reporting
   - Summary generation

**Manual Trigger:**
```
Actions → Nightly Video Generation Pipeline → Run workflow
```

**Benefits:**
- No local infrastructure required
- Automatic artifact storage
- Built-in error reporting
- Scalable execution

## Error Handling

### Common Issues

1. **Missing API Key**
   ```
   ❌ Missing required environment variable: RUNWAYML_API_SECRET
   ```
   **Solution:** Set the `RUNWAYML_API_SECRET` environment variable

2. **No Images Found**
   ```
   ❌ No PNG images found in video_queue
   ```
   **Solution:** Add PNG images to the `video_queue/` directory

3. **Task Creation Failures**
   ```
   ⚠️ 3 tasks failed to create
   ```
   **Solution:** Check API quotas, image formats, and network connectivity

4. **Download Failures**
   ```
   ⚠️ Failed to download video for task abc123
   ```
   **Solution:** Check network connectivity and storage space

### Debugging

1. **Use Dry Run Mode:**
   ```bash
   python generate_videos.py --dry-run
   ```

2. **Check Pipeline Logs:**
   ```bash
   tail -f logs/pipeline_YYYYMMDD_HHMMSS.log
   ```

3. **Review Pipeline State:**
   ```bash
   cat logs/pipeline_state_YYYYMMDD_HHMMSS.json
   ```

4. **Skip Validation (Debugging Only):**
   ```bash
   python generate_videos.py --skip-validation
   ```

## Integration Examples

### Bash Script Wrapper

```bash
#!/bin/bash
# nightly_video_generation.sh

set -e  # Exit on error

# Load environment
source .env

# Set working directory
cd /path/to/video/generation

# Run pipeline with error handling
if python generate_videos.py --max_videos 10 --platform ig; then
    echo "✅ Pipeline completed successfully"
    # Optional: Upload to CDN, send notifications, etc.
else
    echo "❌ Pipeline failed"
    # Optional: Send error notifications
    exit 1
fi
```

### Python Integration

```python
from generate_videos import VideoGenerationPipeline
import argparse

# Create arguments
args = argparse.Namespace(
    max_videos=5,
    platform='ig',
    timeout=600,
    skip_validation=False,
    dry_run=False
)

# Run pipeline
pipeline = VideoGenerationPipeline(args)
success = pipeline.run()

if success:
    print("Pipeline completed successfully")
    # Access pipeline state
    print(f"Videos generated: {pipeline.state['videos_downloaded']}")
else:
    print("Pipeline failed")
    print(f"Errors: {pipeline.state['errors']}")
```

## Performance Tuning

### Optimization Tips

1. **Batch Size:** Start with `--max_videos 5` and increase based on API limits
2. **Timeout:** Increase `--timeout` for larger batches (e.g., `--timeout 1200`)
3. **Smartproxy:** Enable for improved reliability in production
4. **Image Quality:** Use high-quality PNG images (1024x1024 or higher)

### Monitoring

- Review batch reports for success rates
- Monitor API usage and quotas
- Track video generation times
- Analyze failure patterns

## Best Practices

1. **Environment Management:**
   - Use `.env` files for local development
   - Store secrets securely in production
   - Validate environment before execution

2. **Content Organization:**
   - Use descriptive filenames for images
   - Organize by platform and theme
   - Maintain consistent naming conventions

3. **Pipeline Monitoring:**
   - Enable logging for all executions
   - Review batch reports regularly
   - Set up alerting for failures

4. **Resource Management:**
   - Monitor API quotas and usage
   - Manage storage for generated content
   - Clean up old artifacts periodically

## Support

For issues and questions:

1. Check the pipeline logs in `logs/`
2. Review the batch reports in `video_outputs/`
3. Test with `--dry-run` mode first
4. Verify environment configuration
5. Check API key validity and quotas

The CLI wrapper provides comprehensive error reporting and logging to help diagnose and resolve issues quickly.

