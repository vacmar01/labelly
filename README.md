# Labelly 

![image](/assets/screenshot.png)

`Labelly` is a self-hostable, file-based, local-first solution for labelling text data, e.g. for AI training purposes. 

Through it's local first approach, it's especially suitable for sensitive data like medical records or legal documents.

## How to Install `Labelly`

The easiest way to get `Labelly` running is through docker: 

Clone the GitHub repo and run `docker build -t labelly .`

## How to add your data

### Text to label

`Labelly` expects a `/data` folder in the root path with the text files to label in `data/files`. 

Alternatively, you can providefile called `input.csv` with the data to label. `Labelly` expects to have `input.csv` to have a `text` column at least. 

An `id` column is optional and will be created with the row number as the id when missing. 

An example of a proper `data` folder can be found in `_example_data`.

### Labels

Additionally you have to your define your labels in a `labels.json` file in the `data` folder. 

An example `labels.json` file can be found here: 

```json
{
    "Examination": {
        "options": [
            "Normal",
            "Abnormal",
            "Unsure"
        ]
    },
    "Intervention": {
        "type": "multiple",
        "options": [
            "None",
            "Medication",
            "Surgery",
            "Other"
        ]
    }
}
```

Each key represents a label group named after the key. The `type` specifies if it's a multi-label or single-label label group or not (defaults to single-label label group). The options specify the different options the label can have. 

The results will be written into a `data/results.csv` file. 

## How to run the docker container

`docker run -p 8000:8000 -v $(pwd)/data:/app/data labelly`

Swap out `$(pwd)/data` for a proper path to your data on your local machine. The folder wild be mounted into the correct location of the docker container. 

## Roadmap

This is a very early proof of concept. Current todos can be found in [TODOS.md](/TODOS.md).

## Feedback

Do you have feedback? 

Write me on [Twitter](https://twitter.com/rasmus1610) or write me a mail: mariusvach [at] gmail.com
