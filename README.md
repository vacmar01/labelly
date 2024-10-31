# Labelly 

![image](/assets/screenshot.png)

`Labelly` is a self-hostable, file-based, local-first solution for labelling text data, e.g. for AI training purposes. 

Through it's local first approach, it's especially suitable for sensitive data like medical records or legal documents.

## How to Install `Labelly`

The easiest way to get `Labelly` running is through docker: 

Clone the GitHub repo and run `docker build -t labelly .`

## How to add your data

`Labelly` expects a `/data` folder in the root path with the text files to label in `data/files`. An example of a proper `data` folder can be found in `_example_data`.

Additionally you have to your define your labels in a `labels.json` file in the `data` folder. 

An example `labels.json` file can be found here: 

```json
{
    "Examination": [
        "Normal",
        "Abnormal",
        "Unsure"
    ],
    "Bleeding": [
        "None",
        "Mild",
        "Moderate",
        "Severe"
    ],
    "MassEffect": [
        "None",
        "Mild",
        "Moderate",
        "Severe"
    ]
}
```

The results will be written into a `data/results.csv` file. 

## How to run the docker container

`docker run -p 8000:8000 -v $(pwd)/data:/app/data labelly`

Swap out `$(pwd)/data` for a proper path to your data on your local machine. The folder wild be mounted into the correct location of the docker container. 

## Roadmap

This is a very early proof of concept. Here are some things I want to improve in the future:

- [ ] Support csv as file inputs
- [ ] Support multiple labels of same label tag
- [ ] Proper stats

## Feedback

Do you have feedback? 

Write me on [Twitter](https://twitter.com/rasmus1610) or write me a mail: mariusvach [at] gmail.com
