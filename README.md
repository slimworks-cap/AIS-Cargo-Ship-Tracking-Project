# AIS-Cargo-Ship-Tracking-Project

<!-- TABLE OF CONTENTS -->
<header>Table of Contents</header>
  <ol>
    <li><a href="#about-the-project">About The Project</a></li>
    <li><a href="#built-with">Built With</a></li>
    <li><a href="#background">Background</a></li>
    <li><a href="#project-structure">Project Structure</a></li>
    <li><a href="#demo-video">Demo Video</a></li>

  </ol>

<!-- ABOUT THE PROJECT -->

# About The Project

A real-time data engineering pipeline that ingests live vessel position data 
from the AIS (Automatic Identification System) network, processes it through 
a medallion architecture on Databricks, and serves it to an interactive 
Streamlit dashboard showing cargo vessel traffic in San Francisco Bay.

<img src=https://i.imgur.com/i3zt7XD.png>
<img src=https://imgur.com/NjXJUxA.png>
<img src=https://imgur.com/T2cBzju.png>

# Built With
* [Python][Python-url]
* [Databricks Free Edition][Databricks-url]
* [Streamlit][Streamlit-url]
* [AIS Stream][AIS_Stream-url]

# Background

Pursuant with my goal to make a project that is aligned with my background in freight forwarding and NVOCC logistics as well as to improve my skills and knowledge in Python and Databricks. I have created this AIS Tracking project to create a fullstack ETL pipeline and dashboard that tracks cargo vessels in real-time as well as to track their historical movements in the San Francisco Bay. 

This project was built with the AI-assisted development (Claude by Anthropic) and uses Databricks' proprietary streaming technology to ingest, clean, and transform the data via medallion architecture as well as load the databases on the same platform which is then uploaded onto a Streamlit Dashboard in order to view movements of the vessels.

Beyond the technical skills - this project improved not only my knowledge of different Python modules and databricks but also improved my knowledge of maritime management information concepts such as AIS systems, Berthing cycles, Maritime Identifiers, like the MMSI.

<!-- Project Structure -->
# Project Structure
├── <a href="https://github.com/slimworks-cap/AIS-Cargo-Ship-Tracking-Project/blob/main/.gitignore">.gitignore</a>  
├── <a href="https://github.com/slimworks-cap/AIS-Cargo-Ship-Tracking-Project/blob/main/README.md">README.md</a>  
├── <a href="https://github.com/slimworks-cap/AIS-Cargo-Ship-Tracking-Project/blob/main/ais_app.py">ais_app.py</a>  
├── <a href="https://github.com/slimworks-cap/AIS-Cargo-Ship-Tracking-Project/blob/main/ais_data_collector.py">ais_data_collector.py</a>   
└── <a href="https://github.com/slimworks-cap/AIS-Cargo-Ship-Tracking-Project/blob/main/ais_data_uploader.py">ais_data_uploader.py</a>

<!-- Demo video -->
# Demo Video

<!-- MARKDOWN LINKS & IMAGES -->

[Python-url]:       https://www.python.org/
[Databricks-url]:   https://www.databricks.com/
[Streamlit-url]:    https://streamlit.io/
[AIS_Stream-url]:   https://aisstream.io/
