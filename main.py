from typing import Literal
from fasthtml.common import *
import os
import json
import pandas as pd
import fcntl
from contextlib import contextmanager

from pydantic import BaseModel, Field

# File handling constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
ALLOWED_EXTENSIONS = ('.txt', '.md')

@contextmanager
def file_lock(filepath):
    """Thread-safe file locking context manager"""
    with open(filepath, 'a+') as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX)
            yield f
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

def safe_read_file(filepath: str, max_size: int = MAX_FILE_SIZE) -> str:
    """Safely read a file with size limits and error handling"""
    try:
        path = Path(filepath)
        if path.suffix not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid file type: {path.suffix}")
        
        if path.stat().st_size > max_size:
            raise ValueError(f"File too large: {path.stat().st_size} bytes")
            
        with path.open('r', encoding='utf-8') as f:
            return f.read()
    except (IOError, OSError) as e:
        trace(f"Error reading file {filepath}: {str(e)}")
        return f"Error reading file: {str(e)}"
    
def validate_idx(idx: int, max_idx: int) -> int:
    """Validate and bound check the index parameter"""
    try:
        idx = int(idx)
        if idx < 0 or idx >= max_idx:
            raise ValueError(f"Index {idx} out of bounds (0-{max_idx-1})")
        return idx
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class LabelGroup(BaseModel):
    """Pydantic model for a single label group"""
    type: Literal["single", "multiple"] = Field(default="single")
    options: List[str]
    
class Labels(BaseModel):
    """Pydantic model for the labels file"""
    labels: dict[str, LabelGroup]
    
def safe_load_labels(filepath: str) -> Dict:
    """Safely load and validate labels file"""
    try:
        if not os.path.exists(filepath):
            print(f"File {filepath} does not exist")
            return {}
            
        with open(filepath, 'r') as f:
            labels = json.load(f)
            labels = Labels(labels=labels)
                
        return labels.labels
    except json.JSONDecodeError:
        trace(f"Invalid JSON in {filepath}")
        return {}
    except Exception as e:
        trace(f"Error loading labels: {str(e)}")
        return {}
    
def safe_save_results(results: pd.DataFrame, filepath: str) -> bool:
    """Thread-safe results saving"""
    try:
        with file_lock(filepath):
            results.to_csv(filepath, index=False)
        return True
    except Exception as e:
        trace(f"Error saving results: {str(e)}")
        return False

from lucide_fasthtml import Lucide

app, rt = fast_app(
    pico=False,
    htmlkw={"class": "uk-theme-zinc"},
    exts="preload",
    hdrs=(Link(rel='stylesheet', href='https://unpkg.com/franken-ui@1.1.0/dist/css/core.min.css'),
          Link(rel="stylesheet", href="/main.css"),
          Script(src="https://cdn.tailwindcss.com")
        )
    )

if os.path.exists("data/results.csv"):
    results = pd.read_csv("data/results.csv")
else:
    results = pd.DataFrame(columns=["file", "label", "value"])
    
files = os.listdir("data/files") if os.path.exists("data/files") else []

def preprocess_labels(labels: dict):
    """
    Preprocesses a dictionary of labels by indexing each label with an overall index.
    Args:
        labels (dict): A dictionary where keys are label categories and values are lists of labels.
    Returns:
        dict: A dictionary where each label is replaced with a dictionary containing the original label 
              and an overall index. The overall index is a unique integer assigned to each label across 
              all categories.
    """
    indexed_data = {}
    overall_index = 0
    for key,_ in labels.items():
        indexed_data[key] = []
        for o in labels[key].options:
            indexed_data[key].append({
                "value": o,
                "overall_index": overall_index
            })
            overall_index += 1
            
    return indexed_data

if os.path.exists("data/labels.json"):
    raw_labels = safe_load_labels("data/labels.json")
    preprocessed_labels = preprocess_labels(raw_labels)
    
else: 
    preprocessed_labels = {}
    
    
def get_stats(idx: int, files: list, results: pd.DataFrame):
    return (
        Div(cls="flex justify-between text-muted-foreground text-sm", id="stats")(
            Span(f"File {idx + 1} of {len(files)}"),
            Span(f"{len(results['file'].unique())}/{len(files)} annotated") if results is not None else Span(f"0/{len(files)} annotated") 
        ),
    )
    
@rt("/")
def get():
    """Currently just redirect to the first file to label from the root path. In the future a proper landing page, with an overview of all files, could be implemented"""
    return RedirectResponse("/label/0")

@rt("/label/{idx}")
def get(idx: int):
    if os.path.exists("data/files") and len(files) > 0:
        with open(f"data/files/{files[idx]}", "r") as f:
            text = f.read()
    else: 
        return (
             Div(cls="min-h-screen w-screen flex flex-col justify-center items-center", hx_boost="true")(
                Div(cls="max-w-[960px]")(
                    Div(cls="uk-card uk-card-default uk-card-body mt-2")(
                        Div(cls="border rounded p-2 bg-muted text-foreground")(
                            "No files to label found. Mount a volume to /data with text files to label."
                        )
                    )
                )
            )
        )

    def label_form(label: str, values: list):
        
        def determine_checked(label: str, value: list):
            return len(results.loc[(results["file"] == files[idx]) & (results["label"] == label) & results["value"].str.contains(value)]) > 0
        
        # create a variable shortcuts consisting of a list of all numbers from 1 to 9 and a to z
        shortcuts = [str(i) for i in range(1, 10)] + [chr(i) for i in range(97, 123)]
        
        return (
            Div(
                H2(cls="font-bold text-xl")(label),
                Form(cls="mt-2 flex flex-col gap-1", hx_post=f"/label/{idx}/{label}", hx_trigger="change changed", hx_target="#stats", hx_swap="outerHTML")(
                    *[Label(
                        Input(type="radio", cls="uk-radio", name="label_value", id=f"input-{v['overall_index']}", value=v["value"], checked=determine_checked(label, v["value"])) if raw_labels[label].type == "single" else Input(type="checkbox", cls="uk-checkbox", name="label_value", id=f"input-{v['overall_index']}", value=v["value"], checked=determine_checked(label, v["value"])),
                        v["value"],
                        " ",
                        Sup(shortcuts[v["overall_index"]]),
                        Script("window.addEventListener('keydown', function(e) {if (e.key === '" + shortcuts[v["overall_index"]] + "') {me('#input-" + str(v["overall_index"]) + "').click(); console.log(e.key)}})")
                    ) for v in values],
                )
            )
        )
        
    def next_shortcut(): return Script("window.addEventListener('keydown', function(e) {if (e.key === 'ArrowRight') {window.location.href = '/label/" + str(idx + 1) + "'}})")
    def prev_shortcut(): return Script("window.addEventListener('keydown', function(e) {if (e.key === 'ArrowLeft') {window.location.href = '/label/" + str(idx - 1) + "'}})")
    
    return (
        Div(cls="min-h-screen flex flex-col justify-center items-center", hx_boost="true")(
            Div(cls="max-w-[960px] mt-2")(
                get_stats(idx, files, results),
                Div(cls="uk-card uk-card-default uk-card-body mt-2")(
                    Div(cls="grid grid-cols-2 gap-4")(
                        Div(cls="border rounded p-2 bg-muted text-foreground")(
                            text
                        ),
                        Div(cls="space-y-2")(
                            *[label_form(label, values) for label, values in preprocessed_labels.items()]
                        )
                    ),
                    Div(cls="flex justify-between items-center mt-8", hx_ext="preload")(
                        A(href=f"/label/{idx-1}", preload=True,  cls="uk-button uk-button-default gap-2")(Lucide("arrow-left"), "Previous") if idx > 0 else Button(cls="uk-button uk-button-default gap-2", disabled=True)(Lucide("arrow-left"), "Previous"),
                        A(href=f"/label/{idx+1}", preload=True, cls="uk-button uk-button-default gap-2")("Next", Lucide("arrow-right")) if idx < len(files) - 1 else Button(cls="uk-button uk-button-default gap-2", disabled=True)("Next", Lucide("arrow-right")),
                    )
                ),
                P(cls="text-muted-foreground text-sm mt-2")("Use the arrow keys to move from file to file. Use the number keys or the corresponding letter to select a label.")
            )
        ),
        
        next_shortcut() if idx < len(files) - 1 else "",
        prev_shortcut() if idx > 0 else "",
        
        
    )
    
@rt("/label/{idx}/{label}")
async def post(req, idx: int, label: str, label_value: List[str] = None):
    try:
        idx = validate_idx(idx, len(files))
        
        # Validate label exists
        if label not in preprocessed_labels:
            raise HTTPException(status_code=400, detail=f"Invalid label: {label}")
            
        # add multiple values to results as a comma separated string
        label_value = ", ".join(label_value)
        
        # Update or add new row
        global results
        new_data = {"file": files[idx], "label": label, "value": label_value}
        mask = (results["file"] == files[idx]) & (results["label"] == label)
        
        # Remove existing rows for the same label if there is no form_data send with (usually when all checkboxes are unchecked after being checked before)
        if label_value is None:
            results = results.loc[~mask]
        
        if mask.any():
            results.loc[mask, "value"] = label_value
        else:
            results = pd.concat([results, pd.DataFrame([new_data])], ignore_index=True)
        
        if not safe_save_results(results, "data/results.csv"):
            raise HTTPException(status_code=500, detail="Failed to save results")
            
        return get_stats(idx, files, results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
serve(port=8000, reload=False)