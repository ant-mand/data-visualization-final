# Multimodal Data Provenance Dashboard

Data provenance describes the "story" of a dataset: where its contents came from, how they were collected or generated, how they were transformed, and under what terms they can be used. Provenance includes not just web domains or platforms (like Wikipedia or YouTube), but also licensing, geographic and linguistic coverage, human annotation, and relationships between derived datasets and their sources. Provenance makes it possible to trace training data back to its origins, assess legal and ethical risks, and understand over- or under-represented data in AI systems. Weak or missing provenance may obscure restrictions, amplify existing skews in who is represented, and make it harder to build accountable and inclusive models.

In order to address this problem, the Data Provenance Initiative audited over **1800 datasets**, tracing their sources, licenses, creators, and uses, and released an open dataset and interactive Explorer tool so practitioners can filter, inspect, and document training data with much stronger accountability.

[Visit the Data Provenance Initiative](https://www.dataprovenance.org/)

## This Project

This project extends their work by comparing provenance across modalities. We look at where documentation is strongest and which policy-relevant fields are missing or underspecified in the dataset records.

# Setup

```
pip3 install -r requirements.txt
```

# Run

```
python3 build_dataset.py
python3 analysis/analysis_licenses.py
python3 analysis/analysis_policy_gaps.py
python3 analysis/analysis_visibility.py
python3 app.py
```
