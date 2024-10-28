from fasthtml.common import *
import os
import json
import pandas as pd

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
    for key, values in labels.items():
        indexed_data[key] = []
        for value in values:
            indexed_data[key].append({"value": value, "overall_index": overall_index})
            overall_index += 1
            
    return indexed_data

if os.path.exists("data/labels.json"):
    with open("data/labels.json", "r") as f:
        labels = json.load(f)
    
    labels = preprocess_labels(labels)
else: 
    labels = {}
    
    
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
             Div(cls="h-screen w-screen flex flex-col justify-center items-center", hx_boost="true")(
                Div(cls="max-w-[960px]")(
                    Div(cls="uk-card uk-card-default uk-card-body mt-2")(
                        Div(cls="border rounded p-2 bg-muted text-foreground")(
                            "No files to label found. Mount a volume to /data/files with text files to label."
                        )
                    )
                )
            )
        )

    def label_form(label: str, values: list):
        
        def determine_checked(label: str, value: list):
            return len(results.loc[(results["file"] == files[idx]) & (results["label"] == label) & (results["value"] == value)]) > 0
        
        # create a variable shortcuts consisting of a list of all numbers from 1 to 9 and a to z
        shortcuts = [str(i) for i in range(1, 10)] + [chr(i) for i in range(97, 123)]
        
        return (
            Div(
                H2(cls="font-bold text-xl")(label),
                Form(cls="mt-2 flex flex-col gap-1", hx_post=f"/label/{idx}/{label}", hx_trigger="change changed", hx_target="#stats", hx_swap="outerHTML")(
                    *[Label(
                        Input(type="radio", cls="uk-radio", name="label_value", id=f"input-{v['overall_index']}", value=v["value"], checked=determine_checked(label, v["value"])),
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
        Div(cls="h-screen w-screen flex flex-col justify-center items-center", hx_boost="true")(
            Div(cls="max-w-[960px]")(
                get_stats(idx, files, results),
                Div(cls="uk-card uk-card-default uk-card-body mt-2")(
                    Div(cls="grid grid-cols-2 gap-4")(
                        Div(cls="border rounded p-2 bg-muted text-foreground")(
                            text
                        ),
                        Div(cls="space-y-2")(
                            *[label_form(label, values) for label, values in labels.items()]
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
def post(idx: int, label: str, label_value: str):
    global results
    # Check if an entry with the same file and label already exists
    existing_entry = results.loc[(results["file"] == files[idx]) & (results["label"] == label)]
    
    if not existing_entry.empty:
        # Update the existing entry with the new label_value
        results.loc[(results["file"] == files[idx]) & (results["label"] == label), "value"] = label_value
    else:
        # Add a new entry
        new_row = pd.DataFrame([{"file": files[idx], "label": label, "value": label_value}])
        results = pd.concat([results, new_row], ignore_index=True)
    
    # Save the results to the CSV file
    results.to_csv("data/results.csv", index=False)
    
    return get_stats(idx, files, results)
    
serve(port=8000, reload=False)