# Network of stories

## Intro

- This is a proof-of-concept software developed as an analysis tool for my thesis work.
- The goal for this project is to demonstrate the capabilities of first story detection (FSD) using similarity methods.
- The datasets used in the thesis are not provided as part of this project.

## Setup

### Pre-requisites

- Docker compose
- npm
- Python >3.10
- Alibaba GTE model weights
- Cuda cabable machine

### Install

- Clone the repository
- Make sure that you have docker compose and npm installed

- Run:

```bash
$: cd frontend/
$: npm install
```

```bash
$: cd backend/
$: docker compose up --build
```
- The software should start at ```localhost:5173 ```

## Features

- The software is designed to be a testbench for different embedding methods and datasets.

### Adding data

- The datasets are loaded from ``` backend/mock_data/<dataset_name>.json ```

- The dataset has to be added into the drop down menu in ``` frontend/src/App.vue ``` in the ``` datasourceOptions ```