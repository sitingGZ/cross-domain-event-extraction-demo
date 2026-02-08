# Web-Based Event Extraction Annotation Interface - Usage Guide

## Quick Start

### 1. Launch the Application
```bash
cd /user/debi5729/Cross-Domain-Text-Event-Extraction
python web_dash_app.py
```

The application will be available at: **http://localhost:8050**

### 2. Prepare Your Data

Create a JSON file with documents in this format:
```json
{
  "documents": [
    {
      "id": "doc_001",
      "text": "Your text here..."
    },
    {
      "id": "doc_002",
      "text": "Another text..."
    }
  ]
}
```

A sample file is provided: `sample_documents.json`

---

## Step-by-Step Workflow

### Step 1: Upload Documents
1. Click the upload area in the "1. Upload Data" section
2. Select your JSON file
3. System will validate and show "✓ Loaded X documents"
4. Configuration options become enabled

### Step 2: Configure Settings
1. **Select Dataset**: Choose from:
   - geneva (100+ semantic event types: communication, movement, conflict, commerce, change of state, etc.)
   - wikievents (50 hierarchical event types: ArtifactExistence, Cognitive, Conflict, Contact, Disaster, Justice, Life, Movement, Transaction)
   - casie
   - genia2013
   - m2e2
   - rams
   
2. **Select Model Type**:
   - **domain-specific**: Optimized for chosen dataset
   - **cross-domain**: Works well across all datasets

### Step 3: Select Document
1. Open the "3. Select Document" dropdown
2. Choose a document from the list
3. Original text will be displayed in a card

### Step 4: Run Event Detection
1. Click "Run Event Detection" button
2. System will:
   - Run trigger identification
   - Classify triggers into event types
   - Generate results in three modes:
     - **Pipeline Mode**: Sequential identification + classification
     - **E2E Mode**: Joint identification and classification
     - **Merged Mode**: Combined results from both approaches

3. **View Results**:
   - **Annotated Source Text**: Shows triggers highlighted in the original text
   - **Three Tabs**: Pipeline, E2E, and Merged modes
   - Each tab shows:
     - Event badges (E1, E2, etc.)
     - Event type classification
     - Character offsets (span ranges)

### Step 5: Validate & Extract Arguments
1. After reviewing event detection results, click "Validate & Extract Arguments"
2. System will extract arguments for each detected trigger:
   - Argument text spans are highlighted
   - Argument roles (Speaker, Addressee, Message, etc.) are displayed
   - Roles are color-coded for easy distinction

3. **View Argument Results**:
   - Three tabs for Pipeline, E2E, and Merged modes
   - Each event card shows:
     - Trigger information
     - Associated arguments with roles
     - Character offsets for verification

### Step 6: Save Results
Two options available after argument extraction:

#### Option A: Save & Switch Dataset (Multi-dataset Annotation)
1. Click "Save & Switch Dataset" button
2. Current results are saved for the selected dataset
3. Select a **different dataset**
4. Click "Run Event Detection" again
5. Repeat the process for the new dataset
6. All results are accumulated in memory

#### Option B: Save & Finish
1. Click "Save & Finish" button
2. All accumulated results are saved to a JSON file
3. File location: `/user/debi5729/Cross-Domain-Text-Event-Extraction/annotation_results/`
4. File name: `annotated_{doc_id}_{random_id}.json`

---

## Output Format

### Single Dataset (Pipeline Mode)
```json
{
  "doc_id": "doc_001",
  "source": "Argentina rejects reports...",
  "events": {
    "geneva": {
      "pipeline": [
        {
          "trigger": {
            "text": "rejects",
            "type": "Statement",
            "offset": [9, 15]
          },
          "arguments": [
            {
              "text": "Argentina",
              "role": "Speaker",
              "offset": [0, 8]
            }
          ]
        }
      ],
      "e2e": [...],
      "merged": [...]
    }
  }
}
```

### Multi-Dataset Annotation
```json
{
  "doc_id": "doc_001",
  "source": "Argentina rejects reports...",
  "events": {
    "geneva": {
      "pipeline": [...],
      "e2e": [...],
      "merged": [...]
    },
    "m2e2": {
      "pipeline": [...],
      "e2e": [...],
      "merged": [...]
    },
    "wikievents": {
      "pipeline": [...],
      "e2e": [...],
      "merged": [...]
    }
  }
}
```

---

## Color Guide

### Trigger Highlighting
| Mode | Color | Hex Code |
|------|-------|----------|
| Pipeline | Yellow | #fff3cd |
| E2E | Blue | #cfe2ff |
| Merged | Green | #d1e7dd |

### Argument Role Colors
- Auto-assigned from palette of 6 colors
- Consistent within a document
- Helps distinguish between different argument roles

---

## Tips & Best Practices

### 1. Dataset Selection
- Use **domain-specific** models when working exclusively with one dataset
- Use **cross-domain** when mixing datasets or unsure which to choose
- Domain-specific models typically have slightly higher precision

### 2. Multi-Dataset Annotation
- Useful for understanding how different schemas capture events
- Compare event types across datasets
- Useful for schema alignment studies

### 3. Interpreting Results
- **Merged Mode**: Combines pipeline and e2e for comprehensive view
  - Use when both approaches agree (high confidence)
  - Use when one approach has better coverage
- **Pipeline vs E2E**:
  - Pipeline: More conservative (two-step process)
  - E2E: Joint modeling (captures dependencies)

### 4. Troubleshooting
- **Model not found**: Ensure model paths exist in file system
- **Empty results**: Try different text or model type
- **Memory issues**: Restart browser and app if memory accumulates
- **Slow inference**: First run loads model, subsequent runs use cache

---

## Advanced Features

### 1. Batch Processing
While the interface is designed for single documents:
- Upload multiple documents
- Process them one by one
- Save results after each document
- Results accumulate in `annotation_results/` directory

### 2. Model Paths
Edit in `web_dash_app.py` `get_model_path()` function:
```python
def get_model_path(model_type: str, dataset: str):
    tokenizer_dir = "google-t5/t5-base"
    
    if model_type == "cross-domain":
        model_dir = "path/to/cross-domain/model"
    else:
        model_dir = f"path/to/domain-specific/{dataset}/model"
    
    return tokenizer_dir, model_dir
```

### 3. Output Directory
Change in `save_and_finish()` callback:
```python
output_dir = Path("/custom/output/path")
```

---

## API Integration

### Using web_infer.py Functions Directly
```python
from web_infer import (
    run_single_inference_event_detection,
    parse_and_merge_single_inference_event_detection_results,
    run_single_inference_event_argument_extraction,
    structure_argument_extraction_pipeline_predictions,
)

# Your custom inference code
```

---

## Keyboard Shortcuts
Currently none, but can be added. Navigation via mouse clicks on buttons.

---

## Browser Compatibility
- Chrome/Chromium: ✅ Recommended
- Firefox: ✅ Supported
- Safari: ✅ Supported
- Edge: ✅ Supported

---

## Performance Metrics

| Operation | Time |
|-----------|------|
| Model Loading (first time) | 30-60s |
| Event Detection | 2-5s |
| Argument Extraction | 2-5s |
| JSON Save | <1s |

---

## Support & Feedback

For issues or questions:
1. Check the main README.md
2. Review error messages in browser console
3. Check server logs in terminal
4. Contact: [Your contact info]

---

## Example Workflow

Here's a complete example:

```
1. Upload sample_documents.json
2. Select dataset: "geneva"
3. Select model: "cross-domain"
4. Choose document: "doc_001"
5. Run Event Detection
   - See 2 triggers in Pipeline mode
   - See 3 triggers in E2E mode
   - See 3 triggers in Merged mode
6. Validate & Extract Arguments
   - See 8 arguments in Pipeline mode
   - See 10 arguments in E2E mode
7. Save & Switch Dataset
   - Select dataset: "m2e2"
   - Run Event Detection again (different schema)
   - Validate & Extract Arguments
8. Save & Finish
   - Results saved with events for both "geneva" and "m2e2"
```

---

## Next Steps

1. **Start the app**: `python web_dash_app.py`
2. **Upload test data**: Use `sample_documents.json`
3. **Explore results**: See event detection highlighting
4. **Experiment**: Try different datasets and models
5. **Integrate**: Use saved results in your pipeline


